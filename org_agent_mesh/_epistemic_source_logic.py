from __future__ import annotations

from dataclasses import replace
from typing import Iterable, Mapping, Sequence

from ._epistemic_base import *
from ._epistemic_base import _digest, _norm, _parse_ts
from ._epistemic_model import *

def _source_base_origin_key(src: SourceIdentity) -> str:
    if src.content_hash:
        return "hash:" + src.content_hash.lower()
    return "meta:" + _digest([
        _norm(src.canonical_origin), _norm(src.publisher), _norm(src.title),
        src.publication_date or "", _norm(src.version), _norm(src.canonical_identifier),
    ])


def collapse_source_identities(sources: Iterable[SourceIdentity]):
    """Collapse mirrors/derivatives to independent origins, including transitive lineage."""
    rows=tuple(sources)
    by_id={src.source_identity_id:src for src in rows}
    if len(by_id) != len(rows):
        raise EpistemicError("duplicate source_identity_id")
    memo: dict[str, tuple[str,...]]={}

    def roots(source_id: str, trail: tuple[str,...]=()) -> tuple[str,...]:
        if source_id in memo:
            return memo[source_id]
        if source_id in trail:
            raise EpistemicError("source lineage cycle detected")
        src=by_id[source_id]
        if not src.derived_from:
            result=(_source_base_origin_key(src),)
        else:
            found=[]
            for parent in src.derived_from:
                if parent in by_id:
                    found.extend(roots(parent, trail + (source_id,)))
                else:
                    found.append("external:" + _norm(parent))
            result=tuple(sorted(set(found)))
        memo[source_id]=result
        return result

    groups: dict[str,list[SourceIdentity]]={}
    for src in rows:
        root_keys=roots(src.source_identity_id)
        key=root_keys[0] if len(root_keys)==1 else "lineage:"+_digest(root_keys)
        groups.setdefault(key,[]).append(src)

    canonical=[]; alias={}
    for key in sorted(groups):
        group=groups[key]
        chosen=sorted(group,key=lambda item:(bool(item.derived_from), item.source_identity_id))[0]
        canonical.append(chosen)
        for src in group:
            alias[src.source_identity_id]=chosen.source_identity_id
    return tuple(canonical), alias


def validate_model_provenance(model: SharedEpistemicModel) -> bool:
    source_ids=[src.source_identity_id for src in model.sources]
    instance_ids=[item.source_instance_id for item in model.source_instances]
    evidence_ids=[item.evidence_id for item in model.evidence]
    claim_ids=[item.claim_id for item in model.claims]
    for label, values in (("source",source_ids),("source instance",instance_ids),("evidence",evidence_ids),("claim",claim_ids)):
        if len(values) != len(set(values)):
            raise EpistemicError(f"duplicate {label} identifier")
    sources=set(source_ids); claims=set(claim_ids); evidence=set(evidence_ids)
    instances={item.source_instance_id:item for item in model.source_instances}
    for item in model.source_instances:
        if item.source_identity_id not in sources:
            raise EpistemicError("source instance references unknown source identity")
    for item in model.evidence:
        if item.source_identity_id not in sources:
            raise EpistemicError("evidence references unknown source identity")
        instance=instances.get(item.source_instance_id)
        if instance is None:
            raise EpistemicError("evidence references unknown source instance")
        if instance.source_identity_id != item.source_identity_id:
            raise EpistemicError("evidence source identity does not match source instance")
        if any(ref not in claims for ref in item.supports + item.opposes):
            raise EpistemicError("evidence references unknown claim")
    for claim in model.claims:
        if any(ref not in evidence for ref in claim.evidence_for + claim.evidence_against):
            raise EpistemicError("claim references unknown evidence")
    for hypothesis in model.hypotheses:
        if any(ref not in claims for ref in hypothesis.supporting_claims + hypothesis.opposing_claims):
            raise EpistemicError("hypothesis references unknown claim")
    return True


def _canonicalize_provenance(model: SharedEpistemicModel, collapsed: tuple[SourceIdentity,...], alias: Mapping[str,str]):
    instances=tuple(replace(item,source_identity_id=alias[item.source_identity_id]) for item in model.source_instances)
    instance_map={item.source_instance_id:item for item in instances}
    evidence=[]
    for item in model.evidence:
        canonical_id=alias[item.source_identity_id]
        instance=instance_map[item.source_instance_id]
        if instance.source_identity_id != canonical_id:
            raise EpistemicError("canonical source identity does not match source instance")
        evidence.append(replace(item,source_identity_id=canonical_id))
    return instances,tuple(evidence)


def _support_origins(claim: ClaimRecord, evidence: Mapping[str,EvidenceItem], alias: Mapping[str,str]):
    ids=[]
    for eid in claim.evidence_for:
        item=evidence.get(eid)
        if item:
            ids.append(alias.get(item.source_identity_id,item.source_identity_id))
    return set(ids)


