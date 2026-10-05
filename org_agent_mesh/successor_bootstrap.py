from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Iterable, Mapping, Sequence

from .reliability_v18_core import digest, ensure_aware, parse_iso, verify_signature


class SuccessorBootstrapError(RuntimeError):
    pass


class PriorityProvenance(str, Enum):
    HUMAN_SET = "HUMAN_SET"
    POLICY_SET = "POLICY_SET"
    DERIVED = "DERIVED"
    INCOMPLETE = "INCOMPLETE"


class EvidenceState(str, Enum):
    OBSERVED = "OBSERVED"
    SUPPORTED = "SUPPORTED"
    INFERRED = "INFERRED"
    HYPOTHESIS = "HYPOTHESIS"
    DISPUTED = "DISPUTED"
    BLOCKED = "BLOCKED"


class LaunchDisposition(str, Enum):
    CREATE = "CREATE"
    ATTACH = "ATTACH"
    RESUME = "RESUME"
    OBSERVE = "OBSERVE"
    REJECT_DUPLICATE = "REJECT_DUPLICATE"


HUMAN_PROJECT_PRIORITY: tuple[str, ...] = (
    "Duo Screen / Duo Open",
    "Intercommunication Enhancements",
    "BenefitFlow",
    "AI Behavioral Control Lab",
    "Samsung Power Bootstrap",
    "Warp Propulsion Lab",
)

GET_STARTED_SEQUENCE: tuple[str, ...] = (
    "ORIENT",
    "HYDRATE_PROJECT_CAPSULE",
    "READ_PRIORITY_FRONTIER_SNAPSHOT",
    "READ_CURRENT_TASK_IDENTITIES_CLAIMS_HEARTBEATS",
    "READ_MATERIAL_FINDINGS_BLOCKERS_CHECKPOINTS",
    "IDENTIFY_HIGHEST_VALUE_APPROPRIATE_UNCLAIMED_LANE",
    "CLASSIFY_DUPLICATION",
    "CLAIM_REGISTER_CANONICAL",
    "PUBLISH_START_STATUS",
    "EXECUTE",
    "PERSIST_MATERIAL_DELTAS",
    "REASSESS_FRONTIER",
    "HANDOFF_CLOSE",
)

INITIAL_DUO_RESEARCH_PROFILE: Mapping[str, int] = {
    "MASTER": 1,
    "MANAGER": 1,
    "RESEARCH": 3,
}

RESUMABLE_LAUNCH_STATES = frozenset({"ACTIVE", "STARTING", "WAITING", "RECOVERING"})


@dataclass(frozen=True)
class PriorityCandidate:
    project: str
    objective: str
    blocker_severity: int = 0
    downstream_unlock: int = 0
    risk_reduction: int = 0
    uncertainty_reduction: int = 0
    information_value: int = 0
    freshness_need: int = 0
    estimated_cost: int = 0
    starvation: int = 0

    @property
    def derived_score(self) -> int:
        return (
            4 * self.blocker_severity
            + 3 * self.downstream_unlock
            + 3 * self.risk_reduction
            + 2 * self.uncertainty_reduction
            + 2 * self.information_value
            + self.freshness_need
            + self.starvation
            - self.estimated_cost
        )


@dataclass(frozen=True)
class PriorityFrontierSnapshot:
    snapshot_id: str
    source_revisions: tuple[str, ...]
    generated_at_utc: str
    expires_at_utc: str
    project_order: tuple[str, ...]
    priority_provenance: str
    project_id: str
    project_priority: int | None
    open_frontier: tuple[str, ...]
    active_task_ids: tuple[str, ...] = ()
    active_claim_ids: tuple[str, ...] = ()
    recent_liveness: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    checkpoints: tuple[str, ...] = ()
    latest_evidence_refs: tuple[str, ...] = ()
    recommended_next_actions: tuple[str, ...] = ()
    authority: bool = False

    def is_fresh(self, now: datetime) -> bool:
        now = ensure_aware(now)
        return parse_iso(self.generated_at_utc) <= now < parse_iso(self.expires_at_utc)

    def require_fresh(self, now: datetime) -> None:
        if not self.is_fresh(now):
            raise SuccessorBootstrapError("PRIORITY_FRONTIER_STALE")


