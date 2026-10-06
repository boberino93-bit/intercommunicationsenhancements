from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from ._epistemic_primitives import *
from ._epistemic_primitives import _digest, _norm, _parse_ts

@dataclass(frozen=True)
class SourceIdentity:
    source_identity_id: str
    canonical_origin: str | None
    publisher: str | None
    title: str | None
    publication_date: str | None
    version: str | None
    canonical_identifier: str | None
    content_hash: str | None
    derived_from: tuple[str,...]=()
    metadata: Mapping[str,object]=field(default_factory=dict)

    def origin_key(self) -> str:
        lineage_root = sorted(_norm(x) for x in self.derived_from if x)
        if lineage_root:
            return "derived:" + _digest(lineage_root)
        if self.content_hash:
            return "hash:" + self.content_hash.lower()
        return "meta:" + _digest([_norm(self.canonical_origin), _norm(self.publisher), _norm(self.title), self.publication_date or "", _norm(self.version), _norm(self.canonical_identifier)])


@dataclass(frozen=True)
class SourceInstance:
    source_instance_id: str; source_identity_id: str; locator: str; captured_at: str | None=None; content_hash: str | None=None; instance_type: str="UNKNOWN"


@dataclass(frozen=True)
class NegativeEvidence:
    result: str  # NOT_FOUND means search did not locate it; ABSENT means inspected authoritative surface asserts absence.
    search_scope: str
    surfaces_inspected: tuple[str,...]
    search_date: str
    relevant_versions: tuple[str,...]=()
    confidence: int=50

    def __post_init__(self):
        if self.result not in {"NOT_FOUND", "ABSENT"}:
            raise EpistemicError("negative evidence result must be NOT_FOUND or ABSENT")
        if not isinstance(self.surfaces_inspected, tuple) or not self.surfaces_inspected:
            raise EpistemicError("negative evidence must record inspected surfaces")
        if not all(isinstance(item, str) and item.strip() for item in self.surfaces_inspected):
            raise EpistemicError("negative evidence surfaces must be non-empty strings")
        if not 0 <= self.confidence <= 100:
            raise EpistemicError("negative evidence confidence must be 0..100")
        _parse_ts(self.search_date)


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    source_instance_id: str
    source_identity_id: str
    tier: EvidenceTier
    summary: str
    supports: tuple[str,...]=()
    opposes: tuple[str,...]=()
    applicability: Applicability=Applicability()
    direct: bool=True
    negative: NegativeEvidence | None=None
    originating_agent: str | None=None


@dataclass(frozen=True)
class ClaimRecord:
    claim_id: str
    canonical_claim: str
    claim_key: str
    value: str
    status: ClaimStatus=ClaimStatus.UNRESOLVED
    confidence: int=50
    confidence_basis: str="unreconciled"
    evidence_for: tuple[str,...]=()
    evidence_against: tuple[str,...]=()
    evidence_tier: EvidenceTier=EvidenceTier.INFERENCE
    applicability: Applicability=Applicability()
    dependencies: tuple[str,...]=()
    related_entities: tuple[str,...]=()
    originating_agent: str | None=None
    current_owner_or_reviewer: str | None=None
    independent_support_count: int=0
    source_identity_count: int=0
    last_reviewed: str | None=None
    supersedes: tuple[str,...]=()
    superseded_by: str | None=None
    minority_finding: bool=False

    def __post_init__(self):
        if not 0 <= self.confidence <= 100: raise EpistemicError("claim confidence must be 0..100")


@dataclass(frozen=True)
class PredictedObservation:
    observation_id: str; statement: str; expected_if_true: bool=True

@dataclass(frozen=True)
class DiscriminatingTest:
    test_id: str; description: str; expected_by_hypothesis: Mapping[str,str]; cost: float=1.0; completed_result: str | None=None

@dataclass(frozen=True)
class HypothesisRecord:
    hypothesis_id: str
    statement: str
    probability_or_confidence: int
    supporting_claims: tuple[str,...]=()
    opposing_claims: tuple[str,...]=()
    predicted_observations: tuple[PredictedObservation,...]=()
    discriminating_tests: tuple[DiscriminatingTest,...]=()
    falsification_attempts: tuple[str,...]=()
    last_probability_change: str | None=None
    probability_change_reason: str | None=None
    owner: str | None=None
    status: HypothesisStatus=HypothesisStatus.ACTIVE
    competes_with: tuple[str,...]=()


@dataclass(frozen=True)
class ContradictionRecord:
    contradiction_id: str
    claim_ids: tuple[str,...]
    classification: ContradictionClass
    supporting_evidence: tuple[str,...]
    conflicting_evidence: tuple[str,...]
    assigned_reconciler: str | None=None
    reconciliation_actions: tuple[str,...]=()
    resolution: str | None=None
    remaining_uncertainty: str | None=None
    model_change_refs: tuple[str,...]=()
    resolved: bool=False



@dataclass(frozen=True)
class VersionRecord:
    version_id: str; product: str; version: str; effective_from: str | None=None; effective_until: str | None=None; metadata: Mapping[str,object]=field(default_factory=dict)

@dataclass(frozen=True)
class EnvironmentRecord:
    environment_id: str; name: str; environment_type: str; deployment_id: str | None=None; metadata: Mapping[str,object]=field(default_factory=dict)

