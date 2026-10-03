from dataclasses import dataclass
import re

from .project_scope import ProjectScopeError, require_project_id


SCHEMA = "org-agent-mesh/scheduled-task-route/v1"
EXECUTION_SCHEDULERS = ("AUTOMATION", "NONE_STATIC_SLACK")
DELIVERY_TRANSPORTS = ("NONE", "SLACK")
DELIVERY_EVENTS = ("START", "BLOCKER", "COMPLETE", "FAILURE", "DIGEST")
SLACK_INPUT_MODES = ("NONE", "READ_ONLY_CONTEXT", "EXPLICIT_HUMAN_APPROVAL")
_DESTINATION_RE = re.compile(r"^[CDGUW][A-Z0-9]+$")
_THREAD_RE = re.compile(r"^[0-9]+\.[0-9]+$")


class ScheduledTaskRouteError(ValueError):
    pass


@dataclass(frozen=True)
class ScheduledTaskRoute:
    project_id: str
    task_id: str
    execution_scheduler: str = "AUTOMATION"
    delivery_transport: str = "NONE"
    delivery_events: tuple[str, ...] = ("COMPLETE", "FAILURE")
    slack_workspace_id: str | None = None
    slack_destination_id: str | None = None
    slack_thread_ts: str | None = None
    slack_input_mode: str = "NONE"
    canonical_state_required_before_completion_post: bool = True
    idempotency_key: str | None = None

    def __post_init__(self):
        require_project_id(self.project_id)
        if not isinstance(self.task_id, str) or not self.task_id.strip():
            raise ScheduledTaskRouteError("task_id is required")
        if self.execution_scheduler not in EXECUTION_SCHEDULERS:
            raise ScheduledTaskRouteError("unsupported execution_scheduler")
        if self.delivery_transport not in DELIVERY_TRANSPORTS:
            raise ScheduledTaskRouteError("unsupported delivery_transport")
        if self.slack_input_mode not in SLACK_INPUT_MODES:
            raise ScheduledTaskRouteError("unsupported slack_input_mode")
        unknown = set(self.delivery_events) - set(DELIVERY_EVENTS)
        if unknown:
            raise ScheduledTaskRouteError(f"unsupported delivery events: {sorted(unknown)}")
        if len(set(self.delivery_events)) != len(self.delivery_events):
            raise ScheduledTaskRouteError("delivery_events must be unique")
        if not self.canonical_state_required_before_completion_post:
            raise ScheduledTaskRouteError("canonical state must precede completion delivery")

        if self.delivery_transport == "SLACK":
            if not self.slack_destination_id:
                raise ScheduledTaskRouteError("Slack delivery requires an explicit destination ID")
            if not _DESTINATION_RE.fullmatch(self.slack_destination_id):
                raise ScheduledTaskRouteError("invalid Slack destination ID")
        elif self.slack_destination_id or self.slack_thread_ts or self.slack_workspace_id:
            raise ScheduledTaskRouteError("Slack fields require delivery_transport=SLACK")

        if self.slack_thread_ts and not _THREAD_RE.fullmatch(self.slack_thread_ts):
            raise ScheduledTaskRouteError("invalid Slack thread timestamp")

        if self.execution_scheduler == "NONE_STATIC_SLACK" and self.delivery_transport != "SLACK":
            raise ScheduledTaskRouteError("static Slack scheduling requires Slack transport")

    def assert_project(self, expected_project_id: str):
        expected_project_id = require_project_id(expected_project_id)
        if self.project_id != expected_project_id:
            raise ProjectScopeError("Scheduled task route belongs to a foreign project")
        return True

    def event_enabled(self, event: str) -> bool:
        if event not in DELIVERY_EVENTS:
            raise ScheduledTaskRouteError("unsupported delivery event")
        return event in self.delivery_events

    def as_dict(self) -> dict:
        return {
            "schema": SCHEMA,
            "project_id": self.project_id,
            "task_id": self.task_id,
            "execution_scheduler": self.execution_scheduler,
            "delivery_transport": self.delivery_transport,
            "slack_workspace_id": self.slack_workspace_id,
            "slack_destination_id": self.slack_destination_id,
            "slack_thread_ts": self.slack_thread_ts,
            "delivery_events": list(self.delivery_events),
            "slack_input_mode": self.slack_input_mode,
            "canonical_state_required_before_completion_post": self.canonical_state_required_before_completion_post,
            "idempotency_key": self.idempotency_key,
        }
