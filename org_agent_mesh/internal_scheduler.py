from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
import hashlib
from typing import Protocol

from .launch_admission import (
    LaunchAdmissionController,
    LaunchAdmissionPolicy,
    LaunchAttemptState,
)
from .project_scope import require_project_id, require_resource_id


class InternalSchedulerError(ValueError):
    pass


def _aware_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise InternalSchedulerError("timezone-aware datetime required")
    return value.astimezone(timezone.utc)


def _stable_id(*parts: str) -> str:
    material = "\0".join(parts).encode("utf-8")
    return hashlib.sha256(material).hexdigest()[:32]


@dataclass(frozen=True)
class InternalScheduleSpec:
    schedule_id: str
    project_id: str
    task_id: str
    role_id: str
    interval_seconds: int
    next_due_at: datetime
    enabled: bool = True
    catch_up_policy: str = "COALESCE_TO_LATEST"
    max_pending_tickets: int = 1

    def __post_init__(self):
        require_resource_id(self.schedule_id, field="schedule_id")
        require_project_id(self.project_id)
        require_resource_id(self.task_id, field="task_id")
        require_resource_id(self.role_id, field="role_id")
        if self.role_id.lower() == "primary":
            raise InternalSchedulerError("PRIMARY creation is prohibited for internal scheduler service")
        if not isinstance(self.interval_seconds, int) or self.interval_seconds <= 0:
            raise InternalSchedulerError("interval_seconds must be a positive integer")
        _aware_utc(self.next_due_at)
        if self.catch_up_policy not in {"COALESCE_TO_LATEST", "SKIP_OBSOLETE", "REPLAY_REQUIRED"}:
            raise InternalSchedulerError("unsupported catch_up_policy")
        if not isinstance(self.max_pending_tickets, int) or self.max_pending_tickets <= 0:
            raise InternalSchedulerError("max_pending_tickets must be a positive integer")


@dataclass(frozen=True)
class SpawnTicket:
    ticket_id: str
    occurrence_id: str
    schedule_id: str
    project_id: str
    task_id: str
    role_id: str
    scheduled_for: datetime
    created_at: datetime
    state: str = "READY_FOR_HOST_ADMISSION"
    attempt: int = 0
    provider_result: str | None = None
    next_eligible_at: datetime | None = None
    session_started: bool = False
    authority_conveyed: bool = False

    def __post_init__(self):
        for field, value in (
            ("ticket_id", self.ticket_id),
            ("occurrence_id", self.occurrence_id),
            ("schedule_id", self.schedule_id),
            ("task_id", self.task_id),
            ("role_id", self.role_id),
        ):
            require_resource_id(value, field=field)
        require_project_id(self.project_id)
        _aware_utc(self.scheduled_for)
        _aware_utc(self.created_at)
        if self.next_eligible_at is not None:
            _aware_utc(self.next_eligible_at)
        if self.state not in {
            "READY_FOR_HOST_ADMISSION",
            "HOST_ADMITTED",
            "PROVIDER_ACCEPTED",
            "BOOTSTRAP_READY",
            "RETRY_WAIT",
            "COMPLETED",
            "TERMINAL_FAILURE",
            "HOST_SPAWN_ADAPTER_REQUIRED",
        }:
            raise InternalSchedulerError("unsupported ticket state")
        if self.session_started and self.state not in {"PROVIDER_ACCEPTED", "BOOTSTRAP_READY", "COMPLETED"}:
            raise InternalSchedulerError("session_started requires accepted provider state")
        if self.authority_conveyed:
            raise InternalSchedulerError("spawn tickets never convey mutation authority")


@dataclass(frozen=True)
class HostLaunchReceipt:
    ticket_id: str
    provider_result: str
    session_started: bool = False
    external_execution_id: str | None = None


class HostSpawnAdapter(Protocol):
    """Host boundary that may turn an admitted ticket into a real model execution."""

    def submit(self, ticket: SpawnTicket) -> HostLaunchReceipt:
        ...


