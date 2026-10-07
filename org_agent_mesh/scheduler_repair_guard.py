from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

UTC = timezone.utc


class RepairGrantError(ValueError):
    pass


def _parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise RepairGrantError("invalid grant or ledger timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RepairGrantError("grant and ledger timestamps must be timezone-aware")
    return parsed.astimezone(UTC)


@dataclass(frozen=True)
class RepairGrantDecision:
    allowed: bool
    reason: str
    quarantine_required: bool
    target_repairs_in_window: int
    total_repairs_in_window: int
    expires_at: str | None


def evaluate_repair_grant(
    grant: dict,
    *,
    actor_frontend_automation_id: str,
    target_frontend_automation_id: str,
    observed_at: datetime,
    ledger_events: list[dict] | tuple[dict, ...] = (),
) -> RepairGrantDecision:
    """Evaluate a bounded scheduler liveness-repair grant.

    This function grants no scheduler authority by itself. It only decides whether the
    durable human grant is current, exactly scoped, and still inside its repair budget.
    The normal scheduler activation and reconciliation gates remain independently
    required.
    """
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise RepairGrantError("observed_at must be timezone-aware")
    now = observed_at.astimezone(UTC)

    expires_at_value = grant.get("expires_at")
    expires_at = _parse_time(expires_at_value) if expires_at_value else None
    issued_at_value = grant.get("issued_at")
    issued_at = _parse_time(issued_at_value) if issued_at_value else None

    def decision(allowed: bool, reason: str, *, quarantine: bool = False, target_count: int = 0, total_count: int = 0):
        return RepairGrantDecision(
            allowed=allowed,
            reason=reason,
            quarantine_required=quarantine,
            target_repairs_in_window=target_count,
            total_repairs_in_window=total_count,
            expires_at=expires_at_value,
        )

    if grant.get("status") != "ACTIVE":
        return decision(False, "REPAIR_GRANT_NOT_ACTIVE")
    if issued_at is None or expires_at is None:
        return decision(False, "REPAIR_GRANT_MISSING_TIME_BOUNDS")
    if expires_at <= issued_at:
        raise RepairGrantError("repair grant expires_at must be after issued_at")
    if now < issued_at:
        return decision(False, "REPAIR_GRANT_NOT_YET_VALID")
    if now >= expires_at:
        return decision(False, "REPAIR_GRANT_EXPIRED")

    authorized_actors = {
        item.get("frontend_automation_id")
        for item in grant.get("authorized_repair_actors", [])
        if item.get("frontend_automation_id")
    }
    if actor_frontend_automation_id not in authorized_actors:
        return decision(False, "REPAIR_ACTOR_NOT_AUTHORIZED")

    targets = set(grant.get("authorized_target_frontend_automation_ids", []))
    if target_frontend_automation_id not in targets:
        return decision(False, "REPAIR_TARGET_NOT_AUTHORIZED")
    if grant.get("allowed_transition") != "DISABLED_TO_ENABLED_ONLY":
        return decision(False, "REPAIR_GRANT_TRANSITION_SCOPE_INVALID")

    budget = grant.get("repair_budget") or {}
    window_minutes = int(budget.get("window_minutes", 0))
    max_per_target = int(budget.get("max_repairs_per_target_in_window", 0))
    max_total = int(budget.get("max_total_repairs_in_window", 0))
    if window_minutes <= 0 or max_per_target <= 0 or max_total <= 0:
        return decision(False, "REPAIR_GRANT_BUDGET_INVALID")

    window_start = now - timedelta(minutes=window_minutes)
    applied_statuses = set(budget.get("count_statuses", ["APPLIED_AND_VERIFIED"]))
    recent: list[dict] = []
    for event in ledger_events:
        timestamp_value = event.get("observed_at")
        if not timestamp_value:
            continue
        timestamp = _parse_time(timestamp_value)
        if timestamp > now:
            raise RepairGrantError("repair ledger contains a future event")
        if timestamp < window_start:
            continue
        if event.get("status") not in applied_statuses:
            continue
        if event.get("resulting_enabled_state") is not True:
            continue
        recent.append(event)

    total_count = len(recent)
    target_count = sum(
        1 for event in recent if event.get("frontend_automation_id") == target_frontend_automation_id
    )
    if target_count >= max_per_target:
        return decision(
            False,
            "REPAIR_TARGET_BUDGET_EXHAUSTED",
            quarantine=True,
            target_count=target_count,
            total_count=total_count,
        )
    if total_count >= max_total:
        return decision(
            False,
            "REPAIR_GLOBAL_BUDGET_EXHAUSTED",
            quarantine=True,
            target_count=target_count,
            total_count=total_count,
        )

    return decision(
        True,
        "REPAIR_GRANT_CURRENT_SCOPED_AND_WITHIN_BUDGET",
        target_count=target_count,
        total_count=total_count,
    )
