from dataclasses import dataclass
from datetime import datetime, timezone
from math import floor
from typing import Iterable, Optional

DEFAULT_RESERVE_FRACTION = 0.20
RESOURCE_KINDS = ("COMMITS", "UPLOADS", "BYTES", "ARTIFACTS", "API_WRITES")
LIMIT_SOURCES = ("EXPLICIT_CONFIG", "PROVIDER_OBSERVED", "ERROR_DERIVED", "UNKNOWN")
CAPACITY_STATES = ("GREEN", "AMBER", "PRESERVE", "RESERVE_ONLY", "EXHAUSTED", "UNKNOWN")
WRITE_CLASSES = ("ESSENTIAL_CANONICAL", "COALESCED_CHECKPOINT", "DISCRETIONARY")
HIGH_LEVEL_NEEDS = (
    "REVIEW_REQUIRED", "PRIMARY_DECISION", "RELEASE_PENDING",
    "CAPACITY_PRESSURE", "BLOCKED"
)

_STATE_RANK = {
    "GREEN": 0,
    "AMBER": 1,
    "PRESERVE": 2,
    "RESERVE_ONLY": 3,
    "EXHAUSTED": 4,
    "UNKNOWN": 5,
}


def _parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("UTC timestamp must be a non-empty string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("UTC timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class CapacityResource:
    resource_kind: str
    hard_limit: Optional[int]
    used: Optional[int]
    source: str = "UNKNOWN"
    reserve_fraction: float = DEFAULT_RESERVE_FRACTION
    measurement_window: Optional[str] = None
    reset_at_utc: Optional[str] = None

    def __post_init__(self):
        if self.resource_kind not in RESOURCE_KINDS:
            raise ValueError(f"Unsupported capacity resource: {self.resource_kind!r}")
        if self.source not in LIMIT_SOURCES:
            raise ValueError(f"Unsupported limit source: {self.source!r}")
        if not 0 < self.reserve_fraction < 1:
            raise ValueError("reserve_fraction must be between 0 and 1")
        if self.hard_limit is not None and self.hard_limit <= 0:
            raise ValueError("hard_limit must be positive when known")
        if self.used is not None and self.used < 0:
            raise ValueError("used cannot be negative")
        if self.reset_at_utc is not None:
            _parse_utc(self.reset_at_utc)

    @property
    def safe_ceiling(self) -> Optional[int]:
        if self.hard_limit is None:
            return None
        return max(0, floor(self.hard_limit * (1 - self.reserve_fraction)))

    @property
    def remaining_safe_budget(self) -> Optional[int]:
        if self.safe_ceiling is None or self.used is None:
            return None
        return max(0, self.safe_ceiling - self.used)

    @property
    def utilization_fraction(self) -> Optional[float]:
        if self.hard_limit is None or self.used is None:
            return None
        return self.used / self.hard_limit

    @property
    def state(self) -> str:
        if self.hard_limit is None or self.used is None:
            return "UNKNOWN"
        if self.used >= self.hard_limit:
            return "EXHAUSTED"
        if self.used >= self.safe_ceiling:
            return "RESERVE_ONLY"
        ratio = self.utilization_fraction
        if ratio >= 0.75:
            return "PRESERVE"
        if ratio >= 0.60:
            return "AMBER"
        return "GREEN"

    def to_signal_dict(self) -> dict:
        return {
            "resource_kind": self.resource_kind,
            "hard_limit": self.hard_limit,
            "used": self.used,
            "source": self.source,
            "reserve_fraction": self.reserve_fraction,
            "safe_ceiling": self.safe_ceiling,
            "remaining_safe_budget": self.remaining_safe_budget,
            "state": self.state,
            "measurement_window": self.measurement_window,
            "reset_at_utc": self.reset_at_utc,
        }


@dataclass(frozen=True)
class WriteDecision:
    allowed: bool
    reason: str
    capacity_state: str
    remaining_safe_budget: Optional[int]


def evaluate_write(
    resource: CapacityResource,
    write_class: str,
    units: int = 1,
    *,
    content_digest: Optional[str] = None,
    last_persisted_digest: Optional[str] = None,
) -> WriteDecision:
    if write_class not in WRITE_CLASSES:
        raise ValueError(f"Unsupported write class: {write_class!r}")
    if units <= 0:
        raise ValueError("units must be positive")
    if content_digest and last_persisted_digest and content_digest == last_persisted_digest:
        return WriteDecision(False, "UNCHANGED_CONTENT", resource.state, resource.remaining_safe_budget)

    state = resource.state
    projected_used = None if resource.used is None else resource.used + units

    if state == "EXHAUSTED":
        return WriteDecision(False, "HARD_LIMIT_EXHAUSTED", state, resource.remaining_safe_budget)

    if write_class == "ESSENTIAL_CANONICAL":
        if resource.hard_limit is not None and projected_used is not None and projected_used > resource.hard_limit:
            return WriteDecision(False, "WOULD_EXCEED_HARD_LIMIT", state, resource.remaining_safe_budget)
        return WriteDecision(True, "ESSENTIAL_CANONICAL_ALLOWED", state, resource.remaining_safe_budget)

    if state == "UNKNOWN":
        return WriteDecision(False, "UNKNOWN_CAPACITY_DEFERS_NONESSENTIAL_WRITE", state, None)

    if state == "RESERVE_ONLY":
        return WriteDecision(False, "PRESERVE_20_PERCENT_RESERVE", state, resource.remaining_safe_budget)

    if state == "PRESERVE" and write_class == "DISCRETIONARY":
        return WriteDecision(False, "PRESERVE_MODE_REQUIRES_COALESCING", state, resource.remaining_safe_budget)

    if resource.safe_ceiling is not None and projected_used is not None and projected_used > resource.safe_ceiling:
        return WriteDecision(False, "WOULD_CONSUME_RESERVED_CAPACITY", state, resource.remaining_safe_budget)

    return WriteDecision(True, "WITHIN_SAFE_WRITE_BUDGET", state, resource.remaining_safe_budget)


def overall_state(resources: Iterable[CapacityResource]) -> str:
    items = list(resources)
    if not items:
        return "UNKNOWN"
    states = [item.state for item in items]
    if "UNKNOWN" in states:
        return "UNKNOWN"
    return max(states, key=lambda value: _STATE_RANK[value])


def build_capacity_signal(
    *,
    project_id: str,
    repository_identity: str,
    observed_revision: str,
    measured_at_utc: str,
    resources: Iterable[CapacityResource],
    high_level_needs: Iterable[str] = (),
    pending_writes: Optional[dict] = None,
) -> dict:
    if not project_id or not repository_identity or not observed_revision:
        raise ValueError("project_id, repository_identity, and observed_revision are required")
    _parse_utc(measured_at_utc)
    resource_list = list(resources)
    state = overall_state(resource_list)
    needs = sorted(set(high_level_needs))
    invalid = [need for need in needs if need not in HIGH_LEVEL_NEEDS]
    if invalid:
        raise ValueError(f"Unsupported high-level needs: {invalid}")
    pending = dict(pending_writes or {})
    for key in WRITE_CLASSES:
        value = pending.get(key, 0)
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"pending write count for {key} must be a non-negative integer")
        pending[key] = value

    return {
        "schema": "org-agent-mesh/capacity-signal/v1",
        "project_id": project_id,
        "repository_identity": repository_identity,
        "observed_revision": observed_revision,
        "measured_at_utc": measured_at_utc,
        "overall_state": state,
        "resources": [item.to_signal_dict() for item in resource_list],
        "high_level_needs": needs,
        "pending_writes": pending,
        "batching_recommended": state in {"AMBER", "PRESERVE", "RESERVE_ONLY", "UNKNOWN"},
        "discretionary_writes_blocked": state in {"PRESERVE", "RESERVE_ONLY", "EXHAUSTED", "UNKNOWN"},
        "essential_writes_blocked": state == "EXHAUSTED",
    }


