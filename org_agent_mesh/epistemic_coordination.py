from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum, IntEnum
from hashlib import sha256
import json
from typing import Mapping, Sequence


def _norm(value: str | None) -> str:
    return " ".join((value or "").strip().casefold().split())


def _digest(value) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _ts(value: str | None):
    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


class EpistemicError(ValueError):
    pass


class AuthorityError(PermissionError):
    pass


class StaleModelRevision(RuntimeError):
    pass


class EvidenceTier(IntEnum):
    DIRECT_CURRENT_OPERATIONAL = 1
    TARGET_DEPLOYMENT = 2
    CURRENT_AUTHORITATIVE = 3
    HISTORICAL_AUTHORITATIVE = 4
    SECONDARY = 5
    INFERENCE = 6


class ClaimStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    LIKELY = "LIKELY"
    PLAUSIBLE = "PLAUSIBLE"
    UNRESOLVED = "UNRESOLVED"
    CONTRADICTED = "CONTRADICTED"
    SUPERSEDED = "SUPERSEDED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class TemporalStatus(str, Enum):
    CURRENT = "CURRENT"
    HISTORICAL = "HISTORICAL"
    TRANSITIONAL = "TRANSITIONAL"
    SUPERSEDED = "SUPERSEDED"
    FUTURE = "FUTURE"
    UNKNOWN = "UNKNOWN"


class ContradictionClass(str, Enum):
    TEMPORAL_TRANSITION = "TEMPORAL_TRANSITION"
    VERSION_DIFFERENCE = "VERSION_DIFFERENCE"
    ENVIRONMENT_DIFFERENCE = "ENVIRONMENT_DIFFERENCE"
    CONFIGURATION_DIFFERENCE = "CONFIGURATION_DIFFERENCE"
    DEPLOYMENT_CUSTOMIZATION = "DEPLOYMENT_CUSTOMIZATION"
    TERMINOLOGY_DIFFERENCE = "TERMINOLOGY_DIFFERENCE"
    USER_OR_WORKFLOW_DIFFERENCE = "USER_OR_WORKFLOW_DIFFERENCE"
    SOURCE_QUALITY_DIFFERENCE = "SOURCE_QUALITY_DIFFERENCE"
    INCOMPLETE_EVIDENCE = "INCOMPLETE_EVIDENCE"
    TRUE_CONTRADICTION = "TRUE_CONTRADICTION"
    UNRESOLVED = "UNRESOLVED"


class HypothesisStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUPPORTED = "SUPPORTED"
    FALSIFIED = "FALSIFIED"
    SUPERSEDED = "SUPERSEDED"
    UNRESOLVED = "UNRESOLVED"


class PeerDisposition(str, Enum):
    SUPPORT = "SUPPORT"
    QUALIFY = "QUALIFY"
    CONTRADICT = "CONTRADICT"
    DUPLICATE_ORIGIN = "DUPLICATE_ORIGIN"
    TEMPORAL_VARIANT = "TEMPORAL_VARIANT"
    CONTEXT_VARIANT = "CONTEXT_VARIANT"
    UNRELATED = "UNRELATED"


class ResearchMode(str, Enum):
    EXPLORER = "EXPLORER"
    DOMAIN_SPECIALIST = "DOMAIN_SPECIALIST"
    HISTORIAN = "HISTORIAN"
    DEPLOYMENT_SPECIFIC = "DEPLOYMENT_SPECIFIC"
    ARCHITECTURE_MAPPER = "ARCHITECTURE_MAPPER"
    INDEPENDENT_VALIDATOR = "INDEPENDENT_VALIDATOR"
    SKEPTIC = "SKEPTIC"
    RED_TEAM = "RED_TEAM"
    SOURCE_DEDUP = "SOURCE_DEDUP"
    CONTRADICTION_ANALYST = "CONTRADICTION_ANALYST"
    RECONCILER = "RECONCILER"
    SYNTHESIS = "SYNTHESIS"


