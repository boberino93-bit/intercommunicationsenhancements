from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ._epistemic_base import *

@dataclass(frozen=True)
class ReconciliationTelemetry:
    unique_source_origins: int=0
    source_instances_collapsed: int=0
    claims_with_complete_provenance_pct: float=0.0
    contradictions_opened: int=0
    contradictions_resolved: int=0
    temporal_conflicts_reclassified: int=0
    hypotheses_generated: int=0
    hypotheses_falsified: int=0
    independent_confirmations: int=0
    evidence_reuse_rate: float=0.0
    redundant_research_rate: float=0.0
    minority_findings_preserved: int=0
    tasks_cancelled_after_reconciliation: int=0
    confidence_revisions: int=0
    model_revisions: int=0
    conclusions_changed_after_peer_evidence: int=0


@dataclass(frozen=True)
class SharedEpistemicModel:
    project_id: str
    generation: int
    parent_generation: int | None
    sources: tuple[SourceIdentity,...]=()
    source_instances: tuple[SourceInstance,...]=()
    evidence: tuple[EvidenceItem,...]=()
    claims: tuple[ClaimRecord,...]=()
    hypotheses: tuple[HypothesisRecord,...]=()
    contradictions: tuple[ContradictionRecord,...]=()
    entities: tuple[EntityRecord,...]=()
    relationships: tuple[RelationshipRecord,...]=()
    events: tuple[EventRecord,...]=()
    deployments: tuple[DeploymentContextRecord,...]=()
    versions: tuple[VersionRecord,...]=()
    environments: tuple[EnvironmentRecord,...]=()
    temporal_transitions: tuple[TemporalTransitionRecord,...]=()
    causal_chains: tuple[CausalChainRecord,...]=()
    model_revisions: tuple[ModelRevisionRecord,...]=()
    reconciliations: tuple[ReconciliationRecord,...]=()
    terminology: tuple[TermAliasRecord,...]=()
    open_questions: tuple[OpenQuestionRecord,...]=()
    syntheses: tuple[SynthesisOutput,...]=()
    telemetry: ReconciliationTelemetry=ReconciliationTelemetry()
    authority: bool=False

    def __post_init__(self):
        if self.authority: raise AuthorityError("epistemic model cannot carry consequence authority")
        if self.generation < 0: raise EpistemicError("generation must be nonnegative")


@dataclass(frozen=True)
class ReconciliationResult:
    model: SharedEpistemicModel
    changed_claim_ids: tuple[str,...]
    cancelled_question_ids: tuple[str,...]
    duplicate_identity_map: Mapping[str,str]
    peer_changed_conclusion: bool