def signal_materially_changed(previous: Optional[dict], current: dict) -> bool:
    if previous is None:
        return True
    keys = (
        "overall_state",
        "high_level_needs",
        "batching_recommended",
        "discretionary_writes_blocked",
        "essential_writes_blocked",
    )
    if any(previous.get(key) != current.get(key) for key in keys):
        return True
    previous_resources = {
        item.get("resource_kind"): (item.get("state"), item.get("safe_ceiling"))
        for item in previous.get("resources", [])
    }
    current_resources = {
        item.get("resource_kind"): (item.get("state"), item.get("safe_ceiling"))
        for item in current.get("resources", [])
    }
    return previous_resources != current_resources


def signal_is_stale(measured_at_utc: str, now_utc: str, *, max_age_seconds: int) -> bool:
    if max_age_seconds <= 0:
        raise ValueError("max_age_seconds must be positive")
    measured = _parse_utc(measured_at_utc)
    now = _parse_utc(now_utc)
    return (now - measured).total_seconds() > max_age_seconds


def aggregate_capacity_signals(signals: Iterable[dict]) -> dict:
    latest = {}
    for signal in signals:
        project_id = signal.get("project_id")
        if not project_id:
            raise ValueError("capacity signal missing project_id")
        current = latest.get(project_id)
        if current is None or _parse_utc(signal["measured_at_utc"]) > _parse_utc(current["measured_at_utc"]):
            latest[project_id] = signal

    state_counts = {state: 0 for state in CAPACITY_STATES}
    need_counts = {need: 0 for need in HIGH_LEVEL_NEEDS}
    pressure_projects = []
    primary_decisions = []
    for project_id, signal in sorted(latest.items()):
        state = signal.get("overall_state", "UNKNOWN")
        state_counts[state if state in state_counts else "UNKNOWN"] += 1
        for need in signal.get("high_level_needs", []):
            if need in need_counts:
                need_counts[need] += 1
        if state in {"PRESERVE", "RESERVE_ONLY", "EXHAUSTED", "UNKNOWN"}:
            pressure_projects.append({"project_id": project_id, "state": state})
        if "PRIMARY_DECISION" in signal.get("high_level_needs", []):
            primary_decisions.append(project_id)

    return {
        "schema": "org-agent-mesh/capacity-aggregate/v1",
        "project_count": len(latest),
        "state_counts": state_counts,
        "high_level_need_counts": need_counts,
        "capacity_pressure_projects": pressure_projects,
        "projects_requiring_primary_decision": primary_decisions,
    }