@dataclass(frozen=True)
class ActorContext:
    project_id: str
    role: str
    agent_instance_id: str
    capabilities: frozenset[str] = frozenset()

    def can_accept_model(self) -> bool:
        return self.role.upper() == "PRIMARY" and "WRITE_ACCEPTED_STATE" in self.capabilities


@dataclass(frozen=True)
class Applicability:
    environment: str | None = None
    software_version: str | None = None
    protocol_version: str | None = None
    deployment_id: str | None = None
    workflow_context: str | None = None
    actor_context: str | None = None
    observed_at: str | None = None
    published_at: str | None = None
    effective_from: str | None = None
    effective_until: str | None = None
    temporal_status: TemporalStatus = TemporalStatus.UNKNOWN

    def __post_init__(self):
        for field_name in ("observed_at", "published_at", "effective_from", "effective_until"):
            _ts(getattr(self, field_name))


@dataclass(frozen=True)
class EntityRecord:
    entity_id: str
    canonical_name: str
    entity_type: str
    aliases: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class RelationshipRecord:
    relationship_id: str
    subject_entity_id: str
    predicate: str
    object_entity_id: str
    applicability: Applicability = Applicability()
    confidence: int = 50


@dataclass(frozen=True)
class EventRecord:
    event_id: str
    event_type: str
    entity_ids: tuple[str, ...]
    occurred_at: str
    applicability: Applicability = Applicability()
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class DeploymentContextRecord:
    deployment_id: str
    environment: str
    software_version: str | None
    configuration_refs: tuple[str, ...] = ()
    effective_from: str | None = None
    effective_until: str | None = None


@dataclass(frozen=True)
class TermAliasRecord:
    term: str
    canonical_entity_id: str
    alias_type: str
    valid_from: str | None = None
    valid_until: str | None = None


@dataclass(frozen=True)
class OpenQuestionRecord:
    question_id: str
    question: str
    decision_impact: float
    dependency_fanout: float
    expected_cost: float
    expected_information_gain: float
    status: str = "OPEN"

    @property
    def priority(self) -> float:
        if self.expected_cost <= 0:
            raise EpistemicError("expected_cost must be > 0")
        return self.expected_information_gain * self.decision_impact * self.dependency_fanout / self.expected_cost


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
    derived_from: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def origin_key(self) -> str:
        lineage = sorted(_norm(value) for value in self.derived_from if value)
        if lineage:
            return "derived:" + _digest(lineage)
        if self.content_hash:
            return "hash:" + self.content_hash.lower()
        return "meta:" + _digest([
            _norm(self.canonical_origin), _norm(self.publisher), _norm(self.title), self.publication_date or "",
            _norm(self.version), _norm(self.canonical_identifier),
        ])


@dataclass(frozen=True)
class SourceInstance:
    source_instance_id: str
    source_identity_id: str
    locator: str
    captured_at: str | None = None
    content_hash: str | None = None
    instance_type: str = "UNKNOWN"


@dataclass(frozen=True)
class NegativeEvidence:
    result: str
    search_scope: str
    surfaces_inspected: tuple[str, ...]
    search_date: str
    relevant_versions: tuple[str, ...] = ()
    confidence: int = 50

    def __post_init__(self):
        if self.result not in {"NOT_FOUND", "ABSENT"}:
            raise EpistemicError("negative evidence result must be NOT_FOUND or ABSENT")
        _ts(self.search_date)


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    source_instance_id: str
    source_identity_id: str
    tier: EvidenceTier
    summary: str
    supports: tuple[str, ...] = ()
    opposes: tuple[str, ...] = ()
    applicability: Applicability = Applicability()
    direct: bool = True
    negative: NegativeEvidence | None = None
    originating_agent: str | None = None


