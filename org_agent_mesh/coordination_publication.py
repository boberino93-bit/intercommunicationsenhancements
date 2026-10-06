from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from .project_scope import ProjectScopeError, require_project_id, require_repository_identity

CAPABILITY = "NON_AUTHORITATIVE_COORDINATION_PUBLICATION"
LEGACY_CAPABILITY = "PUBLISH_MESSAGE"
ALLOWED_ROLES = {"PRIMARY", "MANAGER", "RESEARCH", "RESEARCHER_1", "RESEARCHER_2", "RESEARCHER_3"}
DEFAULT_GITHUB_PREFIX = "agentbus-backup/coordination-messages/"
TOKEN_FREE_AUTHORIZATION_MODE = "PROJECT_BOUND_CAPABILITY_NO_SECURITY_TOKEN"
GITHUB_CREATE_OPERATION = "CREATE_NEW_FILE"
PROHIBITED_GITHUB_OPERATIONS = {
    "UPDATE_FILE", "DELETE_FILE", "MOVE_FILE", "RENAME_FILE", "BRANCH_CREATE",
    "PULL_REQUEST_CREATE", "PULL_REQUEST_REVIEW", "PULL_REQUEST_APPROVAL",
    "WORKFLOW_RUN", "WORKFLOW_DISPATCH", "WORKFLOW_FILE_MUTATION", "CHECK_RUN",
    "RELEASE", "DEPLOYMENT", "ENVIRONMENT_APPROVAL",
}


class CoordinationPublicationError(PermissionError):
    pass


@dataclass(frozen=True)
class CoordinationRoute:
    project_id: str
    repository: str
    artifactory_namespace: str | None
    github_backup_prefix: str = DEFAULT_GITHUB_PREFIX

    def __post_init__(self) -> None:
        require_project_id(self.project_id)
        require_repository_identity(self.repository)
        _validated_prefix(self.github_backup_prefix)


@dataclass(frozen=True)
class CoordinationPublicationPermit:
    project_id: str
    role: str
    authorization_mode: str
    token_required: bool
    authority_conveyed: bool
    artifactory_allowed: bool
    github_backup_allowed: bool


def _validated_prefix(prefix: str) -> str:
    if not isinstance(prefix, str) or not prefix.strip():
        raise CoordinationPublicationError("backup prefix is required")
    raw = prefix.strip().replace("\\", "/")
    if raw.startswith("/"):
        raise CoordinationPublicationError("backup prefix must be repository-relative")
    parts = PurePosixPath(raw).parts
    if any(part in {"", ".", ".."} for part in parts):
        raise CoordinationPublicationError("backup prefix contains unsafe traversal")
    return raw.rstrip("/") + "/"


def _validated_new_file_path(path: str, prefix: str) -> str:
    if not isinstance(path, str) or not path.strip():
        raise CoordinationPublicationError("backup path is required")
    raw = path.strip().replace("\\", "/")
    if raw.startswith("/"):
        raise CoordinationPublicationError("backup path must be repository-relative")
    parts = PurePosixPath(raw).parts
    if any(part in {"", ".", ".."} for part in parts):
        raise CoordinationPublicationError("backup path contains unsafe traversal")
    normalized = "/".join(parts)
    required = _validated_prefix(prefix)
    if not normalized.startswith(required):
        raise CoordinationPublicationError("backup path is outside the coordination namespace")
    if normalized == required.rstrip("/"):
        raise CoordinationPublicationError("backup path must identify a new message file")
    return normalized


def require_coordination_publication(
    *,
    actor_project_id: str,
    actor_role: str,
    actor_capabilities,
    route: CoordinationRoute,
    target_repository: str,
    target_artifactory_namespace: str | None = None,
    github_backup_path: str | None = None,
    operation: str = "CREATE_NEW_MESSAGE",
    github_operation: str = GITHUB_CREATE_OPERATION,
    authority_conveyed: bool = False,
) -> bool:
    project_id = require_project_id(actor_project_id)
    role = str(actor_role).strip().upper()
    capabilities = frozenset(actor_capabilities or ())

    if role not in ALLOWED_ROLES:
        raise CoordinationPublicationError("role is not eligible for coordination publication")
    if CAPABILITY not in capabilities and LEGACY_CAPABILITY not in capabilities:
        raise CoordinationPublicationError("coordination publication capability is missing")
    if route.project_id != project_id:
        raise ProjectScopeError("coordination route belongs to a foreign project")
    if require_repository_identity(target_repository) != route.repository:
        raise ProjectScopeError("coordination backup repository does not match bound project")
    if operation != "CREATE_NEW_MESSAGE":
        raise CoordinationPublicationError("coordination publication is create-new-message only")
    if authority_conveyed:
        raise CoordinationPublicationError("coordination messages cannot convey authority")

    if target_artifactory_namespace is not None:
        if route.artifactory_namespace is None:
            raise CoordinationPublicationError("project has no registered Artifactory message namespace")
        if target_artifactory_namespace != route.artifactory_namespace:
            raise ProjectScopeError("Artifactory namespace does not match bound project")

    if github_backup_path is not None:
        github_operation = str(github_operation or "").strip().upper()
        if github_operation in PROHIBITED_GITHUB_OPERATIONS or github_operation != GITHUB_CREATE_OPERATION:
            raise CoordinationPublicationError("GitHub coordination lane permits create-new-file backup only")
        _validated_new_file_path(github_backup_path, route.github_backup_prefix)

    if target_artifactory_namespace is None and github_backup_path is None:
        raise CoordinationPublicationError("a registered coordination destination is required")
    return True


def issue_coordination_publication_permit(**kwargs) -> CoordinationPublicationPermit:
    require_coordination_publication(**kwargs)
    return CoordinationPublicationPermit(
        project_id=require_project_id(kwargs["actor_project_id"]),
        role=str(kwargs["actor_role"]).strip().upper(),
        authorization_mode=TOKEN_FREE_AUTHORIZATION_MODE,
        token_required=False,
        authority_conveyed=False,
        artifactory_allowed=kwargs.get("target_artifactory_namespace") is not None,
        github_backup_allowed=kwargs.get("github_backup_path") is not None,
    )
