from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

class HeartbeatError(ValueError):
    pass


def _parse(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception as exc:
        raise HeartbeatError("invalid heartbeat timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise HeartbeatError("heartbeat timestamp must be offset-aware")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class HeartbeatFrame:
    agent_id: str
    session_id: str
    project_id: str
    run_id: str
    role: str
    sequence: int
    sent_at: str
    state: str
    protocol_version: str
    ownership_epoch: int
    fence_digest: str
    persistence_state: str
    computational_budget_state: str
    work_unit: str | None = None
    blocking_condition: str | None = None
    authority_conveyed: bool = False

    def __post_init__(self) -> None:
        for name in ("agent_id", "session_id", "project_id", "run_id", "role", "state", "protocol_version", "fence_digest", "persistence_state", "computational_budget_state"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise HeartbeatError(f"{name} is required")
        if self.sequence < 0 or self.ownership_epoch < 0:
            raise HeartbeatError("sequence and ownership_epoch must be non-negative")
        _parse(self.sent_at)
        if self.authority_conveyed is not False:
            raise HeartbeatError("heartbeat cannot convey authority")


class HeartbeatMonitor:
    def __init__(self, *, future_skew_seconds: int = 30, stale_after_seconds: int = 60) -> None:
        self.future_skew_seconds = future_skew_seconds
        self.stale_after_seconds = stale_after_seconds
        self._last: dict[tuple[str, str, str, str], HeartbeatFrame] = {}

    def observe(self, frame: HeartbeatFrame, *, now: str, expected_ownership_epoch: int | None = None, expected_fence_digest: str | None = None) -> str:
        now_dt = _parse(now)
        sent = _parse(frame.sent_at)
        delta = (sent - now_dt).total_seconds()
        if delta > self.future_skew_seconds:
            raise HeartbeatError("FUTURE_HEARTBEAT_REJECTED")
        age = max(0.0, -delta)
        if age > self.stale_after_seconds:
            raise HeartbeatError("STALE_HEARTBEAT_REJECTED")
        if expected_ownership_epoch is not None and frame.ownership_epoch != expected_ownership_epoch:
            raise HeartbeatError("OWNERSHIP_EPOCH_MISMATCH")
        if expected_fence_digest is not None and frame.fence_digest != expected_fence_digest:
            raise HeartbeatError("FENCE_MISMATCH")
        key = (frame.project_id, frame.run_id, frame.agent_id, frame.session_id)
        previous = self._last.get(key)
        if previous is not None:
            if frame.sequence <= previous.sequence:
                raise HeartbeatError("HEARTBEAT_REPLAY_OR_REORDER")
            if frame.ownership_epoch < previous.ownership_epoch:
                raise HeartbeatError("OWNERSHIP_EPOCH_ROLLBACK")
            if _parse(frame.sent_at) <= _parse(previous.sent_at):
                raise HeartbeatError("HEARTBEAT_TIME_NONMONOTONIC")
        self._last[key] = frame
        return "HEARTBEAT_ACCEPTED"

    def latest(self, *, project_id: str, run_id: str, agent_id: str, session_id: str) -> HeartbeatFrame | None:
        return self._last.get((project_id, run_id, agent_id, session_id))