@dataclass(frozen=True)
class ClaimRecord:
    claim_id: str
    canonical_claim: str
    claim_key: str
    value: str
    status: ClaimStatus = ClaimStatus.UNRESOLVED
    confidence: int = 50
    confidence_basis: str = "unreconciled"
    evidence_for: tuple[str, ...] = ()
    evidence_against: tuple[str, ...] = ()
    evidence_tier: EvidenceTier = EvidenceTier.INFERENCE
    applicability: Applicability = Applicability()
    dependencies: tuple[str, ...] = ()
    related_entities: tuple[str, ...] = ()
    originating_agent: str | None = None
    current_owner_or_reviewer: str | None = None
    independent_support_count: int = 0
    source_identity_count: int = 0
    last_reviewed: str | None = None
    supersedes: tuple[str, ...] = ()
    superseded_by: str | None = None
    minority_finding: bool = False

    def __post_init__(self):
        if not 0 <= self.confidence <= 100:
            raise EpistemicError("claim confidence must be 0..100")


@dataclass(frozen=True)
class PredictedObservation:
    observation_id: str
    statement: str
    expected_if_true: bool = True


@dataclass(frozen=True)
class DiscriminatingTest:
    test_id: str
    description: str
    expected_by_hypothesis: Mapping[str, str]
    cost: float = 1.0
    completed_result: str | None = None


@dataclass(frozen=True)
class HypothesisRecord:
    hypothesis_id: str
    statement: str
    probability_or_confidence: int
    supporting_claims: tuple[str, ...] = ()
    opposing_claims: tuple[str, ...] = ()
    predicted_observations: tuple[PredictedObservation, ...] = ()
    discriminating_tests: tuple[DiscriminatingTest, ...] = ()
    falsification_attempts: tuple[str, ...] = ()
    last_probability_change: str | None = None
    probability_change_reason: str | None = None
    owner: str | None = None
    status: HypothesisStatus = HypothesisStatus.ACTIVE
    competes_with: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContradictionRecord:
    contradiction_id: str
    claim_ids: tuple[str, ...]
    classification: ContradictionClass
    supporting_evidence: tuple[str, ...]
    conflicting_evidence: tuple[str, ...]
    assigned_reconciler: str | None = None
    reconciliation_actions: tuple[str, ...] = ()
    resolution: str | None = None
    remaining_uncertainty: str | None = None
    model_change_refs: tuple[str, ...] = ()
    resolved: bool = False


@dataclass(frozen=True)
class VersionRecord:
    version_id: str
    product: str
    version: str
    effective_from: str | None = None
    effective_until: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class EnvironmentRecord:
    environment_id: str
    name: str
    environment_type: str
    deployment_id: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class TemporalTransitionRecord:
    transition_id: str
    subject_key: str
    from_value: str
    to_value: str
    effective_at: str | None
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class CausalChainRecord:
    causal_chain_id: str
    ordered_claim_ids: tuple[str, ...]
    confidence: int
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class ModelRevisionRecord:
    revision_id: str
    generation: int
    parent_generation: int
    reason: str
    changed_claim_ids: tuple[str, ...]
    contradiction_refs: tuple[str, ...]


@dataclass(frozen=True)
class ReconciliationRecord:
    reconciliation_id: str
    generation: int
    trigger: str
    duplicate_source_aliases: Mapping[str, str]
    changed_claim_ids: tuple[str, ...]
    contradiction_refs: tuple[str, ...]
    hypothesis_refs: tuple[str, ...]
    cancelled_question_refs: tuple[str, ...]


@dataclass(frozen=True)
class SynthesisOutput:
    synthesis_id: str
    generation: int
    conclusion: str
    claim_refs: tuple[str, ...]
    open_question_refs: tuple[str, ...]


@dataclass(frozen=True)
class ResearchBroadcast:
    message_id: str
    project_id: str
    intent: str
    sender_role: str
    sender_agent_instance: str
    discovery_summary: str
    claim_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    source_identity_refs: tuple[str, ...] = ()
    contradiction_refs: tuple[str, ...] = ()
    request: str | None = None
    authority_conveyed: bool = False

    def __post_init__(self):
        if self.authority_conveyed:
            raise AuthorityError("research broadcasts cannot convey authority")


