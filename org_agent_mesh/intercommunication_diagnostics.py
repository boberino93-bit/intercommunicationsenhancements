from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Iterable

from .reliability_v18_core import digest, ensure_aware, iso, parse_iso


class VisibilityError(ValueError):
    pass


class PresenceState(str, Enum):
    STARTING = "STARTING"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    BLOCKED = "BLOCKED"
    RECOVERING = "RECOVERING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    IDLE = "IDLE"


_TERMINAL = {PresenceState.COMPLETE, PresenceState.FAILED, PresenceState.IDLE}


@dataclass(frozen=True)
class HeartbeatPolicy:
    nominal_seconds: int = 45
    max_normal_seconds: int = 60
    coalesce_seconds: int = 15
    stale_seconds: int = 60

    def __post_init__(self):
        if not 30 <= self.nominal_seconds <= 60:
            raise VisibilityError("nominal heartbeat must be 30..60 seconds")
        if self.max_normal_seconds < self.nominal_seconds or self.max_normal_seconds > 60:
            raise VisibilityError("max normal heartbeat must be nominal..60 seconds")
        if not 0 <= self.coalesce_seconds < self.nominal_seconds:
            raise VisibilityError("coalesce interval invalid")
        if self.stale_seconds < self.max_normal_seconds:
            raise VisibilityError("stale threshold must be at least the normal heartbeat bound")


@dataclass(frozen=True)
class HeartbeatObservation:
    frame_id: str
    project_id: str
    agent_id: str
    agent_instance_id: str
    task_semantic_id: str
    sequence: int
    observed_at_utc: str
    state: PresenceState
    progress_digest: str
    material_delta_digest: str
    ownership_epoch: int
    fence_token: str
    run_id: str = ""
    role: str = ""
    generation_id: str = ""
    claim_id: str = ""
    lease_id: str = ""
    policy_identity: str = ""
    execution_phase: str = ""
    last_completed_milestone: str = ""
    blocked_or_waiting_on: str = ""
    next_intended_action: str = ""

    def __post_init__(self):
        if not all((self.frame_id, self.project_id, self.agent_id, self.agent_instance_id, self.task_semantic_id, self.fence_token)):
            raise VisibilityError("heartbeat identity field missing")
        if self.sequence < 0 or self.ownership_epoch < 0:
            raise VisibilityError("negative sequence/ownership epoch")
        parse_iso(self.observed_at_utc)


@dataclass(frozen=True)
class EmissionDecision:
    ephemeral_emit: bool
    durable_emit: bool
    reason: str
    authority_changed: bool = False


class VisibilityCoordinator:
    """Coalesces liveness while persisting material deltas.

    This component never grants ownership or authority. Ownership/fence fields are
    observations used to detect disagreement, not mutation credentials.
    """

    def __init__(self, policy: HeartbeatPolicy | None = None):
        self.policy = policy or HeartbeatPolicy()
        self._last: dict[tuple[str, str], HeartbeatObservation] = {}
        self._metrics = {
            "observations": 0,
            "ephemeral_emits": 0,
            "durable_emits": 0,
            "sequence_rejections": 0,
            "ownership_conflicts_observed": 0,
            "material_transitions": 0,
        }

    def record(self, frame: HeartbeatObservation) -> EmissionDecision:
        key = (frame.project_id, frame.agent_instance_id)
        prior = self._last.get(key)
        self._metrics["observations"] += 1
        if prior is not None:
            if frame.sequence <= prior.sequence:
                self._metrics["sequence_rejections"] += 1
                raise VisibilityError("heartbeat sequence must increase")
            if parse_iso(frame.observed_at_utc) < parse_iso(prior.observed_at_utc):
                raise VisibilityError("heartbeat time moved backwards")

        material = prior is None or frame.material_delta_digest != prior.material_delta_digest
        state_changed = prior is None or frame.state != prior.state
        terminal_transition = prior is not None and frame.state in _TERMINAL and prior.state != frame.state
        ownership_conflict = bool(
            prior is not None
            and frame.ownership_epoch == prior.ownership_epoch
            and frame.fence_token != prior.fence_token
        )
        if ownership_conflict:
            self._metrics["ownership_conflicts_observed"] += 1

        if prior is None:
            ephemeral = True
            reason = "FIRST_STATUS"
        else:
            age = (parse_iso(frame.observed_at_utc) - parse_iso(prior.observed_at_utc)).total_seconds()
            ephemeral = material or state_changed or age >= self.policy.nominal_seconds
            reason = "MATERIAL_DELTA" if material else "STATE_CHANGE" if state_changed else "CADENCE" if ephemeral else "COALESCED"

        durable_state_transition = state_changed and frame.state in {
            PresenceState.DEGRADED, PresenceState.BLOCKED, PresenceState.RECOVERING,
            PresenceState.COMPLETE, PresenceState.FAILED, PresenceState.IDLE,
        }
        durable = material or terminal_transition or durable_state_transition or ownership_conflict
        if durable:
            self._metrics["material_transitions"] += 1
        self._last[key] = frame
        self._metrics["ephemeral_emits"] += int(ephemeral)
        self._metrics["durable_emits"] += int(durable)
        return EmissionDecision(ephemeral, durable, reason, authority_changed=False)

    def latest(self, project_id: str | None = None) -> tuple[HeartbeatObservation, ...]:
        rows = self._last.values()
        if project_id is not None:
            rows = [r for r in rows if r.project_id == project_id]
        return tuple(sorted(rows, key=lambda r: (r.project_id, r.task_semantic_id, r.agent_instance_id)))

    def metrics(self) -> dict:
        total = max(1, self._metrics["observations"])
        return {
            **self._metrics,
            "durable_write_amplification": self._metrics["durable_emits"] / max(1, self._metrics["material_transitions"]),
            "heartbeat_write_amplification": self._metrics["durable_emits"] / total,
            "ephemeral_emit_ratio": self._metrics["ephemeral_emits"] / total,
        }


