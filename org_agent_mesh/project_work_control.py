from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Mapping


EVENT_SCHEMA = "org-agent-mesh/project-work-control-event/v1"
VALID_ACTIONS = {"HOLD", "EXTEND_HOLD", "RESUME"}
VALID_RESUME_POLICIES = {"MANUAL", "AUTO_AT_EXPIRY"}
VALID_DERIVED_STATES = {"ACTIVE", "HOLD", "HOLD_EXPIRED_PENDING_HUMAN_RESUME"}


class ProjectWorkControlError(ValueError):
    """Raised when project work-control state cannot be derived safely."""


@dataclass(frozen=True)
class WorkControlEvent:
    event_id: str
    project_id: str
    action: str
    hold_order_id: str
    issued_at: datetime
    effective_at: datetime
    expires_at: datetime | None
    resume_policy: str
    reason_code: str
    human_reason: str
    metadata: Mapping[str, Any]
    claimed_principal: str
    authentication_ref: str
    authorization_case_id: str
    preserve_partial_state: bool
    source_revision: str | None = None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "WorkControlEvent":
        if not isinstance(payload, Mapping):
            raise ProjectWorkControlError("event_payload_must_be_object")
        if payload.get("schema") != EVENT_SCHEMA:
            raise ProjectWorkControlError("unsupported_event_schema")

        def require_text(name: str) -> str:
            value = payload.get(name)
            if not isinstance(value, str) or not value.strip():
                raise ProjectWorkControlError(f"invalid_{name}")
            return value

        action = require_text("action")
        if action not in VALID_ACTIONS:
            raise ProjectWorkControlError("unsupported_action")
        resume_policy = require_text("resume_policy")
        if resume_policy not in VALID_RESUME_POLICIES:
            raise ProjectWorkControlError("unsupported_resume_policy")
        if payload.get("preserve_partial_state") is not True:
            raise ProjectWorkControlError("preserve_partial_state_must_be_true")

        metadata = payload.get("metadata")
        if not isinstance(metadata, Mapping):
            raise ProjectWorkControlError("metadata_must_be_object")

        issued_at = _parse_time(payload.get("issued_at"), "issued_at")
        effective_at = _parse_time(payload.get("effective_at"), "effective_at")
        expires_raw = payload.get("expires_at")
        expires_at = None if expires_raw is None else _parse_time(expires_raw, "expires_at")
        if expires_at is not None and expires_at <= effective_at:
            raise ProjectWorkControlError("expires_at_must_be_after_effective_at")

        return cls(
            event_id=require_text("event_id"),
            project_id=require_text("project_id"),
            action=action,
            hold_order_id=require_text("hold_order_id"),
            issued_at=issued_at,
            effective_at=effective_at,
            expires_at=expires_at,
            resume_policy=resume_policy,
            reason_code=require_text("reason_code"),
            human_reason=payload.get("human_reason") if isinstance(payload.get("human_reason"), str) else "",
            metadata=dict(metadata),
            claimed_principal=require_text("claimed_principal"),
            authentication_ref=require_text("authentication_ref"),
            authorization_case_id=require_text("authorization_case_id"),
            preserve_partial_state=True,
            source_revision=payload.get("source_revision") if isinstance(payload.get("source_revision"), str) else None,
        )


@dataclass(frozen=True)
class ProjectWorkState:
    project_id: str
    state: str
    active_hold_order_id: str | None = None
    source_event_id: str | None = None
    effective_at: datetime | None = None
    expires_at: datetime | None = None
    resume_policy: str | None = None
    reason_code: str | None = None
    human_reason: str = ""
    metadata: Mapping[str, Any] | None = None
    mutation_blocked_pending_verification: bool = False
    unverified_hold_event_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.state not in VALID_DERIVED_STATES:
            raise ProjectWorkControlError("invalid_derived_state")

    @property
    def project_work_allowed(self) -> bool:
        return self.state == "ACTIVE"

    @property
    def respawn_allowed(self) -> bool:
        return self.state == "ACTIVE"

    @property
    def new_mutation_allowed_by_hold_state(self) -> bool:
        return self.state == "ACTIVE" and not self.mutation_blocked_pending_verification