@dataclass(frozen=True)
class FirstPassSubmission:
    agent_instance_id: str
    research_mode: ResearchMode
    payload_digest: str
    payload: object


@dataclass(frozen=True)
class ReconciliationTelemetry:
    unique_source_origins: int = 0
    source_instances_collapsed: int = 0
    claims_with_complete_provenance_pct: float = 0.0
    contradictions_opened: int = 0
    contradictions_resolved: int = 0
    temporal_conflicts_reclassified: int = 0
    hypotheses_generated: int = 0
    hypotheses_falsified: int = 0
    independent_confirmations: int = 0
    evidence_reuse_rate: float = 0.0
    redundant_research_rate: float = 0.0
    minority_findings_preserved: int = 0
    tasks_cancelled_after_reconciliation: int = 0
    confidence_revisions: int = 0
    model_revisions: int = 0
    conclusions_changed_after_peer_evidence: int = 0


@dataclass(frozen=True)
class SharedEpistemicModel:
    project_id: str
    generation: int = 0
    parent_generation: int | None = None
    entities: tuple[EntityRecord, ...] = ()
    relationships: tuple[RelationshipRecord, ...] = ()
    events: tuple[EventRecord, ...] = ()
    deployments: tuple[DeploymentContextRecord, ...] = ()
    term_aliases: tuple[TermAliasRecord, ...] = ()
    sources: tuple[SourceIdentity, ...] = ()
    source_instances: tuple[SourceInstance, ...] = ()
    evidence: tuple[EvidenceItem, ...] = ()
    claims: tuple[ClaimRecord, ...] = ()
    hypotheses: tuple[HypothesisRecord, ...] = ()
    contradictions: tuple[ContradictionRecord, ...] = ()
    versions: tuple[VersionRecord, ...] = ()
    environments: tuple[EnvironmentRecord, ...] = ()
    temporal_transitions: tuple[TemporalTransitionRecord, ...] = ()
    causal_chains: tuple[CausalChainRecord, ...] = ()
    open_questions: tuple[OpenQuestionRecord, ...] = ()
    model_revisions: tuple[ModelRevisionRecord, ...] = ()
    reconciliations: tuple[ReconciliationRecord, ...] = ()
    syntheses: tuple[SynthesisOutput, ...] = ()
    telemetry: ReconciliationTelemetry = ReconciliationTelemetry()


@dataclass(frozen=True)
class ReconciliationResult:
    model: SharedEpistemicModel
    changed_claim_ids: tuple[str, ...]
    cancelled_question_refs: tuple[str, ...]
    duplicate_source_aliases: Mapping[str, str]
    conclusion_changed_after_peer_evidence: bool


class BlindedRendezvous:
    def __init__(self, expected_agents: Sequence[str], *, threshold: int | None = None):
        self.expected_agents = tuple(dict.fromkeys(expected_agents))
        self.threshold = threshold or len(self.expected_agents)
        if not 1 <= self.threshold <= len(self.expected_agents):
            raise EpistemicError("invalid rendezvous threshold")
        self._sealed: dict[str, FirstPassSubmission] = {}
        self._open = False
        self._peer_classifications: dict[tuple[str, str], PeerDisposition] = {}

    def submit(self, agent_instance_id: str, research_mode: ResearchMode, payload) -> FirstPassSubmission:
        if self._open:
            raise EpistemicError("rendezvous already open")
        if agent_instance_id not in self.expected_agents:
            raise EpistemicError("unexpected rendezvous participant")
        digest = _digest(payload)
        existing = self._sealed.get(agent_instance_id)
        if existing:
            if existing.payload_digest != digest:
                raise EpistemicError("sealed first pass is immutable")
            return existing
        submission = FirstPassSubmission(agent_instance_id, research_mode, digest, payload)
        self._sealed[agent_instance_id] = submission
        return submission

    def peer_material(self):
        if not self._open:
            raise EpistemicError("peer material is blinded until rendezvous opens")
        return tuple(self._sealed[key] for key in sorted(self._sealed))

    def open(self, *, force_timeout: bool = False):
        if len(self._sealed) < self.threshold and not force_timeout:
            raise EpistemicError("rendezvous threshold not reached")
        self._open = True
        return self.peer_material()

    def classify_peer(self, reviewer: str, subject: str, disposition: PeerDisposition):
        if not self._open:
            raise EpistemicError("peer classification requires open rendezvous")
        if reviewer not in self._sealed or subject not in self._sealed:
            raise EpistemicError("unknown rendezvous participant")
        self._peer_classifications[(reviewer, subject)] = disposition