@dataclass(frozen=True)
class PeerMatch:
    project_id: str
    task_semantic_id: str
    agent_instance_id: str
    state: str
    age_seconds: float
    ownership_epoch: int
    fence_token: str
    authoritative: bool = False


class PeerDiscoveryIndex:
    """Read-only overlap discovery built from observed heartbeat state."""

    def __init__(self, coordinator: VisibilityCoordinator):
        self.coordinator = coordinator

    def discover(self, *, project_id: str, task_semantic_id: str, now: datetime) -> tuple[PeerMatch, ...]:
        now = ensure_aware(now)
        rows = []
        for frame in self.coordinator.latest(project_id):
            if frame.task_semantic_id != task_semantic_id:
                continue
            age = (now - parse_iso(frame.observed_at_utc)).total_seconds()
            if age <= self.coordinator.policy.stale_seconds and frame.state not in _TERMINAL:
                rows.append(PeerMatch(
                    project_id=frame.project_id,
                    task_semantic_id=frame.task_semantic_id,
                    agent_instance_id=frame.agent_instance_id,
                    state=frame.state.value,
                    age_seconds=max(0.0, age),
                    ownership_epoch=frame.ownership_epoch,
                    fence_token=frame.fence_token,
                ))
        return tuple(sorted(rows, key=lambda r: (r.age_seconds, r.agent_instance_id)))


class ReadOnlyObservabilityAggregator:
    """Derived fleet view. It cannot mutate task, lease, policy, or ownership state."""

    def __init__(self, coordinator: VisibilityCoordinator, *, allowed_projects: Iterable[str]):
        self.coordinator = coordinator
        self.allowed_projects = frozenset(allowed_projects)

    def snapshot(self, *, now: datetime) -> dict:
        now = ensure_aware(now)
        projects = {}
        for frame in self.coordinator.latest():
            if frame.project_id not in self.allowed_projects:
                continue
            age = max(0.0, (now - parse_iso(frame.observed_at_utc)).total_seconds())
            row = projects.setdefault(frame.project_id, {"active": 0, "stale": 0, "degraded": 0, "terminal": 0})
            if age > self.coordinator.policy.stale_seconds:
                row["stale"] += 1
            elif frame.state in _TERMINAL:
                row["terminal"] += 1
            else:
                row["active"] += 1
                if frame.state in {PresenceState.DEGRADED, PresenceState.BLOCKED, PresenceState.RECOVERING}:
                    row["degraded"] += 1
        payload = {
            "projects": projects,
            "visibility_metrics": self.coordinator.metrics(),
            "authority": False,
            "may_transfer_ownership": False,
        }
        return {**payload, "snapshot_digest": digest(payload)}
