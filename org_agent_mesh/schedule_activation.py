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
    declared_repair_actor: bool = False
    repair_authorization_ref: str | None = None
    repair_scope_contains_task: bool = False
    repair_guard_passed: bool = False
    repair_guard_reason: str | None = None


@dataclass(frozen=True)
class ScheduleStateDecision:
    allowed: bool
    resulting_enabled: bool
    reason: str


def evaluate_schedule_state_change(request: ScheduleStateChangeRequest) -> ScheduleStateDecision:
    """Enforce human-controlled activation with bounded delegated liveness repair.

    A disabled task can be enabled directly by an explicit current human request. A
    declared SYSTEM/RECOVERY reconciler may restore an already-declared mapped task
    only when it carries a durable human repair authorization reference, the target is
    explicitly in scope, and the separate time/budget/quarantine repair guard passed.
    This is repair authority, not general activation or task-creation authority.
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

    if (
        request.actor in {ActivationActor.SYSTEM, ActivationActor.RECOVERY}
        and request.declared_repair_actor
        and bool(request.repair_authorization_ref)
        and request.repair_scope_contains_task
        and request.repair_guard_passed
    ):
        return ScheduleStateDecision(
            allowed=True,
            resulting_enabled=True,
            reason="HUMAN_AUTHORIZED_DECLARED_LIVENESS_REPAIR",
        )

    guard_detail = (
        f" ({request.repair_guard_reason})" if request.repair_guard_reason else ""
    )
    raise ScheduleActivationError(
        "Scheduled swarm tasks may only be enabled by an explicit current human request "
        "or a declared repair actor operating inside a current scoped human repair authorization "
        f"that passed the repair guard{guard_detail}"
    )


def require_preserve_enabled_state(
    *,
    current_enabled: bool,
    proposed_enabled: bool | None,
    actor: ActivationActor,
    explicit_human_request: bool = False,
    declared_repair_actor: bool = False,
    repair_authorization_ref: str | None = None,
    repair_scope_contains_task: bool = False,
    repair_guard_passed: bool = False,
    repair_guard_reason: str | None = None,
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
            declared_repair_actor=declared_repair_actor,
            repair_authorization_ref=repair_authorization_ref,
            repair_scope_contains_task=repair_scope_contains_task,
            repair_guard_passed=repair_guard_passed,
            repair_guard_reason=repair_guard_reason,
        )
    )
    return decision.resulting_enabled