_BASE_CONFIDENCE = {
    EvidenceTier.DIRECT_CURRENT_OPERATIONAL: 90,
    EvidenceTier.TARGET_DEPLOYMENT: 85,
    EvidenceTier.CURRENT_AUTHORITATIVE: 78,
    EvidenceTier.HISTORICAL_AUTHORITATIVE: 66,
    EvidenceTier.SECONDARY: 55,
    EvidenceTier.INFERENCE: 40,
}


def collapse_source_identities(sources: Sequence[SourceIdentity]):
    by_origin: dict[str, SourceIdentity] = {}
    aliases: dict[str, str] = {}
    for source in sorted(sources, key=lambda item: item.source_identity_id):
        key = source.origin_key()
        canonical = by_origin.get(key)
        if canonical is None:
            by_origin[key] = source
            aliases[source.source_identity_id] = source.source_identity_id
        else:
            aliases[source.source_identity_id] = canonical.source_identity_id
    return tuple(by_origin[key] for key in sorted(by_origin)), aliases


def calibrated_confidence(claim: ClaimRecord, evidence_map: Mapping[str, EvidenceItem], source_map: Mapping[str, SourceIdentity], alias_map: Mapping[str, str]):
    support = [evidence_map[eid] for eid in claim.evidence_for if eid in evidence_map]
    oppose = [evidence_map[eid] for eid in claim.evidence_against if eid in evidence_map]
    if not support:
        return max(0, min(100, claim.confidence)), 0, 0, EvidenceTier.INFERENCE, "no supporting evidence"
    best = min(item.tier for item in support)
    origins = {alias_map.get(item.source_identity_id, item.source_identity_id) for item in support}
    duplicate_penalty = max(0, len(support) - len(origins)) * 4
    independence_bonus = min(12, max(0, len(origins) - 1) * 4)
    opposition_penalty = min(28, len(oppose) * 8)
    applicability_penalty = 0
    if claim.applicability.software_version is None:
        applicability_penalty += 3
    if claim.applicability.environment is None:
        applicability_penalty += 3
    historical_penalty = 8 if claim.applicability.temporal_status in {TemporalStatus.HISTORICAL, TemporalStatus.SUPERSEDED} else 0
    confidence = _BASE_CONFIDENCE[best] + independence_bonus - duplicate_penalty - opposition_penalty - applicability_penalty - historical_penalty
    confidence = max(0, min(100, confidence))
    basis = f"tier={int(best)} independent_origins={len(origins)} duplicates={len(support)-len(origins)} opposing={len(oppose)}"
    return confidence, len(origins), len({item.source_identity_id for item in support}), best, basis


def classify_claim_conflict(a: ClaimRecord, b: ClaimRecord) -> ContradictionClass:
    if a.claim_key != b.claim_key or a.value == b.value:
        return ContradictionClass.UNRESOLVED
    aa, bb = a.applicability, b.applicability
    if aa.effective_until and bb.effective_from and _ts(aa.effective_until) <= _ts(bb.effective_from):
        return ContradictionClass.TEMPORAL_TRANSITION
    if bb.effective_until and aa.effective_from and _ts(bb.effective_until) <= _ts(aa.effective_from):
        return ContradictionClass.TEMPORAL_TRANSITION
    if aa.software_version and bb.software_version and aa.software_version != bb.software_version:
        return ContradictionClass.VERSION_DIFFERENCE
    if aa.environment and bb.environment and aa.environment != bb.environment:
        return ContradictionClass.ENVIRONMENT_DIFFERENCE
    if aa.deployment_id and bb.deployment_id and aa.deployment_id != bb.deployment_id:
        return ContradictionClass.DEPLOYMENT_CUSTOMIZATION
    if aa.workflow_context and bb.workflow_context and aa.workflow_context != bb.workflow_context:
        return ContradictionClass.USER_OR_WORKFLOW_DIFFERENCE
    return ContradictionClass.TRUE_CONTRADICTION


