from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
import hashlib

from .project_scope import require_project_id, require_resource_id


RETRYABLE_PROVIDER_RESULTS = frozenset({
    "TOO_MANY_REQUESTS",
    "RATE_LIMITED",
    "TEMPORARY_PROVIDER_UNAVAILABLE",
    "TIMEOUT_BEFORE_BOOTSTRAP",
})
TERMINAL_PROVIDER_RESULTS = frozenset({
    "CONTEXT_MISMATCH",
    "IDENTITY_CONFLICT",
    "UNAUTHORIZED_ROLE",
    "INVALID_LAUNCH_CONTEXT",
    "PERMISSION_DENIED",
})


class LaunchAdmissionError(ValueError):
    pass


def _require_aware(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise LaunchAdmissionError("timezone-aware datetime required")
    return value.astimezone(timezone.utc)


def deterministic_launch_offset_seconds(
    project_id: str,
    task_id: str,
    *,
    window_seconds: int = 300,
) -> int:
    project_id = require_project_id(project_id)
    task_id = require_resource_id(task_id, field="task_id")
    if not isinstance(window_seconds, int) or window_seconds <= 0:
        raise LaunchAdmissionError("window_seconds must be a positive integer")
    digest = hashlib.sha256(f"{project_id}\0{task_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % window_seconds


@dataclass(frozen=True)
class LaunchAdmissionPolicy:
    max_inflight: int = 1
    min_start_interval_seconds: int = 30
    base_backoff_seconds: int = 30
    max_backoff_seconds: int = 900
    max_attempts: int = 6
    jitter_percent: int = 25

    def __post_init__(self):
        for name in (
            "max_inflight",
            "min_start_interval_seconds",
            "base_backoff_seconds",
            "max_backoff_seconds",
            "max_attempts",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or value <= 0:
                raise LaunchAdmissionError(f"{name} must be a positive integer")
        if self.max_backoff_seconds < self.base_backoff_seconds:
            raise LaunchAdmissionError("max_backoff_seconds must be >= base_backoff_seconds")
        if not isinstance(self.jitter_percent, int) or not 0 <= self.jitter_percent <= 100:
            raise LaunchAdmissionError("jitter_percent must be between 0 and 100")


@dataclass(frozen=True)
class LaunchAttemptState:
    project_id: str
    task_id: str
    occurrence_id: str
    status: str = "PENDING"
    attempt: int = 0
    next_eligible_at: datetime | None = None
    last_result: str | None = None
    admitted_at: datetime | None = None
    bootstrap_ready_at: datetime | None = None

    def __post_init__(self):
        require_project_id(self.project_id)
        require_resource_id(self.task_id, field="task_id")
        require_resource_id(self.occurrence_id, field="occurrence_id")
        if self.status not in {
            "PENDING",
            "ADMITTED",
            "PROVIDER_ACCEPTED",
            "BOOTSTRAP_READY",
            "RETRY_WAIT",
            "COMPLETED",
            "TERMINAL_FAILURE",
        }:
            raise LaunchAdmissionError("unsupported launch status")
        if not isinstance(self.attempt, int) or self.attempt < 0:
            raise LaunchAdmissionError("attempt must be a non-negative integer")
        for value in (self.next_eligible_at, self.admitted_at, self.bootstrap_ready_at):
            if value is not None:
                _require_aware(value)

    @property
    def key(self) -> str:
        return f"{self.project_id}::{self.task_id}::{self.occurrence_id}"


@dataclass(frozen=True)
class AdmissionDecision:
    admitted: bool
    state: LaunchAttemptState
    retry_at: datetime | None = None
    reason: str | None = None


class LaunchAdmissionController:
    """
    Reference admission/backoff controller for a scheduler or dispatcher.

    This code must run before provider/model invocation to prevent a thundering
    herd. If the hosting scheduler cannot execute this layer before invocation,
    callers should apply deterministic schedule staggering and persist retry
    state outside the model process.
    """

    def __init__(self, policy: LaunchAdmissionPolicy | None = None):
        self.policy = policy or LaunchAdmissionPolicy()
        self._inflight: set[str] = set()
        self._last_admitted_at: datetime | None = None

    def _backoff_seconds(self, state: LaunchAttemptState) -> int:
        exponent = max(0, state.attempt - 1)
        base = min(
            self.policy.max_backoff_seconds,
            self.policy.base_backoff_seconds * (2 ** exponent),
        )
        if self.policy.jitter_percent == 0:
            return base
        ceiling = max(1, (base * self.policy.jitter_percent) // 100)
        digest = hashlib.sha256(
            f"{state.key}\0{state.attempt}".encode("utf-8")
        ).digest()
        jitter = int.from_bytes(digest[:8], "big") % (ceiling + 1)
        return min(self.policy.max_backoff_seconds, base + jitter)

    def admit(self, state: LaunchAttemptState, now: datetime) -> AdmissionDecision:
        now = _require_aware(now)
        if state.status in {"COMPLETED", "TERMINAL_FAILURE"}:
            return AdmissionDecision(False, state, reason="terminal")
        if state.status in {"ADMITTED", "PROVIDER_ACCEPTED", "BOOTSTRAP_READY"}:
            return AdmissionDecision(False, state, reason="already_inflight_or_started")
        if state.next_eligible_at is not None and now < state.next_eligible_at:
            return AdmissionDecision(False, state, retry_at=state.next_eligible_at, reason="backoff")
        if len(self._inflight) >= self.policy.max_inflight:
            retry_at = now + timedelta(seconds=self.policy.min_start_interval_seconds)
            return AdmissionDecision(False, state, retry_at=retry_at, reason="concurrency_limit")
        if self._last_admitted_at is not None:
            spacing_deadline = self._last_admitted_at + timedelta(
                seconds=self.policy.min_start_interval_seconds
            )
            if now < spacing_deadline:
                return AdmissionDecision(False, state, retry_at=spacing_deadline, reason="start_spacing")
        if state.attempt >= self.policy.max_attempts:
            terminal = replace(state, status="TERMINAL_FAILURE", last_result="MAX_ATTEMPTS_EXCEEDED")
            return AdmissionDecision(False, terminal, reason="max_attempts")

        admitted = replace(
            state,
            status="ADMITTED",
            attempt=state.attempt + 1,
            admitted_at=now,
            next_eligible_at=None,
        )
        self._inflight.add(admitted.key)
        self._last_admitted_at = now
        return AdmissionDecision(True, admitted)

    def provider_result(
        self,
        state: LaunchAttemptState,
        result: str,
        now: datetime,
    ) -> LaunchAttemptState:
        now = _require_aware(now)
        self._inflight.discard(state.key)
        if state.status != "ADMITTED":
            raise LaunchAdmissionError("provider_result requires ADMITTED state")

        if result == "ACCEPTED":
            return replace(state, status="PROVIDER_ACCEPTED", last_result=result)

        if result in RETRYABLE_PROVIDER_RESULTS:
            if state.attempt >= self.policy.max_attempts:
                return replace(
                    state,
                    status="TERMINAL_FAILURE",
                    last_result=f"{result}:MAX_ATTEMPTS_EXCEEDED",
                )
            delay = self._backoff_seconds(state)
            return replace(
                state,
                status="RETRY_WAIT",
                last_result=result,
                next_eligible_at=now + timedelta(seconds=delay),
            )

        if result in TERMINAL_PROVIDER_RESULTS:
            return replace(state, status="TERMINAL_FAILURE", last_result=result)

        raise LaunchAdmissionError("unknown provider result")

    def bootstrap_ready(self, state: LaunchAttemptState, now: datetime) -> LaunchAttemptState:
        now = _require_aware(now)
        if state.status != "PROVIDER_ACCEPTED":
            raise LaunchAdmissionError("bootstrap_ready requires PROVIDER_ACCEPTED state")
        return replace(state, status="BOOTSTRAP_READY", bootstrap_ready_at=now)

    def complete(self, state: LaunchAttemptState) -> LaunchAttemptState:
        if state.status != "BOOTSTRAP_READY":
            raise LaunchAdmissionError("task completion requires BOOTSTRAP_READY state")
        return replace(state, status="COMPLETED", last_result="COMPLETED")

    @staticmethod
    def may_advance_task_state(state: LaunchAttemptState) -> bool:
        return state.status in {"BOOTSTRAP_READY", "COMPLETED"}
