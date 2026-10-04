from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

from .project_role_routing import ResolvedRoute, RoutingError, resolve_route, validate_local_contract, validate_registry


class UniversalIntakeError(RoutingError):
    """Raised when an unbound agent cannot identify and bind a project safely."""


@dataclass(frozen=True)
class ProjectDiscovery:
    project_id: str
    repository: str
    repository_id: int | None
    forum_namespace: str
    evidence: tuple[str, ...]

    def acknowledgement(self) -> str:
        return f"PROJECT DISCOVERED: project={self.project_id}; repository={self.repository}; forum={self.forum_namespace}; evidence={','.join(self.evidence)}; mutation_ready=false"


@dataclass(frozen=True)
class UniversalIntakeResult:
    discovery: ProjectDiscovery
    role_id: str
    role_source: str

    @property
    def mutation_ready(self) -> bool:
        return False

    def acknowledgement(self) -> str:
        return f"UNBOUND ROUTE RESOLVED: project={self.discovery.project_id}; role={self.role_id}; role_source={self.role_source}; repository={self.discovery.repository}; forum={self.discovery.forum_namespace}; mutation_ready=false"


def _normalize_alias(value: str) -> str:
    return " ".join(value.casefold().split())


def _contains_exact_human_alias(text: str, alias: str) -> bool:
    normalized_text = _normalize_alias(text)
    normalized_alias = _normalize_alias(alias)
    pattern = r"(?<!\w)" + re.escape(normalized_alias).replace(r"\ ", r"\s+") + r"(?!\w)"
    return re.search(pattern, normalized_text) is not None


def validate_global_intake_registry(registry: Mapping[str, Any]) -> None:
    validate_registry(registry)
    config = registry.get("global_intake")
    if not isinstance(config, Mapping):
        raise UniversalIntakeError("missing_global_intake")
    if config.get("schema") != "org-agent-mesh/universal-intake/v1":
        raise UniversalIntakeError("unsupported_global_intake_schema")
    if config.get("mode") != "READ_ONLY_UNTIL_BOUND":
        raise UniversalIntakeError("global_intake_not_read_only_until_bound")
    if config.get("rendezvous_repository") != "boberino93-bit/intercommunicationsenhancements":
        raise UniversalIntakeError("invalid_rendezvous_repository")
    if config.get("rendezvous_repository_id") != 1403662737:
        raise UniversalIntakeError("invalid_rendezvous_repository_id")
    if config.get("entrypoint_path") != "UNIVERSAL_AGENT_ENTRYPOINT.md":
        raise UniversalIntakeError("invalid_global_entrypoint_path")
    if config.get("machine_entrypoint_path") != "GLOBAL_AGENT_ENTRYPOINT.json":
        raise UniversalIntakeError("invalid_machine_entrypoint_path")
    if config.get("registry_path") != "PROJECT_ROLE_ROUTING_REGISTRY.json":
        raise UniversalIntakeError("invalid_global_registry_path")
    if config.get("protocol_path") != "protocols/universal_task_routing.md":
        raise UniversalIntakeError("invalid_global_protocol_path")
    if config.get("project_similarity_inference") is not False:
        raise UniversalIntakeError("project_similarity_inference_must_be_false")
    if config.get("role_inference_from_topic") is not False:
        raise UniversalIntakeError("role_inference_from_topic_must_be_false")
    if config.get("cross_project_routing_scan") != "READ_ONLY_REGISTERED_METADATA":
        raise UniversalIntakeError("invalid_cross_project_routing_scan")
    if config.get("fallback_resolution") != "REGISTERED_FORUM_HANDOFF_EXACT_IDENTIFIER_ONLY":
        raise UniversalIntakeError("invalid_fallback_resolution")
    if config.get("local_contract_required_before_project_bootstrap") is not True:
        raise UniversalIntakeError("local_contract_gate_disabled")

    version = tuple(map(int, registry.get("routing_contract_version", "1.0.0").split(".")))
    if version >= (1, 5, 0):
        if config.get("unresolved_action") != "STOP_AFFECTED_MUTATION_CONTINUE_SAFE_READ_ONLY_DISCOVERY":
            raise UniversalIntakeError("invalid_unresolved_action")
        if config.get("context_reference_path") != "AGENT_CONTEXT_REFERENCE.md":
            raise UniversalIntakeError("invalid_context_reference_path")
        if config.get("continuation_protocol_path") != "protocols/autonomous_continuation.md":
            raise UniversalIntakeError("invalid_continuation_protocol_path")
    elif config.get("unresolved_action") != "STOP_BEFORE_MUTATION":
        raise UniversalIntakeError("invalid_unresolved_action")

    if version >= (1, 4, 0) and config.get("active_project_context_policy") != "USE_AS_STRONG_ROUTING_EVIDENCE_UNLESS_EXPLICIT_TARGET_CONFLICTS":
        raise UniversalIntakeError("invalid_active_project_context_policy")
    default_role = config.get("default_human_task_role")
    if not isinstance(default_role, str) or not default_role:
        raise UniversalIntakeError("invalid_default_human_task_role")
    seen_aliases: dict[str, str] = {}
    projects = registry["projects"]
    reserved_identifiers: dict[str, str] = {}
    for project_id, project in projects.items():
        for value in (project_id, project.get("repository"), project.get("forum_namespace")):
            if isinstance(value, str) and value:
                normalized = _normalize_alias(value)
                existing = reserved_identifiers.get(normalized)
                if existing is not None and existing != project_id:
                    raise UniversalIntakeError("duplicate_global_routing_identifier")
                reserved_identifiers[normalized] = project_id
    for project_id, project in projects.items():
        aliases = project.get("discovery_aliases")
        if not isinstance(aliases, list) or not aliases or not all(isinstance(alias, str) and alias.strip() for alias in aliases):
            raise UniversalIntakeError("invalid_discovery_aliases")
        local_aliases: set[str] = set()
        for alias in aliases:
            normalized = _normalize_alias(alias)
            if normalized in local_aliases:
                raise UniversalIntakeError("duplicate_discovery_alias")
            local_aliases.add(normalized)
            reserved_project = reserved_identifiers.get(normalized)
            if reserved_project is not None and reserved_project != project_id:
                raise UniversalIntakeError("discovery_alias_conflicts_with_routing_identifier")
            existing = seen_aliases.get(normalized)
            if existing is not None and existing != project_id:
                raise UniversalIntakeError("duplicate_discovery_alias")
            seen_aliases[normalized] = project_id
        if default_role not in project.get("roles", []):
            raise UniversalIntakeError("default_human_task_role_not_authorized")


