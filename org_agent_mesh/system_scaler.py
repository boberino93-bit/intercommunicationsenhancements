from __future__ import annotations
import hashlib, json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping, Sequence
CAPACITY_STATES={"GREEN","AMBER","PRESERVE","RESERVE_ONLY","EXHAUSTED","UNKNOWN"}; RUN_STATES={"ACTIVE","READY","CONVERGING","DEGRADED_READ_ONLY","COMPLETE"}; ACTIONS={"HOLD","REQUEST_ADMIT","REQUEST_DRAIN_TO_STANDBY"}
DEFAULT_PROJECTS=("ai-behaviour-control-lab","benefitflow","duo-open","fold7-power-lab","intercommunicationsenhancements","warp-propulsion-lab","xrp-thesis")
class SystemScalerError(ValueError): pass
def _parse_utc(v):
    if not isinstance(v,str) or not v: raise SystemScalerError("UTC timestamp must be a non-empty string")
    p=datetime.fromisoformat(v.replace("Z","+00:00"));
    if p.tzinfo is None: raise SystemScalerError("UTC timestamp must include timezone")
    return p.astimezone(timezone.utc)
@dataclass(frozen=True)
class ScalerConfig:
    project_count:int=7; expected_project_ids:tuple[str,...]=DEFAULT_PROJECTS; specialist_cap_per_project:int=8; healthy_windows_required:int=3; cooldown_windows:int=2; manager_queue_soft_limit:int=8; manager_queue_hard_limit:int=15; max_global_admissions_per_cycle:int=7; max_project_admissions_per_cycle:int=1; max_global_drains_per_cycle:int=7; max_signal_age_seconds:int=120; max_future_skew_seconds:int=5
    def __post_init__(self):
        for n in ("project_count","specialist_cap_per_project","healthy_windows_required","cooldown_windows","manager_queue_soft_limit","manager_queue_hard_limit","max_global_admissions_per_cycle","max_project_admissions_per_cycle","max_global_drains_per_cycle","max_signal_age_seconds","max_future_skew_seconds"):
            v=getattr(self,n)
            if not isinstance(v,int) or isinstance(v,bool) or v<=0: raise SystemScalerError(f"{n} must be a positive integer")
        if self.manager_queue_soft_limit>=self.manager_queue_hard_limit: raise SystemScalerError("manager soft limit must be below hard limit")
        p=tuple(sorted(str(x).strip() for x in self.expected_project_ids))
        if len(p)!=self.project_count or len(set(p))!=len(p) or any(not x for x in p): raise SystemScalerError("expected_project_ids must contain exactly project_count unique ids")
        object.__setattr__(self,"expected_project_ids",p)
@dataclass(frozen=True)
class ProjectScaleSignal:
    project_id:str; run_id:str; measured_at_utc:str; active_research:int; standby_research:int; queued_eligible_work:int; manager_queue_depth:int; capacity_state:str; collisions:int=0; unresolved_leases:int=0; completion_integrity_pass:bool=True; ledger_chain_valid:bool=True; handoff_fresh:bool=True; unauthorized_mutations:int=0; cross_project_write_violations:int=0; run_state:str="ACTIVE"; idle_lease_free_agent_ids:tuple[str,...]=(); persistence_state:str="DUAL_PERSISTENCE_CONFIRMED"; persistence_zero_loss:bool=True; persistence_digest_mismatch_count:int=0; persistence_conflict_count:int=0
    def __post_init__(self):
        if not self.project_id or not self.run_id: raise SystemScalerError("project_id and run_id are required")
        _parse_utc(self.measured_at_utc)
        for n in ("active_research","standby_research","queued_eligible_work","manager_queue_depth","collisions","unresolved_leases","unauthorized_mutations","cross_project_write_violations","persistence_digest_mismatch_count","persistence_conflict_count"):
            v=getattr(self,n)
            if not isinstance(v,int) or isinstance(v,bool) or v<0: raise SystemScalerError(f"{n} must be a non-negative integer")
        if self.capacity_state not in CAPACITY_STATES: raise SystemScalerError("invalid capacity_state")
        if self.run_state not in RUN_STATES: raise SystemScalerError("invalid run_state")
        if len(set(self.idle_lease_free_agent_ids))!=len(self.idle_lease_free_agent_ids): raise SystemScalerError("duplicate drain candidates")
@dataclass(frozen=True)
class ScalerMemory: healthy_windows:Mapping[str,int]=field(default_factory=dict); cooldown_remaining:Mapping[str,int]=field(default_factory=dict); fairness_cursor:int=0
@dataclass(frozen=True)
class ScaleDecision:
    action:str; project_id:str|None; agent_id:str|None; reason:str; authority_conveyed:bool=False; direct_termination_allowed:bool=False
    def __post_init__(self):
        if self.action not in ACTIONS: raise SystemScalerError("invalid action")
        if self.authority_conveyed or self.direct_termination_allowed: raise SystemScalerError("scaler may not convey authority or terminate agents")
    def as_dict(self): return {"action":self.action,"project_id":self.project_id,"agent_id":self.agent_id,"reason":self.reason,"authority_conveyed":False,"direct_termination_allowed":False}