@dataclass(frozen=True)
class StepUpAttestation:
    attestation_id: str
    subject: str
    authority_class: str
    project_id: str
    authentication_strength: str
    action_digest: str
    issued_at_utc: str
    expires_at_utc: str
    nonce: str
    verifier_id: str
    signature: str
    status: str = "VALID"

    def unsigned(self) -> dict:
        raw = asdict(self)
        raw.pop("signature")
        return raw


class StepUpVerifier:
    """Verifies exact-action attestations issued outside model context; cannot mint them."""

    STRONG_AUTH = frozenset({"FIDO2", "WEBAUTHN", "HARDWARE_KEY", "MFA_ROOT_CONSOLE", "GITHUB_AUTHENTICATED_ROOT"})

    def __init__(self, trusted_verifiers: Mapping[str, bytes]):
        self._keys = {name: bytes(key) for name, key in trusted_verifiers.items()}
        self._consumed: set[str] = set()
        self._revoked: set[str] = set()

    def revoke(self, attestation_id: str) -> None:
        self._revoked.add(attestation_id)

    def verify_and_consume(
        self,
        attestation: StepUpAttestation,
        *,
        now: datetime,
        project_id: str,
        action_digest: str,
        required_authority_class: str,
    ) -> str:
        now = ensure_aware(now)
        key = self._keys.get(attestation.verifier_id)
        if key is None or not verify_signature(attestation.unsigned(), attestation.signature, key):
            raise SuccessorBootstrapError("AUTHENTICATION_REQUIRED")
        if attestation.authentication_strength not in self.STRONG_AUTH or attestation.status != "VALID":
            raise SuccessorBootstrapError("AUTHENTICATION_REQUIRED")
        if attestation.attestation_id in self._revoked:
            raise SuccessorBootstrapError("AUTHORITY_NOT_ESTABLISHED")
        if attestation.attestation_id in self._consumed:
            raise SuccessorBootstrapError("AUTHENTICATION_REPLAY")
        if now < parse_iso(attestation.issued_at_utc) or now >= parse_iso(attestation.expires_at_utc):
            raise SuccessorBootstrapError("AUTHENTICATION_EXPIRED")
        if (
            attestation.project_id != project_id
            or attestation.action_digest != action_digest
            or attestation.authority_class != required_authority_class
        ):
            raise SuccessorBootstrapError("AUTHORITY_NOT_ESTABLISHED")
        self._consumed.add(attestation.attestation_id)
        return attestation.subject


def resolve_project_priority(
    project_name: str,
    *,
    human_order: Sequence[str] | None = HUMAN_PROJECT_PRIORITY,
    policy_order: Sequence[str] | None = None,
    derived_candidates: Sequence[PriorityCandidate] = (),
) -> tuple[PriorityProvenance, int | None, tuple[str, ...]]:
    if human_order:
        order = tuple(human_order)
        if project_name in order:
            return PriorityProvenance.HUMAN_SET, order.index(project_name) + 1, order
        return PriorityProvenance.INCOMPLETE, None, order
    if policy_order:
        order = tuple(policy_order)
        if project_name in order:
            return PriorityProvenance.POLICY_SET, order.index(project_name) + 1, order
        return PriorityProvenance.INCOMPLETE, None, order
    if derived_candidates:
        ranked = sorted(derived_candidates, key=lambda c: (-c.derived_score, c.project, c.objective))
        order = tuple(dict.fromkeys(c.project for c in ranked))
        if project_name in order:
            return PriorityProvenance.DERIVED, order.index(project_name) + 1, order
    return PriorityProvenance.INCOMPLETE, None, ()


def semantic_launch_identity(*, project_id: str, objective_class: str, parent_work_id: str | None = None) -> str:
    if not project_id or not objective_class:
        raise SuccessorBootstrapError("INPUT_INVALID")
    return digest({
        "project_id": project_id,
        "objective_class": " ".join(objective_class.casefold().split()),
        "parent_work_id": parent_work_id or "",
    })