def calibrated_confidence(claim: ClaimRecord, evidence_by_id: Mapping[str,EvidenceItem], alias: Mapping[str,str]) -> tuple[int,str,int,int,EvidenceTier]:
    supporting=[evidence_by_id[eid] for eid in claim.evidence_for if eid in evidence_by_id]
    opposing=[evidence_by_id[eid] for eid in claim.evidence_against if eid in evidence_by_id]
    origins=_support_origins(claim,evidence_by_id,alias)
    if not supporting:
        base=20; best=EvidenceTier.INFERENCE
    else:
        effective_tiers=[]
        for item in supporting:
            if item.negative and item.negative.result == "NOT_FOUND":
                effective_tiers.append(max(item.tier, EvidenceTier.SECONDARY))
            else:
                effective_tiers.append(item.tier)
        best=min(effective_tiers,key=int)
        base={1:92,2:86,3:82,4:70,5:55,6:42}[int(best)]
    if len(origins)>1:
        base += min(8,4*(len(origins)-1))
    same_origin_support=max(0,len(supporting)-len(origins)); base -= 3*same_origin_support
    if opposing:
        base -= min(30,8*len(opposing))
    app=claim.applicability
    if supporting and any(e.applicability.software_version is None for e in supporting) and app.software_version:
        base -= 5
    if supporting and any(e.applicability.environment is None for e in supporting) and app.environment:
        base -= 4
    stale=sum(1 for e in supporting if e.applicability.temporal_status in {TemporalStatus.HISTORICAL,TemporalStatus.SUPERSEDED})
    base -= min(15,5*stale)
    not_found=sum(1 for e in supporting if e.negative and e.negative.result == "NOT_FOUND")
    absent=sum(1 for e in supporting if e.negative and e.negative.result == "ABSENT")
    base -= min(24,12*not_found)
    if supporting and all(e.negative and e.negative.result == "NOT_FOUND" for e in supporting):
        base=min(base,60)
    base=max(0,min(100,base))
    independent=len(origins)
    source_count=len(origins)
    basis=(f"best_tier={int(best)}; independent_origins={independent}; opposing={len(opposing)}; "
           f"duplicate_support={same_origin_support}; stale={stale}; not_found={not_found}; absent={absent}")
    return base,basis,independent,source_count,best


def classify_claim_conflict(a: ClaimRecord, b: ClaimRecord) -> ContradictionClass:
    if a.claim_key != b.claim_key or a.value == b.value:
        return ContradictionClass.UNRESOLVED
    aa,bb=a.applicability,b.applicability
    a_until=_parse_ts(aa.effective_until); b_from=_parse_ts(bb.effective_from)
    b_until=_parse_ts(bb.effective_until); a_from=_parse_ts(aa.effective_from)
    if (a_until and b_from and a_until <= b_from) or (b_until and a_from and b_until <= a_from):
        return ContradictionClass.TEMPORAL_TRANSITION
    if aa.software_version and bb.software_version and aa.software_version != bb.software_version:
        return ContradictionClass.VERSION_DIFFERENCE
    if aa.environment and bb.environment and aa.environment != bb.environment:
        return ContradictionClass.ENVIRONMENT_DIFFERENCE
    if aa.configuration_profile and bb.configuration_profile and aa.configuration_profile != bb.configuration_profile:
        return ContradictionClass.CONFIGURATION_DIFFERENCE
    if aa.deployment_id and bb.deployment_id and aa.deployment_id != bb.deployment_id:
        return ContradictionClass.DEPLOYMENT_CUSTOMIZATION
    if aa.terminology_namespace and bb.terminology_namespace and aa.terminology_namespace != bb.terminology_namespace:
        return ContradictionClass.TERMINOLOGY_DIFFERENCE
    if (aa.workflow_context and bb.workflow_context and aa.workflow_context != bb.workflow_context) or (aa.actor_context and bb.actor_context and aa.actor_context != bb.actor_context):
        return ContradictionClass.USER_OR_WORKFLOW_DIFFERENCE
    tier_gap=abs(int(a.evidence_tier)-int(b.evidence_tier))
    if tier_gap >= 2 and min(a.confidence,b.confidence) >= 40:
        return ContradictionClass.SOURCE_QUALITY_DIFFERENCE
    if min(a.independent_support_count,b.independent_support_count) == 0 or min(a.confidence,b.confidence) < 40:
        return ContradictionClass.INCOMPLETE_EVIDENCE
    return ContradictionClass.TRUE_CONTRADICTION


def _status_for_confidence(conf:int, opposed:bool, superseded:bool=False):
    if superseded: return ClaimStatus.SUPERSEDED
    if opposed and conf < 60: return ClaimStatus.CONTRADICTED
    if conf>=90:return ClaimStatus.CONFIRMED
    if conf>=75:return ClaimStatus.LIKELY
    if conf>=40:return ClaimStatus.PLAUSIBLE
    return ClaimStatus.UNRESOLVED


def information_gain_rank(questions: Iterable[OpenQuestionRecord], duplicate_penalty: Mapping[str,float] | None=None):
    duplicate_penalty=duplicate_penalty or {}
    rows=[]
    for q in questions:
        penalty=max(0.0,min(0.95,float(duplicate_penalty.get(q.question_id,0.0))))
        rows.append((q.priority*(1-penalty),q))
    return tuple(q for _,q in sorted(rows,key=lambda x:(-x[0],x[1].question_id)))


def _synthesis_conclusion(claims: Sequence[ClaimRecord]) -> str:
    top=sorted(claims,key=lambda c:(-c.confidence,c.claim_id))
    return "; ".join(f"{c.canonical_claim} [{c.status.value} {c.confidence}%]" for c in top[:3])


