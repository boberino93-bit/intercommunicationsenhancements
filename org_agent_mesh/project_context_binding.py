from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import hmac
import json
from typing import Any, Mapping

from .project_scope import require_project_id, require_repository_identity


PROJECT_BOUND_LAUNCH_SCHEMA = "org-agent-mesh/project-bound-launch-context/v1"
BEGIN_MARKER = "ORG_AGENT_MESH_PROJECT_CONTEXT_BINDING"
END_MARKER = "END_ORG_AGENT_MESH_PROJECT_CONTEXT_BINDING"


class ProjectContextBindingError(ValueError):
    pass


@dataclass(frozen=True)
class ProjectContextBinding:
    project_id: str
    chat_project: str
    repository: str
    repository_id: int | None
    forum_authority: str
    forum_namespace: str
    artifact_namespace: str
    local_contract_path: str
    context_reference_path: str

    def acknowledgement(self) -> str:
        return (
            f"PROJECT CONTEXT BOUND: project={self.project_id}; chat_project={self.chat_project}; "
            f"repository={self.repository}; forum={self.forum_namespace}; "
            "task_interpretation_allowed=true; mutation_authority=false"
        )


def _normalize(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProjectContextBindingError("host project context is required")
    return " ".join(value.casefold().split())


def _canonical_fingerprint(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


def resolve_host_project_id(registry: Mapping[str, Any], host_project_context: str) -> str:
    projects = registry.get("projects")
    if not isinstance(projects, Mapping) or not projects:
        raise ProjectContextBindingError("project context registry has no projects")
    if host_project_context in projects:
        return require_project_id(host_project_context)
    normalized = _normalize(host_project_context)
    matches = [
        project_id
        for project_id, project in projects.items()
        if isinstance(project, Mapping)
        and isinstance(project.get("chat_project"), str)
        and _normalize(project["chat_project"]) == normalized
    ]
    if len(matches) != 1:
        raise ProjectContextBindingError("host project context is unknown or ambiguous")
    return require_project_id(matches[0])


def bind_host_project_context(
    registry: Mapping[str, Any],
    *,
    host_project_context: str,
    explicit_project_id: str | None = None,
    repository: str | None = None,
    repository_id: int | None = None,
    forum_namespace: str | None = None,
) -> ProjectContextBinding:
    project_id = resolve_host_project_id(registry, host_project_context)
    project = registry["projects"][project_id]

    if explicit_project_id is not None and require_project_id(explicit_project_id) != project_id:
        raise ProjectContextBindingError("explicit project conflicts with host project context")
    if repository is not None and require_repository_identity(repository) != project.get("repository"):
        raise ProjectContextBindingError("repository conflicts with host project context")
    if repository_id is not None and repository_id != project.get("repository_id"):
        raise ProjectContextBindingError("repository id conflicts with host project context")
    if forum_namespace is not None and forum_namespace != project.get("forum_namespace"):
        raise ProjectContextBindingError("forum namespace conflicts with host project context")

    required_fields = (
        "repository",
        "forum_authority",
        "forum_namespace",
        "artifact_namespace",
        "local_contract_path",
        "context_reference_path",
        "chat_project",
    )
    missing = [name for name in required_fields if not project.get(name)]
    if missing:
        raise ProjectContextBindingError("project context registry entry incomplete: " + ",".join(missing))

    return ProjectContextBinding(
        project_id=project_id,
        chat_project=project["chat_project"],
        repository=require_repository_identity(project["repository"]),
        repository_id=project.get("repository_id"),
        forum_authority=project["forum_authority"],
        forum_namespace=project["forum_namespace"],
        artifact_namespace=project["artifact_namespace"],
        local_contract_path=project["local_contract_path"],
        context_reference_path=project["context_reference_path"],
    )


def binding_payload(binding: ProjectContextBinding) -> dict[str, Any]:
    payload = {
        "schema": PROJECT_BOUND_LAUNCH_SCHEMA,
        "mode": "PROJECT_BOUND",
        "project_id": binding.project_id,
        "chat_project": binding.chat_project,
        "repository": binding.repository,
        "repository_id": binding.repository_id,
        "forum_authority": binding.forum_authority,
        "forum_namespace": binding.forum_namespace,
        "artifact_namespace": binding.artifact_namespace,
        "local_contract_path": binding.local_contract_path,
        "context_reference_path": binding.context_reference_path,
    }
    payload["context_fingerprint"] = _canonical_fingerprint(payload)
    return payload


def render_project_launch_context(binding: ProjectContextBinding) -> str:
    return (
        BEGIN_MARKER
        + "\n"
        + json.dumps(binding_payload(binding), sort_keys=True, separators=(",", ":"))
        + "\n"
        + END_MARKER
    )


def parse_project_launch_context(text: str, registry: Mapping[str, Any]) -> ProjectContextBinding:
    if not isinstance(text, str) or not text.strip():
        raise ProjectContextBindingError("project launch context text is required")
    lines = text.splitlines()
    begins = [i for i, line in enumerate(lines) if line.strip() == BEGIN_MARKER]
    ends = [i for i, line in enumerate(lines) if line.strip() == END_MARKER]
    if len(begins) != 1 or len(ends) != 1 or ends[0] <= begins[0] + 1:
        raise ProjectContextBindingError("exactly one project context binding block is required")
    raw = "\n".join(lines[begins[0] + 1 : ends[0]]).strip()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProjectContextBindingError("project context binding payload is invalid JSON") from exc
    if not isinstance(payload, dict):
        raise ProjectContextBindingError("project context binding payload must be an object")
    fingerprint = payload.pop("context_fingerprint", None)
    if not isinstance(fingerprint, str) or len(fingerprint) != 64:
        raise ProjectContextBindingError("project context binding fingerprint is missing")
    if not hmac.compare_digest(fingerprint, _canonical_fingerprint(payload)):
        raise ProjectContextBindingError("project context binding fingerprint mismatch")
    if payload.get("schema") != PROJECT_BOUND_LAUNCH_SCHEMA or payload.get("mode") != "PROJECT_BOUND":
        raise ProjectContextBindingError("unsupported project context binding schema or mode")

    binding = bind_host_project_context(
        registry,
        host_project_context=payload.get("chat_project", ""),
        explicit_project_id=payload.get("project_id"),
        repository=payload.get("repository"),
        repository_id=payload.get("repository_id"),
        forum_namespace=payload.get("forum_namespace"),
    )
    expected = binding_payload(binding)
    expected.pop("context_fingerprint", None)
    if payload != expected:
        raise ProjectContextBindingError("project context binding does not match canonical registry")
    return binding


def require_project_context_ready(
    *,
    binding: ProjectContextBinding,
    local_bootstrap_loaded: bool,
    context_reference_loaded: bool,
    identity_lock_checked: bool,
    handoff_loaded: bool,
    coordination_route_loaded: bool,
) -> bool:
    require_project_id(binding.project_id)
    checks = {
        "local_bootstrap_loaded": local_bootstrap_loaded,
        "context_reference_loaded": context_reference_loaded,
        "identity_lock_checked": identity_lock_checked,
        "handoff_loaded": handoff_loaded,
        "coordination_route_loaded": coordination_route_loaded,
    }
    missing = [name for name, value in checks.items() if value is not True]
    if missing:
        raise ProjectContextBindingError("project context bootstrap incomplete: " + ",".join(missing))
    return True
