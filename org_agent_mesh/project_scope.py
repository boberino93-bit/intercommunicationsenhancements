from dataclasses import dataclass
from pathlib import Path
import re
import uuid


class ProjectScopeError(PermissionError):
    pass


def require_project_id(project_id):
    if not isinstance(project_id, str) or not project_id.strip():
        raise ProjectScopeError("project_id is required")
    return project_id.strip()


def qualify(project_id, resource_id):
    project_id = require_project_id(project_id)
    if not isinstance(resource_id, str) or not resource_id.strip():
        raise ValueError("resource_id is required")
    safe = lambda value: re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "resource"
    return f"{safe(project_id)}::{safe(resource_id)}"


def new_instance_id(project_id, agent_id):
    return qualify(project_id, f"{agent_id}-{uuid.uuid4().hex}")


def require_same_project(requester_project_id, target_project_id, *, operation="operation"):
    requester_project_id = require_project_id(requester_project_id)
    target_project_id = require_project_id(target_project_id)
    if requester_project_id != target_project_id:
        raise ProjectScopeError(
            f"{operation} denied: requester project {requester_project_id!r} does not own target project {target_project_id!r}"
        )
    return True


def require_project_path(project_root, candidate):
    root = Path(project_root).resolve()
    target = Path(candidate).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ProjectScopeError(f"Path escapes project root: {target}") from exc
    return target


@dataclass(frozen=True)
class ProjectBinding:
    project_id: str
    repository_identity: str
    project_root: str
    agent_id: str
    agent_instance_id: str
    protocol_version: str

    def __post_init__(self):
        require_project_id(self.project_id)
        if not self.agent_id or not self.agent_instance_id:
            raise ValueError("agent_id and agent_instance_id are required")

    def assert_target(self, target_project_id, operation="operation"):
        return require_same_project(self.project_id, target_project_id, operation=operation)
