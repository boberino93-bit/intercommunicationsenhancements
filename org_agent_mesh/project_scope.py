from dataclasses import dataclass
from pathlib import Path
import re
import uuid

from .constants import CAPABILITIES


class ProjectScopeError(PermissionError):
    pass


_PROJECT_ID_RE = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9])?$")
_RESOURCE_ID_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]{0,254}[A-Za-z0-9])?$")
_REPOSITORY_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def require_project_id(project_id):
    if not isinstance(project_id, str):
        raise ProjectScopeError("project_id is required")
    value = project_id.strip()
    if not value or not _PROJECT_ID_RE.fullmatch(value):
        raise ProjectScopeError(
            "project_id must be a canonical lowercase identifier using only a-z, 0-9, '.', '_' or '-'"
        )
    return value


def require_resource_id(resource_id, *, field="resource_id"):
    if not isinstance(resource_id, str):
        raise ValueError(f"{field} is required")
    value = resource_id.strip()
    if not value or not _RESOURCE_ID_RE.fullmatch(value):
        raise ValueError(
            f"{field} must be a canonical identifier using only letters, digits, '.', '_' or '-'"
        )
    return value


def require_repository_identity(repository_identity):
    if not isinstance(repository_identity, str):
        raise ProjectScopeError("repository_identity is required")
    value = repository_identity.strip()
    if not _REPOSITORY_ID_RE.fullmatch(value):
        raise ProjectScopeError("repository_identity must use canonical owner/repository form")
    return value


def qualify(project_id, resource_id):
    """Create an injective project-qualified key without lossy sanitization."""
    project_id = require_project_id(project_id)
    resource_id = require_resource_id(resource_id)
    return f"{project_id}::{resource_id}"


def new_instance_id(project_id, agent_id):
    project_id = require_project_id(project_id)
    agent_id = require_resource_id(agent_id, field="agent_id")
    return f"{project_id}--{agent_id}-{uuid.uuid4().hex}"


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
    target = Path(candidate)
    if not target.is_absolute():
        target = root / target
    target = target.resolve()
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
    capabilities: tuple[str, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "project_id", require_project_id(self.project_id))
        object.__setattr__(
            self, "repository_identity", require_repository_identity(self.repository_identity)
        )
        if not isinstance(self.project_root, str) or not self.project_root.strip():
            raise ValueError("project_root is required")
        object.__setattr__(self, "agent_id", require_resource_id(self.agent_id, field="agent_id"))
        if not isinstance(self.agent_instance_id, str) or not self.agent_instance_id.strip():
            raise ValueError("agent_instance_id is required")
        if not isinstance(self.protocol_version, str) or not self.protocol_version.strip():
            raise ValueError("protocol_version is required")
        unknown = set(self.capabilities) - set(CAPABILITIES)
        if unknown:
            raise ProjectScopeError(f"Unknown capabilities: {sorted(unknown)}")
        object.__setattr__(self, "capabilities", tuple(sorted(set(self.capabilities))))

    def assert_target(self, target_project_id, operation="operation"):
        return require_same_project(self.project_id, target_project_id, operation=operation)

    def assert_capability(self, capability):
        if capability not in CAPABILITIES:
            raise ProjectScopeError(f"Unknown capability: {capability}")
        if capability not in self.capabilities:
            raise ProjectScopeError(
                f"Capability {capability!r} is not granted to agent {self.agent_id!r}"
            )
        return True