class BootstrapInternalScheduler:
    """
    Deterministic bootstrap-resident scheduler kernel.

    The service independently decides when work is due and emits durable spawn
    tickets. A ticket is an execution request, not proof that a ChatGPT/model
    session exists. Real session creation remains a host capability and must pass
    the existing provider-admission and supervisory gates.
    """

    def __init__(
        self,
        *,
        admission_policy: LaunchAdmissionPolicy | None = None,
    ):
        self._schedules: dict[str, InternalScheduleSpec] = {}
        self._tickets: dict[str, SpawnTicket] = {}
        self._launch_states: dict[str, LaunchAttemptState] = {}
        self._admission = LaunchAdmissionController(admission_policy)

    @property
    def schedules(self) -> tuple[InternalScheduleSpec, ...]:
        return tuple(self._schedules[key] for key in sorted(self._schedules))

    @property
    def tickets(self) -> tuple[SpawnTicket, ...]:
        return tuple(self._tickets[key] for key in sorted(self._tickets))

    def register(self, spec: InternalScheduleSpec) -> None:
        if spec.schedule_id in self._schedules:
            raise InternalSchedulerError("schedule_id already registered")
        self._schedules[spec.schedule_id] = spec

    def set_enabled(self, schedule_id: str, enabled: bool, *, explicit_human_action: bool) -> None:
        require_resource_id(schedule_id, field="schedule_id")
        if schedule_id not in self._schedules:
            raise InternalSchedulerError("unknown schedule_id")
        current = self._schedules[schedule_id]
        if current.enabled == enabled:
            return
        if enabled and not explicit_human_action:
            raise InternalSchedulerError("disabled -> enabled requires explicit human action")
        self._schedules[schedule_id] = replace(current, enabled=enabled)

    def _pending_count(self, schedule_id: str) -> int:
        terminal = {"COMPLETED", "TERMINAL_FAILURE"}
        return sum(
            1
            for ticket in self._tickets.values()
            if ticket.schedule_id == schedule_id and ticket.state not in terminal
        )

    @staticmethod
    def _latest_due(spec: InternalScheduleSpec, now: datetime) -> datetime:
        due = _aware_utc(spec.next_due_at)
        now = _aware_utc(now)
        if now < due:
            return due
        elapsed = int((now - due).total_seconds())
        intervals = elapsed // spec.interval_seconds
        return due + timedelta(seconds=intervals * spec.interval_seconds)

    def tick(self, now: datetime) -> tuple[SpawnTicket, ...]:
        now = _aware_utc(now)
        emitted: list[SpawnTicket] = []
        for schedule_id in sorted(self._schedules):
            spec = self._schedules[schedule_id]
            if not spec.enabled or now < _aware_utc(spec.next_due_at):
                continue

            if self._pending_count(schedule_id) >= spec.max_pending_tickets:
                continue

            if spec.catch_up_policy == "REPLAY_REQUIRED":
                scheduled_for = _aware_utc(spec.next_due_at)
            else:
                scheduled_for = self._latest_due(spec, now)

            occurrence_id = _stable_id(schedule_id, scheduled_for.isoformat())
            ticket_id = _stable_id("spawn", spec.project_id, spec.task_id, occurrence_id)
            if ticket_id not in self._tickets:
                ticket = SpawnTicket(
                    ticket_id=ticket_id,
                    occurrence_id=occurrence_id,
                    schedule_id=schedule_id,
                    project_id=spec.project_id,
                    task_id=spec.task_id,
                    role_id=spec.role_id,
                    scheduled_for=scheduled_for,
                    created_at=now,
                )
                self._tickets[ticket_id] = ticket
                self._launch_states[ticket_id] = LaunchAttemptState(
                    project_id=spec.project_id,
                    task_id=spec.task_id,
                    occurrence_id=occurrence_id,
                )
                emitted.append(ticket)

            self._schedules[schedule_id] = replace(
                spec,
                next_due_at=scheduled_for + timedelta(seconds=spec.interval_seconds),
            )
        return tuple(emitted)

    def dispatch(
        self,
        ticket_id: str,
        now: datetime,
        adapter: HostSpawnAdapter | None,
    ) -> SpawnTicket:
        require_resource_id(ticket_id, field="ticket_id")
        now = _aware_utc(now)
        ticket = self._tickets.get(ticket_id)
        if ticket is None:
            raise InternalSchedulerError("unknown ticket_id")
        if ticket.state in {"COMPLETED", "TERMINAL_FAILURE"}:
            return ticket
        if adapter is None:
            updated = replace(ticket, state="HOST_SPAWN_ADAPTER_REQUIRED")
            self._tickets[ticket_id] = updated
            return updated

        state = self._launch_states[ticket_id]
        decision = self._admission.admit(state, now)
        self._launch_states[ticket_id] = decision.state
        if not decision.admitted:
            mapped_state = "RETRY_WAIT" if decision.retry_at else ticket.state
            updated = replace(ticket, state=mapped_state, next_eligible_at=decision.retry_at)
            self._tickets[ticket_id] = updated
            return updated

        admitted_ticket = replace(
            ticket,
            state="HOST_ADMITTED",
            attempt=decision.state.attempt,
            next_eligible_at=None,
        )
        self._tickets[ticket_id] = admitted_ticket
        receipt = adapter.submit(admitted_ticket)
        if receipt.ticket_id != ticket_id:
            raise InternalSchedulerError("host receipt ticket_id mismatch")

        provider_state = self._admission.provider_result(
            decision.state,
            receipt.provider_result,
            now,
        )
        self._launch_states[ticket_id] = provider_state

        if provider_state.status == "PROVIDER_ACCEPTED":
            updated = replace(
                admitted_ticket,
                state="PROVIDER_ACCEPTED",
                provider_result=receipt.provider_result,
                session_started=bool(receipt.session_started),
            )
        elif provider_state.status == "RETRY_WAIT":
            updated = replace(
                admitted_ticket,
                state="RETRY_WAIT",
                provider_result=receipt.provider_result,
                next_eligible_at=provider_state.next_eligible_at,
                session_started=False,
            )
        else:
            updated = replace(
                admitted_ticket,
                state="TERMINAL_FAILURE",
                provider_result=receipt.provider_result,
                session_started=False,
            )
        self._tickets[ticket_id] = updated
        return updated

    def mark_bootstrap_ready(self, ticket_id: str, now: datetime) -> SpawnTicket:
        ticket = self._tickets[ticket_id]
        state = self._admission.bootstrap_ready(self._launch_states[ticket_id], now)
        self._launch_states[ticket_id] = state
        updated = replace(ticket, state="BOOTSTRAP_READY", session_started=True)
        self._tickets[ticket_id] = updated
        return updated

    def mark_completed(self, ticket_id: str) -> SpawnTicket:
        ticket = self._tickets[ticket_id]
        state = self._admission.complete(self._launch_states[ticket_id])
        self._launch_states[ticket_id] = state
        updated = replace(ticket, state="COMPLETED", session_started=True)
        self._tickets[ticket_id] = updated
        return updated

    def snapshot(self) -> dict:
        def encode_datetime(value):
            if isinstance(value, datetime):
                return _aware_utc(value).isoformat()
            return value

        schedules = []
        for spec in self.schedules:
            row = asdict(spec)
            row["next_due_at"] = encode_datetime(spec.next_due_at)
            schedules.append(row)

        tickets = []
        for ticket in self.tickets:
            row = asdict(ticket)
            for field in ("scheduled_for", "created_at", "next_eligible_at"):
                row[field] = encode_datetime(row[field]) if row[field] is not None else None
            tickets.append(row)

        return {
            "schema": "org-agent-mesh/internal-scheduler-state/v1",
            "schedules": schedules,
            "tickets": tickets,
            "invariants": {
                "spawn_ticket_is_session_started": False,
                "schedule_fire_is_mutation_authority": False,
                "primary_creation_allowed": False,
            },
        }