def information_gain_rank(questions: Sequence[OpenQuestionRecord], duplicate_penalty: Mapping[str, float] | None = None):
    duplicate_penalty = duplicate_penalty or {}
    return tuple(sorted(questions, key=lambda q: (-(q.priority * duplicate_penalty.get(q.question_id, 1.0)), q.question_id)))


def _claim_status(confidence: int, opposed: bool, superseded: bool) -> ClaimStatus:
    if superseded:
        return ClaimStatus.SUPERSEDED
    if opposed and confidence < 50:
        return ClaimStatus.CONTRADICTED
    if confidence >= 88:
        return ClaimStatus.CONFIRMED
    if confidence >= 72:
        return ClaimStatus.LIKELY
    if confidence >= 50:
        return ClaimStatus.PLAUSIBLE
    return ClaimStatus.UNRESOLVED


def reconcile(model: SharedEpistemicModel, *, previous_synthesis: str | None = None, peer_evidence_arrived: bool = False, cancel_resolved_below_priority: float = 0.0) -> ReconciliationResult:
    collapsed, aliases = collapse_source_identities(model.sources)
    evidence_map = {item.evidence_id: item for item in model.evidence}
    source_map = {item.source_identity_id: item for item in model.sources}
    claims: list[ClaimRecord] = []
    changed: list[str] = []
    confidence_revisions = independent_confirmations = complete = 0
    for claim in model.claims:
        confidence, independent, source_count, best, basis = calibrated_confidence(claim, evidence_map, source_map, aliases)
        updated = replace(
            claim,
            confidence=confidence,
            confidence_basis=basis,
            independent_support_count=independent,
            source_identity_count=source_count,
            evidence_tier=best,
            status=_claim_status(confidence, bool(claim.evidence_against), claim.superseded_by is not None),
        )
        if updated != claim:
            changed.append(claim.claim_id)
            confidence_revisions += int(confidence != claim.confidence)
        independent_confirmations += int(independent > 1)
        complete += int(bool(claim.evidence_for or claim.evidence_against))
        claims.append(updated)

    contradictions: list[ContradictionRecord] = []
    by_key: dict[str, list[ClaimRecord]] = {}
    for claim in claims:
        by_key.setdefault(claim.claim_key, []).append(claim)
    resolved_classes = {
        ContradictionClass.TEMPORAL_TRANSITION,
        ContradictionClass.VERSION_DIFFERENCE,
        ContradictionClass.ENVIRONMENT_DIFFERENCE,
        ContradictionClass.DEPLOYMENT_CUSTOMIZATION,
        ContradictionClass.USER_OR_WORKFLOW_DIFFERENCE,
    }
    temporal_count = resolved_count = 0
    for group in by_key.values():
        for index, left in enumerate(group):
            for right in group[index + 1:]:
                if left.value == right.value:
                    continue
                classification = classify_claim_conflict(left, right)
                resolved = classification in resolved_classes
                temporal_count += int(classification == ContradictionClass.TEMPORAL_TRANSITION)
                resolved_count += int(resolved)
                contradictions.append(ContradictionRecord(
                    contradiction_id="ctr-" + _digest([left.claim_id, right.claim_id])[:16],
                    claim_ids=(left.claim_id, right.claim_id),
                    classification=classification,
                    supporting_evidence=left.evidence_for,
                    conflicting_evidence=right.evidence_for + right.evidence_against,
                    resolution=(f"reclassified as {classification.value}" if resolved else None),
                    remaining_uncertainty=(None if resolved else "requires discriminating evidence"),
                    resolved=resolved,
                ))

    claim_map = {claim.claim_id: claim for claim in claims}
    hypotheses: list[HypothesisRecord] = []
    falsified = 0
    for hypothesis in model.hypotheses:
        supporting = sum(1 for cid in hypothesis.supporting_claims if cid in claim_map and claim_map[cid].confidence >= 75)
        opposing = sum(1 for cid in hypothesis.opposing_claims if cid in claim_map and claim_map[cid].confidence >= 75)
        updated = hypothesis
        if opposing and not supporting:
            falsified += int(hypothesis.status != HypothesisStatus.FALSIFIED)
            updated = replace(hypothesis, status=HypothesisStatus.FALSIFIED, probability_or_confidence=min(hypothesis.probability_or_confidence, 15), probability_change_reason="strong opposing claim after reconciliation")
        elif supporting > opposing:
            updated = replace(hypothesis, status=HypothesisStatus.SUPPORTED, probability_or_confidence=max(hypothesis.probability_or_confidence, 80), probability_change_reason="strong supporting claims after reconciliation")
        hypotheses.append(updated)

    ranked = information_gain_rank(model.open_questions)
    cancelled = tuple(question.question_id for question in ranked if question.status == "RESOLVED" or question.priority <= cancel_resolved_below_priority)
    generation = model.generation + 1
    top = sorted(claims, key=lambda claim: (-claim.confidence, claim.claim_id))
    conclusion = "; ".join(f"{claim.canonical_claim} [{claim.status.value} {claim.confidence}%]" for claim in top[:3])
    peer_changed = bool(peer_evidence_arrived and previous_synthesis is not None and _norm(previous_synthesis) != _norm(conclusion))
    instances_collapsed = max(0, len(model.source_instances) - len({aliases.get(instance.source_identity_id, instance.source_identity_id) for instance in model.source_instances}))
    telemetry = ReconciliationTelemetry(
        unique_source_origins=len(collapsed),
        source_instances_collapsed=instances_collapsed,
        claims_with_complete_provenance_pct=(100.0 * complete / len(claims) if claims else 100.0),
        contradictions_opened=len(contradictions),
        contradictions_resolved=resolved_count,
        temporal_conflicts_reclassified=temporal_count,
        hypotheses_generated=len(hypotheses),
        hypotheses_falsified=falsified,
        independent_confirmations=independent_confirmations,
        evidence_reuse_rate=(sum(max(0, len(claim.evidence_for) + len(claim.evidence_against) - 1) for claim in claims) / max(1, len(model.evidence))),
        redundant_research_rate=(instances_collapsed / max(1, len(model.source_instances))),
        minority_findings_preserved=sum(1 for claim in claims if claim.minority_finding),
        tasks_cancelled_after_reconciliation=len(cancelled),
        confidence_revisions=confidence_revisions,
        model_revisions=1,
        conclusions_changed_after_peer_evidence=int(peer_changed),
    )
    synthesis = SynthesisOutput("syn-" + _digest([model.project_id, generation, conclusion])[:16], generation, conclusion, tuple(claim.claim_id for claim in top[:3]), tuple(question.question_id for question in ranked if question.question_id not in cancelled))
    transitions = tuple(TemporalTransitionRecord("tr-" + contradiction.contradiction_id[4:], "reconciled-claim", "prior", "current", None, contradiction.supporting_evidence + contradiction.conflicting_evidence) for contradiction in contradictions if contradiction.classification == ContradictionClass.TEMPORAL_TRANSITION)
    revision = ModelRevisionRecord("rev-" + _digest([model.project_id, generation, changed])[:16], generation, model.generation, "periodic reconciliation", tuple(changed), tuple(item.contradiction_id for item in contradictions))
    reconciliation = ReconciliationRecord("rec-" + _digest([model.project_id, generation, aliases])[:16], generation, "EVIDENCE_OR_PEER_UPDATE", aliases, tuple(changed), tuple(item.contradiction_id for item in contradictions), tuple(item.hypothesis_id for item in hypotheses), cancelled)
    updated_model = replace(model, generation=generation, parent_generation=model.generation, sources=collapsed, claims=tuple(claims), hypotheses=tuple(hypotheses), contradictions=tuple(contradictions), temporal_transitions=model.temporal_transitions + transitions, model_revisions=model.model_revisions + (revision,), reconciliations=model.reconciliations + (reconciliation,), syntheses=model.syntheses + (synthesis,), telemetry=telemetry)
    return ReconciliationResult(updated_model, tuple(changed), cancelled, aliases, peer_changed)


