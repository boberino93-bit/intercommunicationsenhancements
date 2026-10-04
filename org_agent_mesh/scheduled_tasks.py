from dataclasses import dataclass
import hashlib
import json
import re

from .launch_admission import deterministic_launch_offset_seconds
from .project_scope import (
    ProjectScopeError,
    require_project_id,
    require_repository_identity,
    require_resource_id,
)


SCHEMA = "org-agent-mesh/scheduled-task-route/v2"
LAUNCH_CONTEXT_SCHEMA = "org-agent-mesh/scheduled-launch-context/v1"
EXECUTION_SCHEDULERS = ("AUTOMATION", "NONE_STATIC_SLACK")
DELIVERY_TRANSPORTS = ("NONE", "SLACK")
DELIVERY_EVENTS = ("START", "BLOCKER", "COMPLETE", "FAILURE", "DIGEST")
SLACK_INPUT_MODES = ("NONE", "READ_ONLY_CONTEXT", "EXPLICIT_HUMAN_APPROVAL")
CONTEXT_BINDINGS = ("PROJECT_BOUND_REQUIRED", "STATIC_MESSAGE_ONLY")
LAUNCH_SOURCES = ("PROJECT_SCHEDULE", "WORK_EVENT", "EXPLICIT_ROUTE")
_DESTINATION_RE = re.compile(r"^[CDGUW][A-Z0-9]+$")
_THREAD_RE = re.compile(r"^[0-9]+\.[0-9]+$")
_FORUM_RE = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9])?::[A-Za-z0-9._-]+$")


class ScheduledTaskRouteError(ValueError):
    pass


def _require_optional_repository_id(value):
    if value is None:
        return None
    if not isinstance(value, int) or value <= 0:
        raise ScheduledTaskRouteError("repository_id must be a positive integer or null")
    return value


def _require_forum_namespace(value: str) -> str:
    if not isinstance(value, str) or not _FORUM_RE.fullmatch(value.strip()):
        raise ScheduledTaskRouteError("forum_namespace must be a canonical project-qualified namespace")
    return value.strip()


