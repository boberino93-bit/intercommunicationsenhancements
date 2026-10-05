from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ScheduleActivationError(PermissionError):
    pass


class ActivationActor(str, Enum):
    USER = "USER"
    MASTER = "MASTER"
    PRIMARY = "PRIMARY"
    MANAGER = "MANAGER"
    RESEARCHER = "RESEARCHER"
    RECOVERY = "RECOVERY"
    MIGRATION = "MIGRATION"
    SYSTEM = "SYSTEM"


@dataclass(frozen=True)
class ScheduleStateChangeRequest:
    task_id: str
    current_enabled: bool
    requested_enabled: bool
    actor: ActivationActor
    explicit_human_request: bool = False


@dataclass(frozen=True)
class ScheduleStateDecision:
    allowed: bool
    resulting_enabled: bool
    reason: str


def evaluate_schedule_state_change(request: ScheduleStateChangeRequest) -> ScheduleStateDecision:
    """Enforce human-only activation while allowing safe preservation/disable operations.

    This gate is intentionally stricter than runtime lifecycle authority. MASTER/PRIMARY
    may supervise running work, but they may not turn a disabled recurring swarm task on.
    """
    if request.requested_enabled == request.current_enabled:
        return ScheduleStateDecision(
            allowed=True,
            resulting_enabled=request.current_enabled,
            reason="NO_STATE_CHANGE",
        )

    if request.requested_enabled is False:
        if request.actor in {
            ActivationActor.USER,
            ActivationActor.MASTER,
            ActivationActor.PRIMARY,
            ActivationActor.MANAGER,
            ActivationActor.RECOVERY,
            ActivationActor.SYSTEM,
        }:
            return ScheduleStateDecision(
                allowed=True,
                resulting_enabled=False,
                reason="DISABLE_ALLOWED_AS_CONTAINMENT_OR_HUMAN_CONTROL",
            )
        raise ScheduleActivationError(
            f"{request.actor.value} is not authorized to change scheduled task enablement"
        )

    if request.actor is ActivationActor.USER and request.explicit_human_request:
        return ScheduleStateDecision(
            allowed=True,
            resulting_enabled=True,
            reason="EXPLICIT_HUMAN_ENABLEMENT",
        )

    raise ScheduleActivationError(
        "Scheduled swarm tasks may only be enabled by an explicit current human request"
    )


def require_preserve_enabled_state(
    *,
    current_enabled: bool,
    proposed_enabled: bool | None,
    actor: ActivationActor,
    explicit_human_request: bool = False,
) -> bool:
    """Use for migrations/alignment so omitted state remains unchanged by construction."""
    if proposed_enabled is None:
        return current_enabled
    decision = evaluate_schedule_state_change(
        ScheduleStateChangeRequest(
            task_id="unspecified",
            current_enabled=current_enabled,
            requested_enabled=proposed_enabled,
            actor=actor,
            explicit_human_request=explicit_human_request,
        )
    )
    return decision.resulting_enabled
