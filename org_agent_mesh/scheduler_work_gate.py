from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class WorkConsequence(str, Enum):
    READ_ONLY = "READ_ONLY"
    APPEND_ONLY_OBSERVABILITY = "APPEND_ONLY_OBSERVABILITY"
    REVERSIBLE_MUTATION = "REVERSIBLE_MUTATION"
    PROTECTED_MUTATION = "PROTECTED_MUTATION"


@dataclass(frozen=True)
class SchedulerWorkDecision:
    allowed: bool
    reason: str
    lane_health_state: str
    consequence: WorkConsequence


KNOWN_HEALTH_STATES = frozenset(
    {
        "HEALTHY",
        "RECOVERING",
        "DEGRADED_MISSING_EXECUTION_EVIDENCE",
        "UNQUALIFIED",
    }
)


def evaluate_scheduler_work_gate(
    *,
    lane_health_state: str,
    consequence: WorkConsequence,
) -> SchedulerWorkDecision:
    """Apply scheduler health as an additional restriction on scheduled work.

    This gate never grants project mutation authority. A HEALTHY lane may proceed to
    the normal project/role/mutation gates. A non-healthy lane is restricted to
    read-only work and append-only observability/checkpoint evidence so recovery can
    continue without allowing a degraded execution surface to perform consequential
    mutations.
    """
    if lane_health_state not in KNOWN_HEALTH_STATES:
        return SchedulerWorkDecision(
            allowed=False,
            reason="UNKNOWN_SCHEDULER_HEALTH_STATE_FAILS_CLOSED",
            lane_health_state=lane_health_state,
            consequence=consequence,
        )

    if lane_health_state == "HEALTHY":
        return SchedulerWorkDecision(
            allowed=True,
            reason="SCHEDULER_HEALTH_GATE_PASSED_NORMAL_AUTHORITY_STILL_REQUIRED",
            lane_health_state=lane_health_state,
            consequence=consequence,
        )

    if consequence in {WorkConsequence.READ_ONLY, WorkConsequence.APPEND_ONLY_OBSERVABILITY}:
        return SchedulerWorkDecision(
            allowed=True,
            reason="NON_HEALTHY_LANE_RESTRICTED_TO_SAFE_NON_CONSEQUENTIAL_WORK",
            lane_health_state=lane_health_state,
            consequence=consequence,
        )

    return SchedulerWorkDecision(
        allowed=False,
        reason="SCHEDULER_HEALTH_NOT_QUALIFIED_FOR_CONSEQUENTIAL_MUTATION",
        lane_health_state=lane_health_state,
        consequence=consequence,
    )