def _parse_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ProjectWorkControlError(f"invalid_{field}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProjectWorkControlError(f"invalid_{field}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ProjectWorkControlError(f"{field}_must_be_offset_aware")
    return parsed


def _validate_registry(registry: Mapping[str, Any], project_id: str) -> Mapping[str, Any]:
    if registry.get("schema") != "org-agent-mesh/project-work-control/v1":
        raise ProjectWorkControlError("unsupported_registry_schema")
    projects = registry.get("projects")
    if not isinstance(projects, Mapping):
        raise ProjectWorkControlError("missing_registry_projects")
    project = projects.get(project_id)
    if not isinstance(project, Mapping):
        raise ProjectWorkControlError("unknown_project")
    state = project.get("state")
    if state not in {"ACTIVE", "HOLD", "HOLD_EXPIRED_PENDING_HUMAN_RESUME"}:
        raise ProjectWorkControlError("invalid_registry_project_state")
    return project


def derive_project_work_state(
    registry: Mapping[str, Any],
    events: Iterable[WorkControlEvent | Mapping[str, Any]],
    *,
    project_id: str,
    now: datetime,
    validated_event_ids: Iterable[str] = (),
) -> ProjectWorkState:
    """Derive the current work state from the canonical projection plus append-only events.

    Only event IDs explicitly supplied in ``validated_event_ids`` may change authoritative
    project state. Unvalidated effective HOLD signals do not become authoritative holds, but
    they set ``mutation_blocked_pending_verification`` so callers can fail closed on new
    mutation while authenticating the signal.
    """

    if now.tzinfo is None or now.utcoffset() is None:
        raise ProjectWorkControlError("now_must_be_offset_aware")
    project = _validate_registry(registry, project_id)
    validated = set(validated_event_ids)

    parsed: list[WorkControlEvent] = []
    for item in events:
        event = item if isinstance(item, WorkControlEvent) else WorkControlEvent.from_dict(item)
        if event.project_id == project_id and event.effective_at <= now:
            parsed.append(event)

    parsed.sort(key=lambda event: (event.effective_at, event.issued_at, event.event_id))

    unverified_holds = tuple(
        event.event_id
        for event in parsed
        if event.action in {"HOLD", "EXTEND_HOLD"} and event.event_id not in validated
    )
    authoritative = [event for event in parsed if event.event_id in validated]

    base_state = project.get("state")
    active = _state_from_registry_projection(project_id, project)

    # Replay validated append-only events over the current projection. A projection may
    # already include an active hold; matching future events can extend/resume it.
    for event in authoritative:
        if event.action == "HOLD":
            active = ProjectWorkState(
                project_id=project_id,
                state="HOLD",
                active_hold_order_id=event.hold_order_id,
                source_event_id=event.event_id,
                effective_at=event.effective_at,
                expires_at=event.expires_at,
                resume_policy=event.resume_policy,
                reason_code=event.reason_code,
                human_reason=event.human_reason,
                metadata=dict(event.metadata),
            )
            continue

        if event.action == "EXTEND_HOLD":
            if active.active_hold_order_id != event.hold_order_id or active.state not in {
                "HOLD",
                "HOLD_EXPIRED_PENDING_HUMAN_RESUME",
            }:
                raise ProjectWorkControlError("extend_hold_does_not_match_active_hold")
            active = ProjectWorkState(
                project_id=project_id,
                state="HOLD",
                active_hold_order_id=event.hold_order_id,
                source_event_id=event.event_id,
                effective_at=active.effective_at or event.effective_at,
                expires_at=event.expires_at,
                resume_policy=event.resume_policy,
                reason_code=event.reason_code,
                human_reason=event.human_reason,
                metadata=dict(event.metadata),
            )
            continue

        if event.action == "RESUME":
            if active.active_hold_order_id != event.hold_order_id or active.state not in {
                "HOLD",
                "HOLD_EXPIRED_PENDING_HUMAN_RESUME",
            }:
                raise ProjectWorkControlError("resume_does_not_match_active_hold")
            active = ProjectWorkState(
                project_id=project_id,
                state="ACTIVE",
                source_event_id=event.event_id,
            )

    # Expiry changes derived state but never creates mutation authority or enables a task.
    if active.state == "HOLD" and active.expires_at is not None and now >= active.expires_at:
        if active.resume_policy == "AUTO_AT_EXPIRY":
            active = ProjectWorkState(
                project_id=project_id,
                state="ACTIVE",
                source_event_id=active.source_event_id,
            )
        else:
            active = ProjectWorkState(
                project_id=project_id,
                state="HOLD_EXPIRED_PENDING_HUMAN_RESUME",
                active_hold_order_id=active.active_hold_order_id,
                source_event_id=active.source_event_id,
                effective_at=active.effective_at,
                expires_at=active.expires_at,
                resume_policy=active.resume_policy,
                reason_code=active.reason_code,
                human_reason=active.human_reason,
                metadata=active.metadata,
            )

    # An unverified hold signal blocks only new mutation while verification is pending.
    if unverified_holds:
        active = ProjectWorkState(
            project_id=active.project_id,
            state=active.state,
            active_hold_order_id=active.active_hold_order_id,
            source_event_id=active.source_event_id,
            effective_at=active.effective_at,
            expires_at=active.expires_at,
            resume_policy=active.resume_policy,
            reason_code=active.reason_code,
            human_reason=active.human_reason,
            metadata=active.metadata,
            mutation_blocked_pending_verification=True,
            unverified_hold_event_ids=unverified_holds,
        )

    # Keep this explicit so accidental future changes to the projection cannot be ignored.
    if base_state != project.get("state"):
        raise ProjectWorkControlError("registry_projection_changed_during_derivation")
    return active


def _state_from_registry_projection(project_id: str, project: Mapping[str, Any]) -> ProjectWorkState:
    state = project.get("state")
    hold = project.get("active_hold")
    if state == "ACTIVE":
        return ProjectWorkState(project_id=project_id, state="ACTIVE")
    if not isinstance(hold, Mapping):
        raise ProjectWorkControlError("held_registry_project_missing_active_hold")
    order_id = hold.get("hold_order_id")
    if not isinstance(order_id, str) or not order_id:
        raise ProjectWorkControlError("invalid_registry_hold_order_id")
    expires_at = None
    if hold.get("expires_at") is not None:
        expires_at = _parse_time(hold.get("expires_at"), "registry_expires_at")
    effective_at = None
    if hold.get("effective_at") is not None:
        effective_at = _parse_time(hold.get("effective_at"), "registry_effective_at")
    resume_policy = hold.get("resume_policy")
    if resume_policy not in VALID_RESUME_POLICIES:
        raise ProjectWorkControlError("invalid_registry_resume_policy")
    return ProjectWorkState(
        project_id=project_id,
        state=state,
        active_hold_order_id=order_id,
        source_event_id=hold.get("source_event_id") if isinstance(hold.get("source_event_id"), str) else None,
        effective_at=effective_at,
        expires_at=expires_at,
        resume_policy=resume_policy,
        reason_code=hold.get("reason_code") if isinstance(hold.get("reason_code"), str) else None,
        human_reason=hold.get("human_reason") if isinstance(hold.get("human_reason"), str) else "",
        metadata=dict(hold.get("metadata")) if isinstance(hold.get("metadata"), Mapping) else {},
    )


def require_project_work_allowed(state: ProjectWorkState) -> None:
    if not state.project_work_allowed:
        raise ProjectWorkControlError(f"project_work_blocked:{state.state}")


def require_new_mutation_allowed_by_hold_state(state: ProjectWorkState) -> None:
    if not state.new_mutation_allowed_by_hold_state:
        reason = state.state
        if state.mutation_blocked_pending_verification:
            reason = "UNVERIFIED_HOLD_SIGNAL"
        raise ProjectWorkControlError(f"project_mutation_blocked:{reason}")
