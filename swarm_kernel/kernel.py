from __future__ import annotations
import hashlib,json,random,re,uuid
from dataclasses import dataclass
from datetime import datetime,timedelta,timezone
from pathlib import Path
from typing import Any,Mapping,Sequence
KERNEL_VERSION="1.0.0"; SAFE_ID=re.compile(r"^[A-Za-z0-9._:-]{1,160}$"); RUN_STATES={"PREPARING","READY","ACTIVE","DEGRADED_READ_ONLY","CONVERGING","COMPLETE","ABORTED"}; ROLES={"PRIMARY","MANAGER","RESEARCH"}; QUARANTINE_REASONS={"PROJECT_MISMATCH","STALE_RUN","MALFORMED","UNSUPPORTED_PROTOCOL","ILLEGAL_CROSS_PROJECT_COMMAND","LEASE_CONFLICT","INVARIANT_FAILURE"}
def utc_now(): return datetime.now(timezone.utc)
def iso(dt=None): return (dt or utc_now()).replace(microsecond=0).isoformat().replace("+00:00","Z")
def require_safe_id(v,n):
    if not SAFE_ID.fullmatch(v): raise ValueError(f"unsafe {n}: {v!r}")
    return v
@dataclass(frozen=True)
class ProjectConfig:
    project_id:str; repository:str; canonical_branch:str; coordination_root:str; state_root:str=".swarm"; lease_ttl_seconds:int=1800; heartbeat_interval_seconds:int=300; circuit_breaker_threshold:int=3; manager_queue_soft_limit:int=8; manager_queue_hard_limit:int=15
    @classmethod
    def load(cls,path):
        d=json.loads(Path(path).read_text(encoding="utf-8"));
        if d.get("kernel_version")!=KERNEL_VERSION: raise ValueError("unsupported swarm-kernel version")
        c=cls(d["project_id"],d["repository"],d.get("canonical_branch","main"),d["coordination_root"],d.get("state_root",".swarm"),int(d.get("lease_ttl_seconds",1800)),int(d.get("heartbeat_interval_seconds",300)),int(d.get("circuit_breaker_threshold",3)),int(d.get("manager_queue_soft_limit",8)),int(d.get("manager_queue_hard_limit",15))); require_safe_id(c.project_id,"project_id")
        if "/" not in c.repository or c.state_root!=".swarm": raise ValueError("invalid project binding")
        return c
def validate_binding(c,p,r):
    if p!=c.project_id or r!=c.repository: raise PermissionError("project/repository binding mismatch; fail closed")
def new_global_run_id(prefix="run"): require_safe_id(prefix,"run prefix"); return f"{prefix}_{utc_now().strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:12]}"
def operation_id(p,r,o,s):
    for v,n in ((p,"project_id"),(r,"global_run_id"),(o,"operation"),(s,"subject")): require_safe_id(v,n)
    return hashlib.sha256("|".join((p,r,o,s)).encode()).hexdigest()
def record_path(k,r,i):
    if k not in {"epochs","ready","leases","idempotency","quarantine","health","checkpoints","convergence"}: raise ValueError("unsupported state kind")
    require_safe_id(r,"global_run_id"); require_safe_id(i,"record_id"); return f".swarm/{k}/{r}/{i}.json"
def ready_record(c,r,a,role,package_version,source_revision):
    require_safe_id(r,"global_run_id"); require_safe_id(a,"agent_id")
    if role not in ROLES: raise ValueError("invalid role")
    return {"schema":"swarm-kernel/ready/v1","kernel_version":KERNEL_VERSION,"project_id":c.project_id,"repository":c.repository,"global_run_id":r,"agent_id":a,"role":role,"package_version":package_version,"source_revision":source_revision,"status":"READY","timestamp_utc":iso()}
def can_open_start_gate(expected,ready,explicit_close=False):
    m=sorted(set(expected)-set(ready)); return (not m or explicit_close),m