def stage_research_ceiling(stage_population,cfg):
    if stage_population not in {15,30,60,100}: raise SystemScalerError("unsupported stage population")
    return max(0,min(cfg.project_count*cfg.specialist_cap_per_project,stage_population-cfg.project_count*2))
def _hard_freeze(s):
    if s.capacity_state=="UNKNOWN": return "UNKNOWN_CAPACITY"
    if s.capacity_state=="EXHAUSTED": return "EXHAUSTED_CAPACITY_CHECKPOINT_UNSAFE"
    if s.run_state=="DEGRADED_READ_ONLY": return "DEGRADED_READ_ONLY"
    if s.unauthorized_mutations: return "UNAUTHORIZED_MUTATION_EVIDENCE"
    if s.cross_project_write_violations: return "CROSS_PROJECT_WRITE_VIOLATION"
    if not s.handoff_fresh: return "STALE_HANDOFF"
    if not s.ledger_chain_valid: return "LEDGER_CHAIN_INVALID"
    if not s.completion_integrity_pass: return "COMPLETION_INTEGRITY_FAILURE"
    if s.unresolved_leases: return "UNRESOLVED_LEASE"
    if s.persistence_state!="DUAL_PERSISTENCE_CONFIRMED": return "DUAL_PERSISTENCE_UNCONFIRMED"
    if not s.persistence_zero_loss: return "PERSISTENCE_DEGRADED"
    if s.persistence_digest_mismatch_count: return "PERSISTENCE_DIGEST_MISMATCH"
    if s.persistence_conflict_count: return "PERSISTENCE_CONFLICT"
    return None
def _telemetry_freeze(s,*,run_id,now,cfg):
    if s.run_id!=run_id: return "RUN_ID_MISMATCH"
    age=(now-_parse_utc(s.measured_at_utc)).total_seconds()
    if age>cfg.max_signal_age_seconds:return "STALE_TELEMETRY"
    if age<-cfg.max_future_skew_seconds:return "FUTURE_TELEMETRY"
def _healthy(s,cfg): return _hard_freeze(s) is None and s.capacity_state=="GREEN" and s.manager_queue_depth<cfg.manager_queue_soft_limit and s.collisions==0 and s.run_state in {"ACTIVE","READY"}
def update_memory(signals,memory,cfg):
    h={}; c={}
    for s in signals: h[s.project_id]=int(memory.healthy_windows.get(s.project_id,0))+1 if _healthy(s,cfg) else 0; c[s.project_id]=max(0,int(memory.cooldown_remaining.get(s.project_id,0))-1)
    return ScalerMemory(h,c,memory.fairness_cursor)
def _signal_dict(s):
    return {"project_id":s.project_id,"run_id":s.run_id,"measured_at_utc":s.measured_at_utc,"active_research":s.active_research,"standby_research":s.standby_research,"queued_eligible_work":s.queued_eligible_work,"manager_queue_depth":s.manager_queue_depth,"capacity_state":s.capacity_state,"collisions":s.collisions,"unresolved_leases":s.unresolved_leases,"completion_integrity_pass":s.completion_integrity_pass,"ledger_chain_valid":s.ledger_chain_valid,"handoff_fresh":s.handoff_fresh,"unauthorized_mutations":s.unauthorized_mutations,"cross_project_write_violations":s.cross_project_write_violations,"run_state":s.run_state,"idle_lease_free_agent_ids":list(s.idle_lease_free_agent_ids),"persistence_state":s.persistence_state,"persistence_zero_loss":s.persistence_zero_loss,"persistence_digest_mismatch_count":s.persistence_digest_mismatch_count,"persistence_conflict_count":s.persistence_conflict_count}