@dataclass(frozen=True)
class ResearchLaunchEnvelope:
    project_id: str
    run_id: str
    task_id: str
    semantic_launch_id: str
    role: str
    allowed_capabilities: tuple[str, ...]
    priority_frontier_snapshot_ref: str
    source_boundaries: tuple[str, ...]
    prohibited_sources: tuple[str, ...]
    objective_class: str
    resource_budget: Mapping[str, int]
    verification_expectations: tuple[str, ...]
    checkpoint_location: str
    heartbeat_destination: str
    material_delta_destination: str
    stop_criteria: tuple[str, ...]
    escalation_conditions: tuple[str, ...]
    handoff_contract_ref: str
    policy_versions: tuple[str, ...]
    protocol_versions: tuple[str, ...]

    def validate(self) -> None:
        required = {
            "project_id": self.project_id,
            "run_id": self.run_id,
            "task_id": self.task_id,
            "semantic_launch_id": self.semantic_launch_id,
            "role": self.role,
            "priority_frontier_snapshot_ref": self.priority_frontier_snapshot_ref,
            "objective_class": self.objective_class,
            "checkpoint_location": self.checkpoint_location,
            "heartbeat_destination": self.heartbeat_destination,
            "material_delta_destination": self.material_delta_destination,
            "handoff_contract_ref": self.handoff_contract_ref,
        }
        missing = sorted(name for name, value in required.items() if not value)
        if missing:
            raise SuccessorBootstrapError(f"INPUT_INVALID:{','.join(missing)}")
        expected = semantic_launch_identity(project_id=self.project_id, objective_class=self.objective_class)
        if self.semantic_launch_id != expected:
            raise SuccessorBootstrapError("CONTRACT_VIOLATION:semantic_launch_id")
        if not self.stop_criteria:
            raise SuccessorBootstrapError("CONTRACT_VIOLATION:stop_criteria")
        if not self.allowed_capabilities:
            raise SuccessorBootstrapError("AUTHORITY_NOT_ESTABLISHED:capabilities")


@dataclass(frozen=True)
class ExistingLaunch:
    semantic_launch_id: str
    run_id: str
    state: str
    healthy: bool


def resolve_launch_disposition(envelope: ResearchLaunchEnvelope, existing: Iterable[ExistingLaunch]) -> tuple[LaunchDisposition, str | None]:
    envelope.validate()
    matching = [x for x in existing if x.semantic_launch_id == envelope.semantic_launch_id]
    active = [x for x in matching if x.state in RESUMABLE_LAUNCH_STATES]
    healthy = [x for x in active if x.healthy]
    if healthy:
        chosen = sorted(healthy, key=lambda x: x.run_id)[0]
        return LaunchDisposition.ATTACH, chosen.run_id
    if active:
        chosen = sorted(active, key=lambda x: x.run_id)[0]
        return LaunchDisposition.RESUME, chosen.run_id
    return LaunchDisposition.CREATE, None


@dataclass(frozen=True)
class CapabilityObservation:
    capability: str
    available: bool
    authorized: bool
    project_boundary: str
    evidence_quality: str
    consequential_external_effect: bool


def select_capability_path(observations: Sequence[CapabilityObservation], required: Sequence[str]) -> tuple[str, ...]:
    by_name = {x.capability: x for x in observations}
    selected: list[str] = []
    for capability in required:
        obs = by_name.get(capability)
        if obs is None or not obs.available:
            raise SuccessorBootstrapError(f"DEPENDENCY_UNAVAILABLE:{capability}")
        if not obs.authorized:
            raise SuccessorBootstrapError(f"PERMISSION_DENIED:{capability}")
        selected.append(capability)
    return tuple(selected)


def initial_duo_research_profile(project_name: str, *, first_kickoff: bool) -> Mapping[str, int]:
    if not first_kickoff or project_name != "Duo Screen / Duo Open":
        raise SuccessorBootstrapError("PROFILE_NOT_APPLICABLE")
    return dict(INITIAL_DUO_RESEARCH_PROFILE)
