from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from ._epistemic_base import *
from ._epistemic_base import _digest, _norm
from ._epistemic_model import *
from ._epistemic_source_logic import *
from ._epistemic_source_logic import _canonicalize_provenance, _status_for_confidence, _synthesis_conclusion

def reconcile(model: SharedEpistemicModel, *, peer_evidence_ids: Iterable[str]=(), cancel_resolved_below_priority: float=0.0) -> ReconciliationResult:
    validate_model_provenance(model)
    collapsed,alias=collapse_source_identities(model.sources)
    canonical_instances,canonical_evidence=_canonicalize_provenance(model,collapsed,alias)
    canonical_model=replace(model,sources=collapsed,source_instances=canonical_instances,evidence=canonical_evidence)
    validate_model_provenance(canonical_model)
    e_by={e.evidence_id:e for e in canonical_evidence}
    peer_ids=frozenset(peer_evidence_ids)
    unknown_peer=peer_ids-set(e_by)
    if unknown_peer:
        raise EpistemicError("peer evidence attribution references unknown evidence")
    if any(not e_by[eid].originating_agent for eid in peer_ids):
        raise EpistemicError("peer evidence attribution requires originating_agent provenance")

    changed=[]; claims=[]; independent_confirmations=0; complete=0; confidence_revisions=0
    for c in model.claims:
        conf,basis,ind,src_count,best=calibrated_confidence(c,e_by,alias)
        opposed=bool(c.evidence_against)
        status=_status_for_confidence(conf,opposed,c.superseded_by is not None)
        nc=replace(c,confidence=conf,confidence_basis=basis,independent_support_count=ind,source_identity_count=src_count,evidence_tier=best,status=status)
        if nc!=c:
            changed.append(c.claim_id); confidence_revisions += int(conf!=c.confidence)
        if ind>1:
            independent_confirmations += 1
        if c.evidence_for or c.evidence_against:
            complete += 1
        claims.append(nc)

    contradictions=[]; temporal=0; resolved=0
    by_key: dict[str,list[ClaimRecord]]={}
    for c in claims:
        by_key.setdefault(c.claim_key,[]).append(c)
    resolved_classes={
        ContradictionClass.TEMPORAL_TRANSITION, ContradictionClass.VERSION_DIFFERENCE,
        ContradictionClass.ENVIRONMENT_DIFFERENCE, ContradictionClass.CONFIGURATION_DIFFERENCE,
        ContradictionClass.DEPLOYMENT_CUSTOMIZATION, ContradictionClass.TERMINOLOGY_DIFFERENCE,
        ContradictionClass.USER_OR_WORKFLOW_DIFFERENCE, ContradictionClass.SOURCE_QUALITY_DIFFERENCE,
    }
    for group in by_key.values():
        for i,a in enumerate(group):
            for b in group[i+1:]:
                if a.value==b.value:
                    continue
                cls=classify_claim_conflict(a,b)
                is_resolved=cls in resolved_classes
                if cls==ContradictionClass.TEMPORAL_TRANSITION:
                    temporal += 1
                if is_resolved:
                    resolved += 1
                contradictions.append(ContradictionRecord(
                    contradiction_id="ctr-"+_digest([a.claim_id,b.claim_id])[:16], claim_ids=(a.claim_id,b.claim_id), classification=cls,
                    supporting_evidence=a.evidence_for, conflicting_evidence=b.evidence_for+b.evidence_against,
                    resolution=(f"reclassified as {cls.value}" if is_resolved else None),
                    remaining_uncertainty=(None if is_resolved else "requires discriminating evidence"), resolved=is_resolved
                ))

    hypotheses=[]; falsified=0
    claim_map={c.claim_id:c for c in claims}
    for h in model.hypotheses:
        opposing=sum(1 for cid in h.opposing_claims if cid in claim_map and claim_map[cid].confidence>=75)
        supporting=sum(1 for cid in h.supporting_claims if cid in claim_map and claim_map[cid].confidence>=75)
        status=h.status; probability=h.probability_or_confidence; reason=h.probability_change_reason
        if opposing and not supporting:
            status=HypothesisStatus.FALSIFIED; probability=min(probability,15); reason="strong opposing claim after reconciliation"; falsified += int(h.status!=HypothesisStatus.FALSIFIED)
        elif supporting>opposing:
            status=HypothesisStatus.SUPPORTED; probability=max(probability,80); reason="strong supporting claims after reconciliation"
        hypotheses.append(replace(h,status=status,probability_or_confidence=probability,probability_change_reason=reason))

    ranked=information_gain_rank(model.open_questions)
    cancelled=tuple(q.question_id for q in ranked if q.status=="RESOLVED" or q.priority<=cancel_resolved_below_priority)
    new_generation=model.generation+1
    conclusion=_synthesis_conclusion(claims)

    peer_changed=False
    if peer_ids:
        counterfactual=[]
        for c in model.claims:
            stripped=replace(c,
                evidence_for=tuple(eid for eid in c.evidence_for if eid not in peer_ids),
                evidence_against=tuple(eid for eid in c.evidence_against if eid not in peer_ids),
            )
            conf,basis,ind,src_count,best=calibrated_confidence(stripped,e_by,alias)
            counterfactual.append(replace(stripped,confidence=conf,confidence_basis=basis,independent_support_count=ind,source_identity_count=src_count,evidence_tier=best,status=_status_for_confidence(conf,bool(stripped.evidence_against),stripped.superseded_by is not None)))
        peer_changed=_norm(_synthesis_conclusion(counterfactual)) != _norm(conclusion)

    instances_collapsed=max(0,len(canonical_instances)-len({item.source_identity_id for item in canonical_instances}))
    tele=ReconciliationTelemetry(
        unique_source_origins=len(collapsed), source_instances_collapsed=instances_collapsed,
        claims_with_complete_provenance_pct=(100.0*complete/len(claims) if claims else 100.0), contradictions_opened=len(contradictions), contradictions_resolved=resolved,
        temporal_conflicts_reclassified=temporal, hypotheses_generated=len(hypotheses), hypotheses_falsified=falsified,
        independent_confirmations=independent_confirmations,
        evidence_reuse_rate=(sum(max(0,len(c.evidence_for)+len(c.evidence_against)-1) for c in claims)/max(1,len(canonical_evidence))),
        redundant_research_rate=(instances_collapsed/max(1,len(canonical_instances))), minority_findings_preserved=sum(1 for c in claims if c.minority_finding),
        tasks_cancelled_after_reconciliation=len(cancelled), confidence_revisions=confidence_revisions, model_revisions=1,
        conclusions_changed_after_peer_evidence=int(peer_changed)
    )
    top=sorted(claims,key=lambda c:(-c.confidence,c.claim_id))
    synthesis=SynthesisOutput("syn-"+_digest([model.project_id,new_generation,conclusion])[:16],new_generation,conclusion,tuple(c.claim_id for c in top[:3]),tuple(q.question_id for q in ranked if q.question_id not in cancelled))
    transitions=tuple(TemporalTransitionRecord("tr-"+c.contradiction_id[4:],"reconciled-claim","prior","current",None,c.supporting_evidence+c.conflicting_evidence) for c in contradictions if c.classification==ContradictionClass.TEMPORAL_TRANSITION)
    revision=ModelRevisionRecord("rev-"+_digest([model.project_id,new_generation,changed])[:16],new_generation,model.generation,"periodic reconciliation",tuple(changed),tuple(c.contradiction_id for c in contradictions))
    reconciliation=ReconciliationRecord("rec-"+_digest([model.project_id,new_generation,alias])[:16],new_generation,"EVIDENCE_OR_PEER_UPDATE",alias,tuple(changed),tuple(c.contradiction_id for c in contradictions),tuple(h.hypothesis_id for h in hypotheses),cancelled)
    new=replace(model,generation=new_generation,parent_generation=model.generation,sources=collapsed,source_instances=canonical_instances,evidence=canonical_evidence,claims=tuple(claims),hypotheses=tuple(hypotheses),contradictions=tuple(contradictions),temporal_transitions=model.temporal_transitions+transitions,model_revisions=model.model_revisions+(revision,),reconciliations=model.reconciliations+(reconciliation,),syntheses=model.syntheses+(synthesis,),telemetry=tele)
    return ReconciliationResult(new,tuple(changed),cancelled,alias,peer_changed)