@dataclass(frozen=True)
class TemporalTransitionRecord:
    transition_id: str; subject_key: str; from_value: str; to_value: str; effective_at: str | None; evidence_refs: tuple[str,...]=()

@dataclass(frozen=True)
class CausalChainRecord:
    causal_chain_id: str; claim_ids: tuple[str,...]; relationship_ids: tuple[str,...]=(); confidence: int=50

@dataclass(frozen=True)
class ModelRevisionRecord:
    revision_id: str; generation: int; parent_generation: int | None; reason: str; changed_claim_ids: tuple[str,...]=(); contradiction_refs: tuple[str,...]=(); created_at: str | None=None

@dataclass(frozen=True)
class ReconciliationRecord:
    reconciliation_id: str; generation: int; trigger: str; source_identity_collapses: Mapping[str,str]; changed_claim_ids: tuple[str,...]; contradiction_refs: tuple[str,...]; hypothesis_refs: tuple[str,...]; cancelled_or_redirected_question_refs: tuple[str,...]; remaining_gaps: tuple[str,...]=()

@dataclass(frozen=True)
class SynthesisOutput:
    synthesis_id: str; model_generation: int; conclusion: str; supporting_claims: tuple[str,...]; unresolved_questions: tuple[str,...]=(); created_at: str | None=None


@dataclass(frozen=True)
class ResearchBroadcast:
    message_id: str
    project_id: str
    intent: str
    sender_role: str
    sender_agent_instance: str
    discovery: str
    source_identity_refs: tuple[str,...]=()
    source_instance_refs: tuple[str,...]=()
    evidence_tiers: tuple[int,...]=()
    temporal_scope: str | None=None
    environment: str | None=None
    version: str | None=None
    claims_affected: tuple[str,...]=()
    significance: str="MEDIUM"
    confidence: int=50
    conflict: str | None=None
    request: str | None=None
    authority_conveyed: bool=False

    SCHEMA = "org-agent-mesh/research-epistemic-broadcast/v1"
    ALLOWED_INTENTS = frozenset({
        "DISCOVERY_BROADCAST", "VERIFICATION_REQUEST", "CONTRADICTION_RAISED",
        "SOURCE_DUPLICATE_NOTICE", "NEGATIVE_EVIDENCE", "HYPOTHESIS_PROPOSED",
        "HYPOTHESIS_TEST_RESULT", "RECONCILIATION_UPDATE", "MODEL_REVISION_NOTICE",
    })
    ALLOWED_ROLES = frozenset({"RESEARCH", "RESEARCHER_1", "RESEARCHER_2", "RESEARCHER_3", "MANAGER"})

    def __post_init__(self):
        if self.authority_conveyed:
            raise AuthorityError("research broadcasts cannot convey authority")
        if self.intent not in self.ALLOWED_INTENTS:
            raise EpistemicError("unsupported research message intent")
        if self.sender_role.upper() not in self.ALLOWED_ROLES:
            raise EpistemicError("epistemic broadcasts are limited to Research and Manager roles")
        if not self.sender_agent_instance.strip():
            raise EpistemicError("sender agent instance is required")
        if self.significance not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
            raise EpistemicError("invalid broadcast significance")
        if not 0 <= self.confidence <= 100:
            raise EpistemicError("broadcast confidence must be 0..100")
        if any(int(tier) not in range(1, 7) for tier in self.evidence_tiers):
            raise EpistemicError("broadcast evidence tiers must be 1..6")

    def to_payload(self) -> dict[str, object]:
        return {
            "schema": self.SCHEMA,
            "message_id": self.message_id,
            "project_id": self.project_id,
            "intent": self.intent,
            "sender_role": self.sender_role.upper(),
            "sender_agent_instance": self.sender_agent_instance,
            "discovery": self.discovery,
            "source_identity_refs": list(self.source_identity_refs),
            "source_instance_refs": list(self.source_instance_refs),
            "evidence_tiers": [int(tier) for tier in self.evidence_tiers],
            "temporal_scope": self.temporal_scope,
            "environment": self.environment,
            "version": self.version,
            "claims_affected": list(self.claims_affected),
            "significance": self.significance,
            "confidence": self.confidence,
            "conflict": self.conflict,
            "request": self.request,
            "authority_conveyed": False,
        }


def require_existing_coordination_permit(broadcast: ResearchBroadcast, permit) -> bool:
    """Bind an epistemic broadcast to a permit issued by the existing coordination publication lane.

    This function does not mint authority and does not create a second transport. Callers must first
    obtain the canonical CoordinationPublicationPermit through coordination_publication.py.
    """
    if permit is None:
        raise AuthorityError("canonical coordination publication permit is required")
    if getattr(permit, "project_id", None) != broadcast.project_id:
        raise AuthorityError("coordination permit project mismatch")
    if str(getattr(permit, "role", "")).upper() != broadcast.sender_role.upper():
        raise AuthorityError("coordination permit role mismatch")
    if bool(getattr(permit, "authority_conveyed", True)):
        raise AuthorityError("coordination permit must be non-authoritative")
    if not (bool(getattr(permit, "artifactory_allowed", False)) or bool(getattr(permit, "github_backup_allowed", False))):
        raise AuthorityError("coordination permit has no approved publication destination")
    return True

