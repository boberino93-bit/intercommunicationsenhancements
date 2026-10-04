from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


class RoutingError(ValueError):
    """Raised when project/role/repository routing cannot be resolved safely."""


@dataclass(frozen=True)
class ResolvedRoute:
    project_id: str
    role_id: str
    repository: str
    forum_namespace: str
    artifact_namespace: str
    handoff_paths: tuple[str, ...]

    def acknowledgement(self, state_ref: str = "unresolved") -> str:
        return (
            f"IDENTITY RESOLVED: project={self.project_id}; role={self.role_id}; "
            f"forum={self.forum_namespace}; repositories={self.repository}; state={state_ref}"
        )


def resolve_route(
    registry: Mapping[str, Any],
    *,
    project_id: str,
    role_id: str,
    current_repository: str,
) -> ResolvedRoute:
    if registry.get("mode") != "FAIL_CLOSED":
        raise RoutingError("registry_not_fail_closed")

    projects = registry.get("projects")
    if not isinstance(projects, Mapping) or project_id not in projects:
        raise RoutingError("unknown_project")

    project = projects[project_id]
    if not isinstance(project, Mapping):
        raise RoutingError("invalid_project_entry")

    roles = project.get("roles")
    if not isinstance(roles, list) or role_id not in roles:
        raise RoutingError("unknown_or_unauthorized_role")

    repository = project.get("repository")
    if not isinstance(repository, str) or not repository:
        raise RoutingError("missing_repository")
    if current_repository != repository:
        raise RoutingError("repository_identity_mismatch")

    forum = project.get("forum_namespace")
    artifact = project.get("artifact_namespace")
    handoff = project.get("handoff_paths")
    if not isinstance(forum, str) or not forum:
        raise RoutingError("missing_forum_namespace")
    if not isinstance(artifact, str) or not artifact:
        raise RoutingError("missing_artifact_namespace")
    if not isinstance(handoff, list) or not handoff or not all(isinstance(p, str) and p for p in handoff):
        raise RoutingError("missing_handoff_paths")

    return ResolvedRoute(
        project_id=project_id,
        role_id=role_id,
        repository=repository,
        forum_namespace=forum,
        artifact_namespace=artifact,
        handoff_paths=tuple(handoff),
    )
