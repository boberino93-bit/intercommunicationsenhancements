from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .schedule_activation import (
    ActivationActor,
    ScheduleActivationError,
    ScheduleStateChangeRequest,
    evaluate_schedule_state_change,
)


class FrontendTaskHealth(str, Enum):
    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    UNAVAILABLE = "UNAVAILABLE"
    STALE = "STALE"


class ReconciliationAction(str, Enum):
    NO_STATE_CHANGE = "NO_STATE_CHANGE"
    DISABLE_AUTHORIZED = "DISABLE_AUTHORIZED"
    ENABLE_AUTHORIZED = "ENABLE_AUTHORIZED"
    ENABLE_AUTHORIZATION_REQUIRED = "ENABLE_AUTHORIZATION_REQUIRED"
    REPLACEMENT_AUTHORIZATION_REQUIRED = "REPLACEMENT_AUTHORIZATION_REQUIRED"
    CAPACITY_LIMIT_DEFERRED = "CAPACITY_LIMIT_DEFERRED"
    STALE_EXECUTION_REPORTED = "STALE_EXECUTION_REPORTED"


@dataclass(frozen=True)
class ReconciliationRequest:
    task_id: str
    current_enabled: bool
    backend_enabled: bool
    enabled_state_policy: str
    health: FrontendTaskHealth = FrontendTaskHealth.AVAILABLE
    account_capacity_available: bool = True
    actor: ActivationActor = ActivationActor.SYSTEM
    explicit_human_request: bool = False


@dataclass(frozen=True)
class ReconciliationDecision:
    action: ReconciliationAction
    may_mutate_frontend: bool
    resulting_enabled: bool
    reason: str


SUPPORTED_ENABLED_STATE_POLICIES = frozenset(
    {
        "MIRROR",
        "MIRROR_WHEN_ACCOUNT_CAPACITY_AVAILABLE",
        "MIRROR_DISABLED_STANDBY",
        "FRONTEND_ONLY",
    }
)


def decide_frontend_reconciliation(request: ReconciliationRequest) -> ReconciliationDecision:
    """Resolve one mapped frontend task without bypassing the activation gate.

    Capacity availability is an admission fact, not activation authority. Missing or dead
    frontend identities are never replaced automatically. Disabled->enabled transitions
    are delegated to schedule_activation so scheduler synchronization cannot silently
    weaken the global human-only activation invariant.
    """
    if request.enabled_state_policy not in SUPPORTED_ENABLED_STATE_POLICIES:
        raise ValueError(f"unsupported enabled_state_policy: {request.enabled_state_policy}")

    if request.health in {FrontendTaskHealth.MISSING, FrontendTaskHealth.UNAVAILABLE}:
        return ReconciliationDecision(
            action=ReconciliationAction.REPLACEMENT_AUTHORIZATION_REQUIRED,
            may_mutate_frontend=False,
            resulting_enabled=request.current_enabled,
            reason="DECLARED_FRONTEND_IDENTITY_UNAVAILABLE_REQUIRES_EXPLICIT_HUMAN_REPLACEMENT_AUTHORIZATION",
        )

    if request.health is FrontendTaskHealth.STALE:
        return ReconciliationDecision(
            action=ReconciliationAction.STALE_EXECUTION_REPORTED,
            may_mutate_frontend=False,
            resulting_enabled=request.current_enabled,
            reason="STALE_EXECUTION_IS_OBSERVABILITY_EVIDENCE_NOT_REPLACEMENT_AUTHORITY",
        )

    if request.enabled_state_policy == "FRONTEND_ONLY":
        return ReconciliationDecision(
            action=ReconciliationAction.NO_STATE_CHANGE,
            may_mutate_frontend=False,
            resulting_enabled=request.current_enabled,
            reason="FRONTEND_ONLY_TASK_REMAINS_FRONTEND_CONTROL",
        )

    if request.enabled_state_policy == "MIRROR_DISABLED_STANDBY":
        desired_enabled = False
    else:
        desired_enabled = request.backend_enabled

    if desired_enabled == request.current_enabled:
        return ReconciliationDecision(
            action=ReconciliationAction.NO_STATE_CHANGE,
            may_mutate_frontend=False,
            resulting_enabled=request.current_enabled,
            reason="ENABLED_STATE_ALREADY_RECONCILED",
        )

    if desired_enabled and not request.account_capacity_available:
        return ReconciliationDecision(
            action=ReconciliationAction.CAPACITY_LIMIT_DEFERRED,
            may_mutate_frontend=False,
            resulting_enabled=request.current_enabled,
            reason="CAPACITY_UNAVAILABLE_DOES_NOT_GRANT_OR_CONSUME_ACTIVATION_AUTHORITY",
        )

    try:
        decision = evaluate_schedule_state_change(
            ScheduleStateChangeRequest(
                task_id=request.task_id,
                current_enabled=request.current_enabled,
                requested_enabled=desired_enabled,
                actor=request.actor,
                explicit_human_request=request.explicit_human_request,
            )
        )
    except ScheduleActivationError:
        if desired_enabled:
            return ReconciliationDecision(
                action=ReconciliationAction.ENABLE_AUTHORIZATION_REQUIRED,
                may_mutate_frontend=False,
                resulting_enabled=request.current_enabled,
                reason="GLOBAL_SCHEDULE_ACTIVATION_GATE_REQUIRES_EXPLICIT_CURRENT_HUMAN_ENABLEMENT",
            )
        raise

    if decision.resulting_enabled:
        return ReconciliationDecision(
            action=ReconciliationAction.ENABLE_AUTHORIZED,
            may_mutate_frontend=True,
            resulting_enabled=True,
            reason=decision.reason,
        )

    return ReconciliationDecision(
        action=ReconciliationAction.DISABLE_AUTHORIZED,
        may_mutate_frontend=True,
        resulting_enabled=False,
        reason=decision.reason,
    )