def new_lease(c,r,t,a,expected_version,now=None):
    now=now or utc_now()
    for v,n in ((r,"global_run_id"),(t,"task_id"),(a,"agent_id")): require_safe_id(v,n)
    if expected_version<0: raise ValueError("expected_version must be non-negative")
    return {"schema":"swarm-kernel/lease/v1","project_id":c.project_id,"repository":c.repository,"global_run_id":r,"task_id":t,"owner_agent_id":a,"version":expected_version+1,"heartbeat_at":iso(now),"expires_at":iso(now+timedelta(seconds=c.lease_ttl_seconds)),"status":"HELD"}
def lease_transition_allowed(cur,expected_version,a,now=None):
    now=now or utc_now()
    if cur is None: return (expected_version==0,"NEW" if expected_version==0 else "VERSION_MISMATCH")
    if int(cur.get("version",-1))!=expected_version: return False,"VERSION_MISMATCH"
    ex=datetime.fromisoformat(str(cur["expires_at"]).replace("Z","+00:00"))
    if cur.get("owner_agent_id")==a: return True,"RENEW"
    if ex<=now: return True,"EXPIRED_RECLAIM"
    return False,"LEASE_HELD"
def deterministic_backoff(k,attempt,cap_seconds=8.0):
    if attempt<0: raise ValueError("attempt must be non-negative")
    seed=int(hashlib.sha256(f"{k}|{attempt}".encode()).hexdigest()[:16],16); ceiling=min(cap_seconds,.25*(2**min(attempt,8))); return random.Random(seed).uniform(.05,max(.05,ceiling))
def idempotency_record(c,r,o,result_ref): require_safe_id(r,"global_run_id");require_safe_id(o,"operation_id");return {"schema":"swarm-kernel/idempotency/v1","project_id":c.project_id,"global_run_id":r,"operation_id":o,"result_ref":result_ref,"committed_at":iso()}
def quarantine_record(c,r,i,reason,details):
    if reason not in QUARANTINE_REASONS: raise ValueError("unsupported quarantine reason")
    return {"schema":"swarm-kernel/quarantine/v1","project_id":c.project_id,"global_run_id":r,"item_id":require_safe_id(i,"item_id"),"reason":reason,"details":details,"timestamp_utc":iso(),"action":"NO_EXECUTION"}
def circuit_state(c,n): return "DEGRADED_READ_ONLY" if n>=c.circuit_breaker_threshold else "ACTIVE"
def backpressure_state(c,n): return "HARD_STOP_SECONDARY_WORK" if n>=c.manager_queue_hard_limit else ("SLOW_SECONDARY_WORK" if n>=c.manager_queue_soft_limit else "NORMAL")
def preflight(c,checks):
    req=("identity_binding","run_epoch","role_binding","package_parity","recovery_state","manager_presence","foreign_write_policy","tests"); missing=[x for x in req if x not in checks]; failed=[x for x in req if checks.get(x) is not True]; return {"schema":"swarm-kernel/preflight/v1","project_id":c.project_id,"kernel_version":KERNEL_VERSION,"missing":missing,"failed":failed,"ready":not missing and not failed,"timestamp_utc":iso()}
def convergence_gate(**k):
    checks={"research_accounted":k["research_accounted"],"manager_dispositions_complete":k["manager_dispositions_complete"],"primary_decisions_persisted":k["primary_decisions_persisted"],"package_parity_restored":k["package_parity_restored"],"no_unresolved_leases":k["unresolved_leases"]==0,"recovery_checkpoint_valid":k["recovery_checkpoint_valid"]}; return {"schema":"swarm-kernel/convergence/v1","checks":checks,"complete":all(checks.values())}
def health_snapshot(c,r,**k):
    if k["state"] not in RUN_STATES: raise ValueError("invalid run state")
    return {"schema":"swarm-kernel/health/v1","kernel_version":KERNEL_VERSION,"project_id":c.project_id,"repository":c.repository,"global_run_id":r,"state":k["state"],"active_agents":k["active_agents"],"manager_queue_depth":k["manager_queue_depth"],"backpressure":backpressure_state(c,k["manager_queue_depth"]),"collisions":k["collisions"],"failed_checks":k["failed_checks"],"last_accepted_integration":k.get("last_accepted_integration"),"package_version":k["package_version"],"cross_project_authority":"NONE","telemetry_visibility":"READ_ONLY","timestamp_utc":iso()}
