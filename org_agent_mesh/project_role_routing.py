from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Mapping


class RoutingError(ValueError):
    """Raised when project/role/repository routing cannot be resolved safely."""


@dataclass(frozen=True)
class ResolvedRoute:
    project_id: str
    role_id: str
    repository: str
    repository_id: int | None
    forum_namespace: str
    forum_authority: str
    forum_repository_view_mode: str
    forum_repository_view_path: str | None
    artifact_namespace: str
    handoff_paths: tuple[str, ...]
    local_contract_path: str | None
    routing_contract_version: str | None

    def acknowledgement(self, state_ref: str = "unresolved") -> str:
        return (
            f"IDENTITY RESOLVED: project={self.project_id}; role={self.role_id}; "
            f"forum={self.forum_namespace}; repositories={self.repository}; state={state_ref}"
        )


def _safe_repo_path(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise RoutingError(f"invalid_{field}")
    if "\\" in value:
        raise RoutingError(f"unsafe_{field}")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise RoutingError(f"unsafe_{field}")
    return value


def _validate_forum_locator(project: Mapping[str, Any], *, project_id: str) -> None:
    namespace = project.get("forum_namespace")
    locator = project.get("forum_locator")
    if not isinstance(locator, Mapping):
        raise RoutingError("missing_forum_locator")
    if locator.get("authority") != "INTERNAL_ARTIFACTORY":
        raise RoutingError("invalid_forum_authority")
    if locator.get("namespace") != namespace:
        raise RoutingError("forum_locator_namespace_mismatch")

    view = locator.get("repository_view")
    if not isinstance(view, Mapping):
        raise RoutingError("missing_forum_repository_view")
    mode = view.get("mode")
    path = view.get("path")
    if mode not in {"LIVE_MIRROR", "SNAPSHOT_BACKUP", "NONE"}:
        raise RoutingError("invalid_forum_repository_view_mode")
    if mode == "NONE":
        if path is not None:
            raise RoutingError("forum_repository_view_path_must_be_null")
    else:
        _safe_repo_path(path, field="forum_repository_view_path")


def validate_registry(registry: Mapping[str, Any]) -> None:
    if registry.get("mode") != "FAIL_CLOSED":
        raise RoutingError("registry_not_fail_closed")
    if registry.get("schema") != "org-agent-mesh/project-role-routing-registry/v1":
        raise RoutingError("unsupported_registry_schema")

    projects = registry.get("projects")
    if not isinstance(projects, Mapping) or not projects:
        raise RoutingError("missing_projects")

    seen_repositories: set[str] = set()
    seen_repository_ids: set[int] = set()
    seen_forums: set[str] = set()
    seen_artifacts: set[str] = set()

    for project_id, project in projects.items():
        if not isinstance(project_id, str) or not project_id:
            raise RoutingError("invalid_project_id")
        if not isinstance(project, Mapping):
            raise RoutingError("invalid_project_entry")

        repository = project.get("repository")
        if not isinstance(repository, str) or not repository or repository.count("/") != 1:
            raise RoutingError("missing_repository")
        if repository in seen_repositories:
            raise RoutingError("duplicate_repository_binding")
        seen_repositories.add(repository)

        repository_id = project.get("repository_id")
        if repository_id is not None:
            if not isinstance(repository_id, int) or isinstance(repository_id, bool) or repository_id <= 0:
                raise RoutingError("invalid_repository_id")
            if repository_id in seen_repository_ids:
                raise RoutingError("duplicate_repository_id_binding")
            seen_repository_ids.add(repository_id)

        roles = project.get("roles")
        if (
            not isinstance(roles, list)
            or not roles
            or not all(isinstance(role, str) and role for role in roles)
            or len(set(roles)) != len(roles)
        ):
            raise RoutingError("invalid_roles")

        forum = project.get("forum_namespace")
        if not isinstance(forum, str) or not forum:
            raise RoutingError("missing_forum_namespace")
        if forum in seen_forums:
            raise RoutingError("duplicate_forum_namespace")
        seen_forums.add(forum)
        _validate_forum_locator(project, project_id=project_id)

        artifact = project.get("artifact_namespace")
        if not isinstance(artifact, str) or not artifact:
            raise RoutingError("missing_artifact_namespace")
        if artifact in seen_artifacts:
            raise RoutingError("duplicate_artifact_namespace")
        seen_artifacts.add(artifact)

        handoff = project.get("handoff_paths")
        if not isinstance(handoff, list) or not handoff:
            raise RoutingError("missing_handoff_paths")
        for handoff_path in handoff:
            _safe_repo_path(handoff_path, field="handoff_path")

        local_contract_path = project.get("local_contract_path")
        if local_contract_path is not None:
            _safe_repo_path(local_contract_path, field="local_contract_path")

        contract_version = project.get("routing_contract_version")
        if contract_version is not None and (not isinstance(contract_version, str) or not contract_version):
            raise RoutingError("invalid_routing_contract_version")


def validate_local_contract(
    registry: Mapping[str, Any],
    *,
    project_id: str,
    contract: Mapping[str, Any],
) -> None:
    validate_registry(registry)
    project = registry["projects"].get(project_id)
    if not isinstance(project, Mapping):
        raise RoutingError("unknown_project")

    if contract.get("schema") != "org-agent-mesh/local-agent-bootstrap/v1":
        raise RoutingError("unsupported_local_contract_schema")
    if contract.get("mode") != "FAIL_CLOSED":
        raise RoutingError("local_contract_not_fail_closed")
    if contract.get("project_id") != project_id:
        raise RoutingError("local_contract_project_mismatch")
    if contract.get("routing_contract_version") != project.get("routing_contract_version"):
        raise RoutingError("local_contract_version_mismatch")

    repository = contract.get("repository")
    if not isinstance(repository, Mapping):
        raise RoutingError("invalid_local_repository")
    if repository.get("full_name") != project.get("repository"):
        raise RoutingError("local_contract_repository_mismatch")
    expected_repository_id = project.get("repository_id")
    if expected_repository_id is not None and repository.get("id") != expected_repository_id:
        raise RoutingError("local_contract_repository_id_mismatch")

    forum = contract.get("forum")
    locator = project.get("forum_locator")
    if not isinstance(forum, Mapping):
        raise RoutingError("local_contract_forum_mismatch")
    if forum.get("namespace") != project.get("forum_namespace"):
        raise RoutingError("local_contract_forum_mismatch")
    if forum.get("authority") != locator.get("authority"):
        raise RoutingError("local_contract_forum_authority_mismatch")
    if forum.get("repository_view") != locator.get("repository_view"):
        raise RoutingError("local_contract_forum_repository_view_mismatch")

    if contract.get("artifact_namespace") != project.get("artifact_namespace"):
        raise RoutingError("local_contract_artifact_namespace_mismatch")
    if contract.get("handoff_paths") != project.get("handoff_paths"):
        raise RoutingError("local_contract_handoff_mismatch")
    if contract.get("authorized_roles") != project.get("roles"):
        raise RoutingError("local_contract_roles_mismatch")


def resolve_route(
    registry: Mapping[str, Any],
    *,
    project_id: str,
    role_id: str,
    current_repository: str,
    current_repository_id: int | None = None,
) -> ResolvedRoute:
    validate_registry(registry)

    projects = registry["projects"]
    if project_id not in projects:
        raise RoutingError("unknown_project")

    project = projects[project_id]
    roles = project["roles"]
    if role_id not in roles:
        raise RoutingError("unknown_or_unauthorized_role")

    repository = project["repository"]
    if current_repository != repository:
        raise RoutingError("repository_identity_mismatch")

    repository_id = project.get("repository_id")
    if current_repository_id is not None:
        if repository_id is None:
            raise RoutingError("registry_missing_repository_id")
        if current_repository_id != repository_id:
            raise RoutingError("repository_stable_id_mismatch")

    forum_locator = project["forum_locator"]
    repository_view = forum_locator["repository_view"]
    return ResolvedRoute(
        project_id=project_id,
        role_id=role_id,
        repository=repository,
        repository_id=repository_id,
        forum_namespace=project["forum_namespace"],
        forum_authority=forum_locator["authority"],
        forum_repository_view_mode=repository_view["mode"],
        forum_repository_view_path=repository_view["path"],
        artifact_namespace=project["artifact_namespace"],
        handoff_paths=tuple(project["handoff_paths"]),
        local_contract_path=project.get("local_contract_path"),
        routing_contract_version=project.get("routing_contract_version"),
    )
