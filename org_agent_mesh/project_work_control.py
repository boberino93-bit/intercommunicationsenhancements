from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable, Mapping, Any


class ProjectWorkControlError(ValueError):
    pass


class ProjectWorkState(str, Enum):
    ACTIVE = "ACTIVE"
    HOLD = "HOLD"
    HOLD_EXPIRED_PENDING_HUMAN_RESUME = "HOLD_EXPIRED_PENDING_HUMAN_RESUME"


class WorkControlAction(str, Enum):
    HOLD = "HOLD"
    EXTEND_HOLD = "EXTEND_HOLD"
    RESUME = "RESUME"


class ResumePolicy(str, Enum):
    MANUAL = "MANUAL"
    AUTO_AT_EXPIRY = "AUTO_AT_EXPIRY"


@dataclass(frozen=True)
class ProjectHold:
    project_id: str
    hold_order_id: str
    issued_at: datetime
    effective_at: datetime
    expires_at: datetime | None
    resume_policy: ResumePolicy
    reason_code: str
    human_reason: str
    metadata: Mapping[str, Any]
    claimed_principal: str
    authentication_ref: str
    authorization_case_id: str
    event_id: str


@dataclass(frozen=True)
class ProjectWorkDecision:
    project_id: str
    state: ProjectWorkState
    allow_new_work: bool
    allow_respawn: bool
    allow_mutation: bool
    reason: str
    active_hold: ProjectHold | None = None


def _parse_datetime(value: str | datetime | None, *, field: str) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError as exc:
            raise ProjectWorkControlError(f"invalid {field}: {value!r}") from exc
    if dt.tzinfo is None:
        raise ProjectWorkControlError(f"{field} must be timezone-aware")
    return dt.astimezone(timezone.utc)


def _event_time(event: Mapping[str, Any]) -> datetime:
    value = _parse_datetime(event.get("issued_at"), field="issued_at")
    if value is None:
        raise ProjectWorkControlError("issued_at is required")
    return value


def _validated_event(event: Mapping[str, Any]) -> Mapping[str, Any]:
    required = {
        "schema",
        "event_id",
        "project_id",
        "action",
        "hold_order_id",
        "issued_at",
        "effective_at",
        "expires_at",
        "resume_policy",
        "reason_code",
        "human_reason",
        "metadata",
        "claimed_principal",
        "authentication_ref",
        "authorization_case_id",
        "preserve_partial_state",
    }
    missing = sorted(required.difference(event))
    if missing:
        raise ProjectWorkControlError(f"missing event fields: {', '.join(missing)}")
    if event.get("schema") != "org-agent-mesh/project-work-control-event/v1":
        raise ProjectWorkControlError("unsupported project work control schema")
    if event.get("preserve_partial_state") is not True:
        raise ProjectWorkControlError("project hold events must preserve partial state")
    for field in ("event_id", "project_id", "hold_order_id", "claimed_principal", "authentication_ref", "authorization_case_id"):
        if not str(event.get(field, "")).strip():
            raise ProjectWorkControlError(f"{field} must be non-empty")
    WorkControlAction(str(event["action"]))
    ResumePolicy(str(event["resume_policy"]))
    _parse_datetime(event.get("effective_at"), field="effective_at")
    _parse_datetime(event.get("expires_at"), field="expires_at")
    _event_time(event)
    return event


def resolve_project_work_state(
    project_id: str,
    events: Iterable[Mapping[str, Any]],
    *,
    now: datetime | None = None,
) -> ProjectWorkDecision:
    """Resolve append-only HOLD/EXTEND_HOLD/RESUME events for one project.

    Events are processed by issued_at then event_id so the projection is deterministic.
    Authentication/authorization must be validated before an event is admitted to this
    resolver; this module never manufactures human authority.
    """
    current_time = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    relevant = [dict(_validated_event(e)) for e in events if e.get("project_id") == project_id]
    relevant.sort(key=lambda e: (_event_time(e), str(e["event_id"])))

    active: ProjectHold | None = None
    for event in relevant:
        effective_at = _parse_datetime(event["effective_at"], field="effective_at")
        if effective_at is None or effective_at > current_time:
            continue
        action = WorkControlAction(str(event["action"]))
        hold_id = str(event["hold_order_id"])

        if action is WorkControlAction.HOLD:
            active = ProjectHold(
                project_id=project_id,
                hold_order_id=hold_id,
                issued_at=_event_time(event),
                effective_at=effective_at,
                expires_at=_parse_datetime(event.get("expires_at"), field="expires_at"),
                resume_policy=ResumePolicy(str(event["resume_policy"])),
                reason_code=str(event["reason_code"]),
                human_reason=str(event["human_reason"]),
                metadata=dict(event.get("metadata") or {}),
                claimed_principal=str(event["claimed_principal"]),
                authentication_ref=str(event["authentication_ref"]),
                authorization_case_id=str(event["authorization_case_id"]),
                event_id=str(event["event_id"]),
            )
            continue

        if active is None or active.hold_order_id != hold_id:
            continue

        if action is WorkControlAction.RESUME:
            active = None
            continue

        if action is WorkControlAction.EXTEND_HOLD:
            active = ProjectHold(
                project_id=project_id,
                hold_order_id=hold_id,
                issued_at=_event_time(event),
                effective_at=active.effective_at,
                expires_at=_parse_datetime(event.get("expires_at"), field="expires_at"),
                resume_policy=ResumePolicy(str(event["resume_policy"])),
                reason_code=str(event["reason_code"]),
                human_reason=str(event["human_reason"]),
                metadata={**dict(active.metadata), **dict(event.get("metadata") or {})},
                claimed_principal=str(event["claimed_principal"]),
                authentication_ref=str(event["authentication_ref"]),
                authorization_case_id=str(event["authorization_case_id"]),
                event_id=str(event["event_id"]),
            )

    if active is None:
        return ProjectWorkDecision(project_id, ProjectWorkState.ACTIVE, True, True, True, "NO_ACTIVE_HOLD")

    if active.expires_at is not None and current_time >= active.expires_at:
        if active.resume_policy is ResumePolicy.AUTO_AT_EXPIRY:
            return ProjectWorkDecision(project_id, ProjectWorkState.ACTIVE, True, True, True, "AUTO_RESUMED_AT_HOLD_EXPIRY")
        return ProjectWorkDecision(
            project_id,
            ProjectWorkState.HOLD_EXPIRED_PENDING_HUMAN_RESUME,
            False,
            False,
            False,
            "MANUAL_HOLD_EXPIRED_REQUIRES_AUTHENTICATED_RESUME",
            active,
        )

    return ProjectWorkDecision(
        project_id,
        ProjectWorkState.HOLD,
        False,
        False,
        False,
        "PROJECT_HOLD_ACTIVE",
        active,
    )


def project_is_held(project_id: str, events: Iterable[Mapping[str, Any]], *, now: datetime | None = None) -> bool:
    return resolve_project_work_state(project_id, events, now=now).state is not ProjectWorkState.ACTIVE


def filter_unheld_projects(
    project_ids: Iterable[str],
    events: Iterable[Mapping[str, Any]],
    *,
    now: datetime | None = None,
) -> list[str]:
    cached_events = list(events)
    return [
        project_id
        for project_id in project_ids
        if resolve_project_work_state(project_id, cached_events, now=now).state is ProjectWorkState.ACTIVE
    ]