def discover_project(
    registry: Mapping[str, Any],
    *,
    task_text: str = "",
    active_project_context: str | None = None,
    explicit_project_id: str | None = None,
    repository: str | None = None,
    repository_id: int | None = None,
    forum_namespace: str | None = None,
) -> ProjectDiscovery:
    validate_global_intake_registry(registry)
    projects = registry["projects"]
    matches: dict[str, list[str]] = {}

    def record(project_id: str, evidence: str) -> None:
        matches.setdefault(project_id, []).append(evidence)

    if explicit_project_id is not None:
        if explicit_project_id not in projects:
            raise UniversalIntakeError("unknown_explicit_project")
        record(explicit_project_id, "explicit_project_id")
    if active_project_context is not None:
        if active_project_context not in projects:
            raise UniversalIntakeError("unknown_active_project_context")
        record(active_project_context, "active_project_context")
    if repository is not None:
        found = [pid for pid, project in projects.items() if project.get("repository") == repository]
        if len(found) != 1:
            raise UniversalIntakeError("unknown_repository")
        record(found[0], "repository")
    if repository_id is not None:
        found = [pid for pid, project in projects.items() if project.get("repository_id") == repository_id]
        if len(found) != 1:
            raise UniversalIntakeError("unknown_repository_id")
        record(found[0], "repository_id")
    if forum_namespace is not None:
        found = [pid for pid, project in projects.items() if project.get("forum_namespace") == forum_namespace]
        if len(found) != 1:
            raise UniversalIntakeError("unknown_forum_namespace")
        record(found[0], "forum_namespace")
    if task_text:
        task_text_casefold = task_text.casefold()
        for project_id, project in projects.items():
            if _contains_exact_human_alias(task_text, project_id):
                record(project_id, "task_project_id")
            repository_name = project.get("repository")
            if isinstance(repository_name, str) and repository_name.casefold() in task_text_casefold:
                record(project_id, "task_repository")
            forum = project.get("forum_namespace")
            if isinstance(forum, str) and forum.casefold() in task_text_casefold:
                record(project_id, "task_forum_namespace")
            for alias in project.get("discovery_aliases", []):
                if _contains_exact_human_alias(task_text, alias):
                    record(project_id, f"alias:{alias}")
    if not matches:
        raise UniversalIntakeError("project_unresolved")
    if len(matches) != 1:
        raise UniversalIntakeError("conflicting_or_ambiguous_project_evidence")
    project_id = next(iter(matches))
    project = projects[project_id]
    return ProjectDiscovery(
        project_id=project_id,
        repository=project["repository"],
        repository_id=project.get("repository_id"),
        forum_namespace=project["forum_namespace"],
        evidence=tuple(dict.fromkeys(matches[project_id])),
    )


def resolve_unbound_intake(
    registry: Mapping[str, Any],
    *,
    task_text: str = "",
    active_project_context: str | None = None,
    explicit_project_id: str | None = None,
    repository: str | None = None,
    repository_id: int | None = None,
    forum_namespace: str | None = None,
    requested_role: str | None = None,
    human_task_present: bool = True,
) -> UniversalIntakeResult:
    discovery = discover_project(
        registry,
        task_text=task_text,
        active_project_context=active_project_context,
        explicit_project_id=explicit_project_id,
        repository=repository,
        repository_id=repository_id,
        forum_namespace=forum_namespace,
    )
    project = registry["projects"][discovery.project_id]
    if requested_role is not None:
        role_id, role_source = requested_role, "explicit"
    else:
        if not human_task_present:
            raise UniversalIntakeError("role_required_without_human_task")
        role_id, role_source = registry["global_intake"]["default_human_task_role"], "global_human_task_default"
    if role_id not in project["roles"]:
        raise UniversalIntakeError("unknown_or_unauthorized_role")
    return UniversalIntakeResult(discovery=discovery, role_id=role_id, role_source=role_source)


def complete_project_binding(
    registry: Mapping[str, Any],
    *,
    intake: UniversalIntakeResult,
    local_contract: Mapping[str, Any],
    current_repository: str | None = None,
    current_repository_id: int | None = None,
) -> ResolvedRoute:
    project_id = intake.discovery.project_id
    validate_local_contract(registry, project_id=project_id, contract=local_contract)
    repository = current_repository or intake.discovery.repository
    repository_id = current_repository_id if current_repository_id is not None else intake.discovery.repository_id
    return resolve_route(
        registry,
        project_id=project_id,
        role_id=intake.role_id,
        current_repository=repository,
        current_repository_id=repository_id,
    )