def _input_digest(*,stage_population,run_id,now_utc,signals,cfg):
    p={"stage_population":stage_population,"run_id":run_id,"now_utc":now_utc,"signals":[_signal_dict(s) for s in sorted(signals,key=lambda x:x.project_id)],"expected_project_ids":list(cfg.expected_project_ids),"specialist_cap_per_project":cfg.specialist_cap_per_project}; return "sha256:"+hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def decide(*,stage_population,run_id,now_utc,signals,memory=None,cfg=None):
    cfg=cfg or ScalerConfig(); original=memory or ScalerMemory(); now=_parse_utc(now_utc)
    if not run_id: raise SystemScalerError("run_id is required")
    if len({s.project_id for s in signals})!=len(signals): raise SystemScalerError("duplicate project signals")
    if set(s.project_id for s in signals)!=set(cfg.expected_project_ids): raise SystemScalerError("exact registered project signal set is required")
    ordered=sorted(signals,key=lambda s:s.project_id); digest=_input_digest(stage_population=stage_population,run_id=run_id,now_utc=now_utc,signals=ordered,cfg=cfg)
    freezes=[(s,_telemetry_freeze(s,run_id=run_id,now=now,cfg=cfg)) for s in ordered]
    if any(r for _,r in freezes): return _result(stage_population,run_id,digest,ordered,original,[ScaleDecision("HOLD",None,None,"GLOBAL_FREEZE:"+",".join(f"{s.project_id}:{r}" for s,r in freezes if r))],cfg)
    freezes=[(s,_hard_freeze(s)) for s in ordered]
    if any(r for _,r in freezes): return _result(stage_population,run_id,digest,ordered,original,[ScaleDecision("HOLD",None,None,"GLOBAL_FREEZE:"+",".join(f"{s.project_id}:{r}" for s,r in freezes if r))],cfg)
    memory=update_memory(ordered,original,cfg); total=sum(s.active_research for s in ordered); ceiling=stage_research_ceiling(stage_population,cfg); excess=max(0,total-ceiling)
    if excess:
        cand=[(s.project_id,a) for s in ordered for a in sorted(s.idle_lease_free_agent_ids)]; n=min(excess,cfg.max_global_drains_per_cycle,len(cand))
        if not n:return _result(stage_population,run_id,digest,ordered,memory,[ScaleDecision("HOLD",None,None,f"STAGE_CONTRACTION_BLOCKED:EXCESS={excess}")],cfg)
        return _result(stage_population,run_id,digest,ordered,memory,[ScaleDecision("REQUEST_DRAIN_TO_STANDBY",p,a,"STAGE_CONTRACTION_GRACEFUL_DRAIN") for p,a in cand[:n]],cfg,remaining_excess=max(0,excess-n))
    pressure=[s for s in ordered if s.manager_queue_depth>=cfg.manager_queue_hard_limit or s.capacity_state=="RESERVE_ONLY"]
    if pressure:
        drains=[ScaleDecision("REQUEST_DRAIN_TO_STANDBY",s.project_id,sorted(s.idle_lease_free_agent_ids)[0],"HARD_PRESSURE_GRACEFUL_DRAIN") for s in pressure if s.idle_lease_free_agent_ids][:cfg.max_global_drains_per_cycle]
        return _result(stage_population,run_id,digest,ordered,memory,drains or [ScaleDecision("HOLD",None,None,"HARD_PRESSURE_NO_SAFE_DRAIN")],cfg)
    available=max(0,ceiling-total)
    if not available:return _result(stage_population,run_id,digest,ordered,memory,[ScaleDecision("HOLD",None,None,"STAGE_RESEARCH_CEILING_REACHED")],cfg)
    if any(s.manager_queue_depth>=cfg.manager_queue_soft_limit or s.capacity_state in {"AMBER","PRESERVE"} or s.collisions for s in ordered):return _result(stage_population,run_id,digest,ordered,memory,[ScaleDecision("HOLD",None,None,"SOFT_PRESSURE_OR_COLLISION")],cfg)
    eligible=[s for s in ordered if s.queued_eligible_work>0 and s.standby_research>0 and s.active_research<cfg.specialist_cap_per_project and memory.healthy_windows.get(s.project_id,0)>=cfg.healthy_windows_required and memory.cooldown_remaining.get(s.project_id,0)==0]
    if not eligible:return _result(stage_population,run_id,digest,ordered,memory,[ScaleDecision("HOLD",None,None,"NO_ADMISSION_DEMAND" if not any(s.queued_eligible_work>0 for s in ordered) else "HYSTERESIS_OR_CAPACITY_NOT_READY")],cfg)
    cursor=memory.fairness_cursor%len(eligible); rotated=eligible[cursor:]+eligible[:cursor]; chosen=rotated[:min(available,cfg.max_global_admissions_per_cycle,len(rotated))]; cd=dict(memory.cooldown_remaining); decisions=[]
    for s in chosen: decisions.append(ScaleDecision("REQUEST_ADMIT",s.project_id,None,"SUSTAINED_HEALTHY_DEMAND")); cd[s.project_id]=cfg.cooldown_windows
    memory=ScalerMemory(dict(memory.healthy_windows),cd,(memory.fairness_cursor+len(chosen))%max(1,len(eligible))); return _result(stage_population,run_id,digest,ordered,memory,decisions,cfg)
def _result(stage_population,run_id,input_digest,signals,memory,decisions,cfg,*,remaining_excess=0):
    p={"schema":"org-agent-mesh/system-scaler-decision/v2","run_id":run_id,"stage_population":stage_population,"research_ceiling":stage_research_ceiling(stage_population,cfg),"active_research":sum(s.active_research for s in signals),"remaining_excess_after_requested_drains":remaining_excess,"input_digest":input_digest,"decisions":[d.as_dict() for d in decisions],"memory":{"healthy_windows":dict(sorted(memory.healthy_windows.items())),"cooldown_remaining":dict(sorted(memory.cooldown_remaining.items())),"fairness_cursor":memory.fairness_cursor},"authority_conveyed":False,"direct_termination_allowed":False}; p["decision_digest"]="sha256:"+hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":")).encode()).hexdigest(); return p
