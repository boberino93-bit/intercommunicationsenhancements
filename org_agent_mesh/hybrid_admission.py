"""Shadow-only hardened hybrid admission primitives.

This module allocates *organizational placement* only. It never creates project
or mutation authority. Protected effects remain governed by the existing
MUTATION_AUTHORIZATION_POLICY, reliability-kernel ownership/fencing, and
ConsequenceGateway.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import math
from typing import Any, Iterable, Mapping, Sequence

from .project_work_control import ProjectWorkDecision


LAUNCH_SCHEMA_V2 = "org-agent-mesh/hybrid-launch-context/v2"
FRONTIER_SCHEMA_V2 = "org-agent-mesh/priority-frontier/v2"
TARGET_ADMISSION_SECONDS = 30.0
NORMAL_MAX_ADMISSION_SECONDS = 45.0


class HybridAdmissionError(ValueError):
    pass


class LaunchMode(str, Enum):
    ROLE_BOUND = "ROLE_BOUND"
    PROJECT_CAPACITY = "PROJECT_CAPACITY"
    PORTFOLIO_CAPACITY = "PORTFOLIO_CAPACITY"


class AdmissionDisposition(str, Enum):
    ADMITTED = "ADMITTED"
    ADMISSION_BLOCKED = "ADMISSION_BLOCKED"
    NO_MATERIAL_WORK = "NO_MATERIAL_WORK"
    READ_ONLY_VALIDATION_AVAILABLE = "READ_ONLY_VALIDATION_AVAILABLE"


class FailureCode(str, Enum):
    LAUNCH_CONTEXT_INVALID = "LAUNCH_CONTEXT_INVALID"
    LAUNCH_MODE_UNKNOWN = "LAUNCH_MODE_UNKNOWN"
    LAUNCH_REPLAY_DETECTED = "LAUNCH_REPLAY_DETECTED"
    FRONTIER_STALE = "FRONTIER_STALE"
    FRONTIER_SOURCE_MISMATCH = "FRONTIER_SOURCE_MISMATCH"
    DIGEST_PROVENANCE_INVALID = "DIGEST_PROVENANCE_INVALID"
    PROJECT_IDENTITY_CONFLICT = "PROJECT_IDENTITY_CONFLICT"
    PROJECT_HOLD_ACTIVE = "PROJECT_HOLD_ACTIVE"
    ROLE_ADMISSION_DENIED = "ROLE_ADMISSION_DENIED"
    CAPABILITY_MISMATCH = "CAPABILITY_MISMATCH"
    CLAIM_CONFLICT = "CLAIM_CONFLICT"
    AUTHORIZATION_REQUIRED = "AUTHORIZATION_REQUIRED"
    CROSS_PROJECT_SCOPE_VIOLATION = "CROSS_PROJECT_SCOPE_VIOLATION"
    NO_MATERIAL_WORK = "NO_MATERIAL_WORK"
    ADMISSION_SLA_EXCEEDED = "ADMISSION_SLA_EXCEEDED"


_ALLOWED_PROVENANCE = frozenset({"DERIVED", "ASSERTED", "HUMAN_SET", "POLICY_SET", "INCOMPLETE"})
_GENERIC_SELF_ADMISSIBLE_ROLES = frozenset({"research", "manager"})


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise HybridAdmissionError("timezone-aware datetime required")
    return value.astimezone(timezone.utc)


def _parse_time(value: str | datetime, field: str) -> datetime:
    if isinstance(value, datetime):
        return _utc(value)
    if not isinstance(value, str) or not value.strip():
        raise HybridAdmissionError(f"{field} is required")
    text = value.strip().replace("Z", "+00:00")
    try:
        return _utc(datetime.fromisoformat(text))
    except ValueError as exc:
        raise HybridAdmissionError(f"invalid {field}") from exc


def _finite_unit(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise HybridAdmissionError(f"{field} must be numeric")
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise HybridAdmissionError(f"{field} must be finite and between 0 and 1")
    return number


def _canonical(value: Any) -> bytes:
    def normalize(item: Any) -> Any:
        if isinstance(item, Enum):
            return item.value
        if isinstance(item, datetime):
            return _utc(item).isoformat().replace("+00:00", "Z")
        if hasattr(item, "__dataclass_fields__"):
            return {k: normalize(v) for k, v in asdict(item).items()}
        if isinstance(item, Mapping):
            return {str(k): normalize(item[k]) for k in sorted(item)}
        if isinstance(item, (tuple, list)):
            return [normalize(v) for v in item]
        return item

    return json.dumps(normalize(value), sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def launch_fingerprint(payload: Mapping[str, Any]) -> str:
    unsigned = {k: payload[k] for k in payload if k != "context_fingerprint"}
    return canonical_digest(unsigned)


def validate_launch_context_v2(
    payload: Mapping[str, Any], *, now: datetime, consumed_occurrence_ids: Iterable[str] = ()
) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise HybridAdmissionError(FailureCode.LAUNCH_CONTEXT_INVALID.value)
    if payload.get("schema") != LAUNCH_SCHEMA_V2:
        raise HybridAdmissionError(FailureCode.LAUNCH_CONTEXT_INVALID.value)
    try:
        mode = LaunchMode(str(payload.get("mode", "")))
    except ValueError as exc:
        raise HybridAdmissionError(FailureCode.LAUNCH_MODE_UNKNOWN.value) from exc

    required = ("occurrence_id", "route_id", "routing_contract_version", "registry_revision", "issued_at", "expires_at")
    if any(not str(payload.get(name, "")).strip() for name in required):
        raise HybridAdmissionError(FailureCode.LAUNCH_CONTEXT_INVALID.value)
    occurrence_id = str(payload["occurrence_id"]).strip()
    if occurrence_id in set(consumed_occurrence_ids):
        raise HybridAdmissionError(FailureCode.LAUNCH_REPLAY_DETECTED.value)

    issued = _parse_time(payload["issued_at"], "issued_at")
    expires = _parse_time(payload["expires_at"], "expires_at")
    current = _utc(now)
    if expires <= issued or current < issued or current >= expires:
        raise HybridAdmissionError(FailureCode.LAUNCH_CONTEXT_INVALID.value)

    project_id = payload.get("project_id")
    role_id = payload.get("role_id")
    project_present = isinstance(project_id, str) and bool(project_id.strip())
    role_present = isinstance(role_id, str) and bool(role_id.strip())

    if mode is LaunchMode.ROLE_BOUND and not (project_present and role_present):
        raise HybridAdmissionError(FailureCode.LAUNCH_CONTEXT_INVALID.value)
    if mode is LaunchMode.PROJECT_CAPACITY and (not project_present or role_present):
        raise HybridAdmissionError(FailureCode.LAUNCH_CONTEXT_INVALID.value)
    if mode is LaunchMode.PORTFOLIO_CAPACITY and (project_present or role_present):
        raise HybridAdmissionError(FailureCode.LAUNCH_CONTEXT_INVALID.value)

    claimed = payload.get("context_fingerprint")
    if not isinstance(claimed, str) or len(claimed) != 64 or claimed != launch_fingerprint(payload):
        raise HybridAdmissionError(FailureCode.LAUNCH_CONTEXT_INVALID.value)
    return dict(payload)


@dataclass(frozen=True)
class DemandDigest:
    project_id: str
    project_state: str
    source_revision: str
    registry_revision: str
    global_run_id: str
    generated_at: datetime
    expires_at: datetime
    priority_tier: int
    priority_provenance: str
    provenance_ref: str
    impact: float
    information_gain: float
    evidence_gap: float
    contradiction: float
    duplicate_risk: float
    manager_backpressure: float
    primary_backpressure: float
    candidate_roles: tuple[str, ...]
    candidate_lanes: tuple[str, ...]
    human_priority_authenticated: bool = False
    privileged_priority_verified: bool = False

    def validate(self, *, now: datetime, expected_registry_revision: str, expected_global_run_id: str) -> None:
        if not self.project_id or self.project_state not in {"ACTIVE", "HOLD", "PAUSED", "STOP"}:
            raise HybridAdmissionError(FailureCode.DIGEST_PROVENANCE_INVALID.value)
        if not self.source_revision or not self.provenance_ref:
            raise HybridAdmissionError(FailureCode.DIGEST_PROVENANCE_INVALID.value)
        if self.registry_revision != expected_registry_revision or self.global_run_id != expected_global_run_id:
            raise HybridAdmissionError(FailureCode.FRONTIER_SOURCE_MISMATCH.value)
        generated = _utc(self.generated_at)
        expires = _utc(self.expires_at)
        current = _utc(now)
        if expires <= generated or current < generated or current >= expires:
            raise HybridAdmissionError(FailureCode.FRONTIER_STALE.value)
        if isinstance(self.priority_tier, bool) or not isinstance(self.priority_tier, int) or not 0 <= self.priority_tier <= 3:
            raise HybridAdmissionError(FailureCode.DIGEST_PROVENANCE_INVALID.value)
        provenance = self.priority_provenance.strip().upper()
        if provenance not in _ALLOWED_PROVENANCE:
            raise HybridAdmissionError(FailureCode.DIGEST_PROVENANCE_INVALID.value)
        if provenance == "HUMAN_SET" and not self.human_priority_authenticated:
            raise HybridAdmissionError(FailureCode.DIGEST_PROVENANCE_INVALID.value)
        if self.priority_tier == 0 and not self.privileged_priority_verified:
            raise HybridAdmissionError(FailureCode.DIGEST_PROVENANCE_INVALID.value)
        for field in ("impact", "information_gain", "evidence_gap", "contradiction", "duplicate_risk", "manager_backpressure", "primary_backpressure"):
            _finite_unit(getattr(self, field), field)
        if len(set(self.candidate_lanes)) != len(self.candidate_lanes) or any(not lane.strip() for lane in self.candidate_lanes):
            raise HybridAdmissionError(FailureCode.DIGEST_PROVENANCE_INVALID.value)
        normalized_roles = tuple(role.strip().lower() for role in self.candidate_roles)
        if any(role not in _GENERIC_SELF_ADMISSIBLE_ROLES for role in normalized_roles):
            raise HybridAdmissionError(FailureCode.ROLE_ADMISSION_DENIED.value)


@dataclass(frozen=True)
class FrontierEntry:
    project_id: str
    source_revision: str
    priority_tier: int
    priority_provenance: str
    impact: float
    information_gain: float
    evidence_gap: float
    contradiction: float
    duplicate_risk: float
    manager_backpressure: float
    primary_backpressure: float
    candidate_roles: tuple[str, ...]
    candidate_lanes: tuple[str, ...]
    digest_hash: str


@dataclass(frozen=True)
class PriorityFrontier:
    schema: str
    snapshot_id: str
    registry_revision: str
    global_run_id: str
    generated_at: datetime
    expires_at: datetime
    entries: tuple[FrontierEntry, ...]
    input_digest: str
    authority_conveyed: bool = False


def build_priority_frontier(
    digests: Sequence[DemandDigest], *, now: datetime, registry_revision: str, global_run_id: str, ttl_seconds: int = 120
) -> PriorityFrontier:
    if ttl_seconds <= 0:
        raise HybridAdmissionError("frontier ttl must be positive")
    current = _utc(now)
    entries: list[FrontierEntry] = []
    for digest in digests:
        digest.validate(now=current, expected_registry_revision=registry_revision, expected_global_run_id=global_run_id)
        if digest.project_state != "ACTIVE":
            continue
        if digest.manager_backpressure >= 1.0 or digest.primary_backpressure >= 1.0:
            continue
        entries.append(FrontierEntry(
            project_id=digest.project_id,
            source_revision=digest.source_revision,
            priority_tier=digest.priority_tier,
            priority_provenance=digest.priority_provenance.strip().upper(),
            impact=digest.impact,
            information_gain=digest.information_gain,
            evidence_gap=digest.evidence_gap,
            contradiction=digest.contradiction,
            duplicate_risk=digest.duplicate_risk,
            manager_backpressure=digest.manager_backpressure,
            primary_backpressure=digest.primary_backpressure,
            candidate_roles=tuple(role.strip().lower() for role in digest.candidate_roles),
            candidate_lanes=tuple(digest.candidate_lanes),
            digest_hash=canonical_digest(digest),
        ))
    entries.sort(key=lambda e: (
        e.priority_tier,
        -e.impact,
        -e.information_gain,
        -e.evidence_gap,
        -e.contradiction,
        e.duplicate_risk,
        e.manager_backpressure,
        e.primary_backpressure,
        e.project_id,
    ))
    input_digest = canonical_digest({"registry_revision": registry_revision, "global_run_id": global_run_id, "entries": entries})
    snapshot_id = f"pf-{input_digest[:20]}"
    from datetime import timedelta
    return PriorityFrontier(
        schema=FRONTIER_SCHEMA_V2,
        snapshot_id=snapshot_id,
        registry_revision=registry_revision,
        global_run_id=global_run_id,
        generated_at=current,
        expires_at=current + timedelta(seconds=ttl_seconds),
        entries=tuple(entries),
        input_digest=input_digest,
        authority_conveyed=False,
    )


def select_frontier_entry(frontier: PriorityFrontier, *, occurrence_id: str, top_k: int = 3) -> FrontierEntry | None:
    if frontier.authority_conveyed:
        raise HybridAdmissionError("frontier may not convey authority")
    if not occurrence_id.strip() or top_k <= 0:
        raise HybridAdmissionError("occurrence_id and positive top_k required")
    if not frontier.entries:
        return None
    best_tier = frontier.entries[0].priority_tier
    pool = [entry for entry in frontier.entries if entry.priority_tier == best_tier][:top_k]
    seed = canonical_digest({"occurrence_id": occurrence_id, "snapshot_id": frontier.snapshot_id})
    return pool[int(seed[:8], 16) % len(pool)]


def _registry_project(registry: Mapping[str, Any], project_id: str) -> Mapping[str, Any]:
    projects = registry.get("projects")
    if isinstance(projects, Mapping):
        entry = projects.get(project_id)
        if isinstance(entry, Mapping):
            return entry
    if isinstance(projects, Sequence) and not isinstance(projects, (str, bytes)):
        for entry in projects:
            if isinstance(entry, Mapping) and entry.get("project_id") == project_id:
                return entry
    raise HybridAdmissionError(FailureCode.PROJECT_IDENTITY_CONFLICT.value)


def resolve_self_admissible_roles(registry: Mapping[str, Any], project_id: str) -> frozenset[str]:
    entry = _registry_project(registry, project_id)
    roles = entry.get("self_admissible_roles", ())
    if not isinstance(roles, Sequence) or isinstance(roles, (str, bytes)):
        raise HybridAdmissionError(FailureCode.ROLE_ADMISSION_DENIED.value)
    normalized = frozenset(str(role).strip().lower() for role in roles if str(role).strip())
    if not normalized.issubset(_GENERIC_SELF_ADMISSIBLE_ROLES):
        raise HybridAdmissionError(FailureCode.ROLE_ADMISSION_DENIED.value)
    return normalized


@dataclass(frozen=True)
class AdmissionOutcome:
    disposition: AdmissionDisposition
    project_id: str | None
    role_id: str | None
    lane_id: str | None
    failure_code: str | None
    evidence_consulted: tuple[str, ...]
    source_revision: str | None
    registry_revision: str
    frontier_snapshot_id: str | None
    elapsed_seconds: float
    sla_target_met: bool
    sla_normal_max_exceeded: bool
    authority_conveyed: bool
    mutation_authority: bool
    precondition_digest: str | None


def evaluate_generic_admission(
    *,
    project_id: str,
    requested_role: str,
    lane_id: str,
    source_revision: str,
    expected_source_revision: str,
    registry: Mapping[str, Any],
    registry_revision: str,
    project_work_decision: ProjectWorkDecision,
    frontier_snapshot_id: str | None,
    started_at: datetime,
    now: datetime,
    evidence_consulted: Iterable[str] = (),
) -> AdmissionOutcome:
    started = _utc(started_at)
    current = _utc(now)
    elapsed = max(0.0, (current - started).total_seconds())

    def blocked(code: FailureCode) -> AdmissionOutcome:
        return AdmissionOutcome(
            AdmissionDisposition.ADMISSION_BLOCKED,
            project_id,
            None,
            None,
            code.value,
            tuple(evidence_consulted),
            source_revision or None,
            registry_revision,
            frontier_snapshot_id,
            elapsed,
            elapsed <= TARGET_ADMISSION_SECONDS,
            elapsed > NORMAL_MAX_ADMISSION_SECONDS,
            False,
            False,
            None,
        )

    if elapsed > NORMAL_MAX_ADMISSION_SECONDS:
        return blocked(FailureCode.ADMISSION_SLA_EXCEEDED)
    if project_work_decision.project_id != project_id or not project_work_decision.allow_new_work:
        return blocked(FailureCode.PROJECT_HOLD_ACTIVE)
    if not source_revision or source_revision != expected_source_revision:
        return blocked(FailureCode.FRONTIER_SOURCE_MISMATCH)

    role = requested_role.strip().lower()
    if role not in _GENERIC_SELF_ADMISSIBLE_ROLES:
        return blocked(FailureCode.ROLE_ADMISSION_DENIED)
    if role not in resolve_self_admissible_roles(registry, project_id):
        return blocked(FailureCode.ROLE_ADMISSION_DENIED)
    if not lane_id.strip():
        return blocked(FailureCode.NO_MATERIAL_WORK)

    binding = {
        "project_id": project_id,
        "role_id": role,
        "lane_id": lane_id.strip(),
        "source_revision": source_revision,
        "registry_revision": registry_revision,
        "frontier_snapshot_id": frontier_snapshot_id,
        "authority_conveyed": False,
        "mutation_authority": False,
    }
    return AdmissionOutcome(
        AdmissionDisposition.ADMITTED,
        project_id,
        role,
        lane_id.strip(),
        None,
        tuple(evidence_consulted),
        source_revision,
        registry_revision,
        frontier_snapshot_id,
        elapsed,
        elapsed <= TARGET_ADMISSION_SECONDS,
        elapsed > NORMAL_MAX_ADMISSION_SECONDS,
        False,
        False,
        canonical_digest(binding),
    )


def consequence_gateway_precondition(outcome: AdmissionOutcome) -> str:
    """Return non-authoritative precondition evidence for ConsequenceGateway.

    This function intentionally does not authorize or commit any effect.
    """
    if outcome.disposition is not AdmissionDisposition.ADMITTED or not outcome.precondition_digest:
        raise HybridAdmissionError(FailureCode.AUTHORIZATION_REQUIRED.value)
    if outcome.authority_conveyed or outcome.mutation_authority:
        raise HybridAdmissionError("hybrid admission may not convey authority")
    return outcome.precondition_digest