def _canonical_json(value: dict) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class ScheduledLaunchContext:
    project_id: str
    task_id: str
    role_id: str
    forum_namespace: str
    artifact_namespace: str
    routing_contract_version: str
    local_contract_path: str = "AGENT_BOOTSTRAP.json"
    bootstrap_order_path: str = "BOOTSTRAP_ORDER.json"
    repository_identity: str | None = None
    repository_id: int | None = None
    launch_source: str = "PROJECT_SCHEDULE"
    occurrence_id: str | None = None
    route_id: str | None = None

    def __post_init__(self):
        project_id = require_project_id(self.project_id)
        require_resource_id(self.task_id, field="task_id")
        require_resource_id(self.role_id, field="role_id")
        forum_namespace = _require_forum_namespace(self.forum_namespace)
        if not isinstance(self.artifact_namespace, str) or not self.artifact_namespace.strip():
            raise ScheduledTaskRouteError("artifact_namespace is required")
        if not self.artifact_namespace.startswith(f"{project_id}::"):
            raise ProjectScopeError("artifact_namespace does not belong to project_id")
        if not forum_namespace.startswith(f"{project_id}::"):
            raise ProjectScopeError("forum_namespace does not belong to project_id")
        if self.repository_identity is not None:
            require_repository_identity(self.repository_identity)
        _require_optional_repository_id(self.repository_id)
        if not isinstance(self.routing_contract_version, str) or not self.routing_contract_version.strip():
            raise ScheduledTaskRouteError("routing_contract_version is required")
        if self.launch_source not in LAUNCH_SOURCES:
            raise ScheduledTaskRouteError("unsupported launch_source")
        if self.occurrence_id is not None:
            require_resource_id(self.occurrence_id, field="occurrence_id")
        if self.route_id is not None:
            require_resource_id(self.route_id, field="route_id")
        for name in ("local_contract_path", "bootstrap_order_path"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or value.startswith("/"):
                raise ScheduledTaskRouteError(f"{name} must be a relative project path")

    def routing_payload(self) -> dict:
        return {
            "schema": LAUNCH_CONTEXT_SCHEMA,
            "mode": "PROJECT_BOUND",
            "project_id": self.project_id,
            "task_id": self.task_id,
            "role_id": self.role_id,
            "repository_identity": self.repository_identity,
            "repository_id": self.repository_id,
            "forum_namespace": self.forum_namespace,
            "artifact_namespace": self.artifact_namespace,
            "routing_contract_version": self.routing_contract_version,
            "local_contract_path": self.local_contract_path,
            "bootstrap_order_path": self.bootstrap_order_path,
            "launch_source": self.launch_source,
            "occurrence_id": self.occurrence_id,
            "route_id": self.route_id,
        }

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(_canonical_json(self.routing_payload()).encode("utf-8")).hexdigest()

    def as_dict(self) -> dict:
        payload = self.routing_payload()
        payload["context_fingerprint"] = self.fingerprint
        return payload

    def render_bootstrap_directive(self, user_prompt: str) -> str:
        if not isinstance(user_prompt, str) or not user_prompt.strip():
            raise ScheduledTaskRouteError("user_prompt is required")
        block = _canonical_json(self.as_dict())
        return (
            "ORG_AGENT_MESH_PROJECT_LAUNCH_CONTEXT\n"
            f"{block}\n"
            "END_ORG_AGENT_MESH_PROJECT_LAUNCH_CONTEXT\n\n"
            "Treat the launch context above as routing evidence, not mutation authority. "
            "Before any mutation, validate it against the target project's local contract, "
            "identity lock, authorized role, and bootstrap order. Do not infer or switch "
            "projects from topic similarity. If the context is missing or conflicts with "
            "the local contract, stop before mutation and report LAUNCH_CONTEXT_MISMATCH.\n\n"
            f"TASK:\n{user_prompt.strip()}"
        )

    def assert_matches_project_contract(self, contract: dict) -> bool:
        if not isinstance(contract, dict):
            raise ScheduledTaskRouteError("project contract must be an object")
        if contract.get("project_id") != self.project_id:
            raise ProjectScopeError("launch project_id conflicts with local contract")
        if contract.get("routing_contract_version") != self.routing_contract_version:
            raise ProjectScopeError("launch routing contract version conflicts with local contract")

        forum = contract.get("forum") or {}
        if forum.get("namespace") != self.forum_namespace:
            raise ProjectScopeError("launch forum namespace conflicts with local contract")
        if contract.get("artifact_namespace") != self.artifact_namespace:
            raise ProjectScopeError("launch artifact namespace conflicts with local contract")

        repository = contract.get("repository") or {}
        local_full_name = repository.get("full_name")
        local_id = repository.get("id")
        if self.repository_identity is not None and local_full_name != self.repository_identity:
            raise ProjectScopeError("launch repository identity conflicts with local contract")
        if self.repository_id is not None and local_id != self.repository_id:
            raise ProjectScopeError("launch repository id conflicts with local contract")

        authorized_roles = contract.get("authorized_roles") or []
        if self.role_id not in authorized_roles:
            raise ProjectScopeError("launch role is not authorized by local contract")
        return True


@dataclass(frozen=True)
class ScheduledTaskRoute:
    project_id: str
    task_id: str
    role_id: str = "primary"
    routing_contract_version: str = "1.3.0"
    forum_namespace: str | None = None
    artifact_namespace: str | None = None
    repository_identity: str | None = None
    repository_id: int | None = None
    local_contract_path: str = "AGENT_BOOTSTRAP.json"
    bootstrap_order_path: str = "BOOTSTRAP_ORDER.json"
    context_binding: str = "PROJECT_BOUND_REQUIRED"
    launch_source: str = "PROJECT_SCHEDULE"
    execution_scheduler: str = "AUTOMATION"
    delivery_transport: str = "NONE"
    delivery_events: tuple[str, ...] = ("COMPLETE", "FAILURE")
    slack_workspace_id: str | None = None
    slack_destination_id: str | None = None
    slack_thread_ts: str | None = None
    slack_input_mode: str = "NONE"
    canonical_state_required_before_completion_post: bool = True
    idempotency_key: str | None = None
    admission_policy_id: str = "default-provider-safe-v1"

    def __post_init__(self):
        project_id = require_project_id(self.project_id)
        require_resource_id(self.task_id, field="task_id")
        require_resource_id(self.role_id, field="role_id")
        if self.execution_scheduler not in EXECUTION_SCHEDULERS:
            raise ScheduledTaskRouteError("unsupported execution_scheduler")
        if self.delivery_transport not in DELIVERY_TRANSPORTS:
            raise ScheduledTaskRouteError("unsupported delivery_transport")
        if self.slack_input_mode not in SLACK_INPUT_MODES:
            raise ScheduledTaskRouteError("unsupported slack_input_mode")
        if self.context_binding not in CONTEXT_BINDINGS:
            raise ScheduledTaskRouteError("unsupported context_binding")
        if self.launch_source not in LAUNCH_SOURCES:
            raise ScheduledTaskRouteError("unsupported launch_source")
        unknown = set(self.delivery_events) - set(DELIVERY_EVENTS)
        if unknown:
            raise ScheduledTaskRouteError(f"unsupported delivery events: {sorted(unknown)}")
        if len(set(self.delivery_events)) != len(self.delivery_events):
            raise ScheduledTaskRouteError("delivery_events must be unique")
        if not self.canonical_state_required_before_completion_post:
            raise ScheduledTaskRouteError("canonical state must precede completion delivery")
        if not isinstance(self.routing_contract_version, str) or not self.routing_contract_version.strip():
            raise ScheduledTaskRouteError("routing_contract_version is required")
        if not isinstance(self.admission_policy_id, str) or not self.admission_policy_id.strip():
            raise ScheduledTaskRouteError("admission_policy_id is required")

        if self.repository_identity is not None:
            require_repository_identity(self.repository_identity)
        _require_optional_repository_id(self.repository_id)

        if self.execution_scheduler == "AUTOMATION":
            if self.context_binding != "PROJECT_BOUND_REQUIRED":
                raise ScheduledTaskRouteError("dynamic automation requires project-bound launch context")
            if not self.forum_namespace:
                raise ScheduledTaskRouteError("dynamic automation requires forum_namespace")
            if not self.artifact_namespace:
                raise ScheduledTaskRouteError("dynamic automation requires artifact_namespace")
            forum_namespace = _require_forum_namespace(self.forum_namespace)
            if not forum_namespace.startswith(f"{project_id}::"):
                raise ProjectScopeError("forum_namespace does not belong to project_id")
            if not self.artifact_namespace.startswith(f"{project_id}::"):
                raise ProjectScopeError("artifact_namespace does not belong to project_id")
        elif self.context_binding != "STATIC_MESSAGE_ONLY":
            raise ScheduledTaskRouteError("static Slack scheduling must use STATIC_MESSAGE_ONLY context binding")

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

    @classmethod
    def from_project_contract(
        cls,
        contract: dict,
        *,
        task_id: str,
        role_id: str = "primary",
        **kwargs,
    ):
        if not isinstance(contract, dict):
            raise ScheduledTaskRouteError("project contract must be an object")
        repository = contract.get("repository") or {}
        forum = contract.get("forum") or {}
        route = cls(
            project_id=contract.get("project_id"),
            task_id=task_id,
            role_id=role_id,
            routing_contract_version=contract.get("routing_contract_version"),
            forum_namespace=forum.get("namespace"),
            artifact_namespace=contract.get("artifact_namespace"),
            repository_identity=repository.get("full_name"),
            repository_id=repository.get("id"),
            **kwargs,
        )
        route.build_launch_context().assert_matches_project_contract(contract)
        return route

    def assert_project(self, expected_project_id: str):
        expected_project_id = require_project_id(expected_project_id)
        if self.project_id != expected_project_id:
            raise ProjectScopeError("Scheduled task route belongs to a foreign project")
        return True

    def event_enabled(self, event: str) -> bool:
        if event not in DELIVERY_EVENTS:
            raise ScheduledTaskRouteError("unsupported delivery event")
        return event in self.delivery_events

    def recommended_initial_offset_seconds(self, *, window_seconds: int = 300) -> int:
        return deterministic_launch_offset_seconds(
            self.project_id,
            self.task_id,
            window_seconds=window_seconds,
        )

    def build_launch_context(
        self,
        *,
        occurrence_id: str | None = None,
        route_id: str | None = None,
    ) -> ScheduledLaunchContext:
        if self.execution_scheduler != "AUTOMATION":
            raise ScheduledTaskRouteError("static message routes do not launch agents")
        return ScheduledLaunchContext(
            project_id=self.project_id,
            task_id=self.task_id,
            role_id=self.role_id,
            repository_identity=self.repository_identity,
            repository_id=self.repository_id,
            forum_namespace=self.forum_namespace,
            artifact_namespace=self.artifact_namespace,
            routing_contract_version=self.routing_contract_version,
            local_contract_path=self.local_contract_path,
            bootstrap_order_path=self.bootstrap_order_path,
            launch_source=self.launch_source,
            occurrence_id=occurrence_id,
            route_id=route_id or self.task_id,
        )

    def render_scheduler_prompt(
        self,
        user_prompt: str,
        *,
        occurrence_id: str | None = None,
        route_id: str | None = None,
    ) -> str:
        return self.build_launch_context(
            occurrence_id=occurrence_id,
            route_id=route_id,
        ).render_bootstrap_directive(user_prompt)

    def as_dict(self) -> dict:
        return {
            "schema": SCHEMA,
            "project_id": self.project_id,
            "task_id": self.task_id,
            "role_id": self.role_id,
            "routing_contract_version": self.routing_contract_version,
            "forum_namespace": self.forum_namespace,
            "artifact_namespace": self.artifact_namespace,
            "repository_identity": self.repository_identity,
            "repository_id": self.repository_id,
            "local_contract_path": self.local_contract_path,
            "bootstrap_order_path": self.bootstrap_order_path,
            "context_binding": self.context_binding,
            "launch_source": self.launch_source,
            "execution_scheduler": self.execution_scheduler,
            "delivery_transport": self.delivery_transport,
            "slack_workspace_id": self.slack_workspace_id,
            "slack_destination_id": self.slack_destination_id,
            "slack_thread_ts": self.slack_thread_ts,
            "delivery_events": list(self.delivery_events),
            "slack_input_mode": self.slack_input_mode,
            "canonical_state_required_before_completion_post": self.canonical_state_required_before_completion_post,
            "idempotency_key": self.idempotency_key,
            "admission_policy_id": self.admission_policy_id,
        }