class AcceptedEpistemicStore:
    """Accepted epistemic state layered on the existing durable backend; this creates no second persistence plane."""

    NAMESPACE = "epistemic-model"
    RESOURCE_ID = "accepted-head"

    def __init__(self, backend, *, require_session=None):
        required = ("create", "read", "compare_and_set")
        if not all(callable(getattr(backend, name, None)) for name in required):
            raise TypeError("backend must satisfy DurableRecordBackend create/read/compare_and_set")
        self.backend = backend
        self.require_session = require_session

    def _authorize(self, actor_or_session, project_id: str):
        if self.require_session is not None:
            return self.require_session(actor_or_session, project_id, operation="accepted epistemic model mutation", capability="WRITE_ACCEPTED_STATE")
        if not isinstance(actor_or_session, ActorContext):
            raise AuthorityError("accepted epistemic writes require canonical session authorization")
        if actor_or_session.project_id != project_id:
            raise AuthorityError("project isolation violation")
        if not actor_or_session.can_accept_model():
            raise AuthorityError("epistemic confidence/consensus cannot create accepted-state authority")
        return actor_or_session

    @staticmethod
    def _jsonable(value):
        if isinstance(value, Enum):
            return value.value
        if hasattr(value, "__dataclass_fields__"):
            return {key: AcceptedEpistemicStore._jsonable(item) for key, item in asdict(value).items()}
        if isinstance(value, dict):
            return {str(key): AcceptedEpistemicStore._jsonable(item) for key, item in value.items()}
        if isinstance(value, (tuple, list, set, frozenset)):
            return [AcceptedEpistemicStore._jsonable(item) for item in value]
        return value

    def read(self, project_id: str):
        return self.backend.read(self.NAMESPACE, project_id, self.RESOURCE_ID)

    def accept(self, actor_or_session, model: SharedEpistemicModel, *, expected_version: int | None, event_id: str):
        self._authorize(actor_or_session, model.project_id)
        if not event_id:
            raise EpistemicError("event_id required")
        model_payload = self._jsonable(model)
        digest = _digest(model_payload)
        current = self.read(model.project_id)
        if current is None:
            if expected_version not in (None, 0):
                raise StaleModelRevision("expected version mismatch")
            return self.backend.create(self.NAMESPACE, model.project_id, self.RESOURCE_ID, {"generation": model.generation, "model": model_payload, "event_digests": {event_id: digest}, "authority": False})
        if expected_version != current.version:
            raise StaleModelRevision("stale writer rejected")
        seen = dict(current.payload.get("event_digests", {}))
        if event_id in seen:
            if seen[event_id] != digest:
                raise EpistemicError("event id collision")
            return "IDEMPOTENT"
        if model.generation <= int(current.payload.get("generation", -1)):
            raise StaleModelRevision("model generation must increase")
        seen[event_id] = digest
        payload = {"generation": model.generation, "model": model_payload, "event_digests": seen, "authority": False}
        try:
            return self.backend.compare_and_set(self.NAMESPACE, model.project_id, self.RESOURCE_ID, expected_version=expected_version, payload=payload)
        except Exception as exc:
            if exc.__class__.__name__ == "StaleVersion":
                raise StaleModelRevision("durable CAS rejected stale writer") from exc
            raise
