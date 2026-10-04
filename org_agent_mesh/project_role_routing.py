from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Mapping


class RoutingError(ValueError):
    """Raised when project/role/repository routing cannot be resolved safely."""


PERSISTENT_AUTHORITY_ROLES = ("primary", "manager", "research")
LEGACY_FAIL_CLOSED_MODE = "FAIL_CLOSED"
LOCAL_CONTINUATION_MODE = "FAIL_CLOSED_LOCAL_CONTINUE_GLOBAL"


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
    execution_modes: tuple[str, ...] = ()
    master_handoff_path: str | None = None

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


def _parse_contract_version(value: Any) -> tuple[int, int, int]:
    if not isinstance(value, str) or not value:
        raise RoutingError("invalid_routing_contract_version")
    parts = value.split(".")
    if len(parts) != 3:
        raise RoutingError("invalid_routing_contract_version")
    try:
        parsed = tuple(int(part) for part in parts)
    except ValueError as exc:
        raise RoutingError("invalid_routing_contract_version") from exc
    if any(part < 0 for part in parsed):
        raise RoutingError("invalid_routing_contract_version")
    return parsed


def _validate_mode(mode: Any, version: tuple[int, int, int], *, local: bool = False) -> None:
    expected = LOCAL_CONTINUATION_MODE if version >= (1, 5, 0) else LEGACY_FAIL_CLOSED_MODE
    if mode != expected:
        raise RoutingError("local_contract_not_fail_closed" if local else "registry_not_fail_closed")


def _validate_communication_awareness(registry: Mapping[str, Any]) -> None:
    version = _parse_contract_version(registry.get("routing_contract_version", "1.0.0"))
    awareness = registry.get("communication_awareness")
    if version < (1, 3, 0):
        if awareness is not None and not isinstance(awareness, Mapping):
            raise RoutingError("invalid_communication_awareness")
        return
    if not isinstance(awareness, Mapping):
        raise RoutingError("missing_communication_awareness")
    repository = awareness.get("protocol_repository")
    if not isinstance(repository, str) or repository.count("/") != 1:
        raise RoutingError("invalid_communication_awareness_repository")
    _safe_repo_path(awareness.get("protocol_path"), field="communication_awareness_protocol_path")
    if awareness.get("required_on_startup") is not True:
        raise RoutingError("communication_awareness_startup_not_required")
    if awareness.get("required_on_visibility_question") is not True:
        raise RoutingError("communication_awareness_visibility_question_not_required")
    if awareness.get("default_visibility_claim") != "PARTIAL_UNLESS_PROVEN":
        raise RoutingError("unsafe_default_visibility_claim")
    required = awareness.get("full_visibility_requires")
    expected = {"DIRECT_INTERNAL_ARTIFACTORY_ACCESS", "PROJECT_NAMESPACE_MATCH", "FULL_SCOPE_PROVEN"}
    if not isinstance(required, list) or set(required) != expected or len(required) != len(expected):
        raise RoutingError("invalid_full_visibility_requirements")

    # 1.5 moves some duplicate safety declarations out of the central registry.
    # Older contracts continue to require those declarations exactly as before.
    if version < (1, 5, 0):
        template = awareness.get("assessment_ack_template")
        if not isinstance(template, str) or not template.startswith("COMMUNICATIONS ASSESSED:"):
            raise RoutingError("invalid_communication_assessment_template")
        rules = registry.get("rules")
        if not isinstance(rules, Mapping):
            raise RoutingError("missing_registry_rules")
        if rules.get("communication_assessment_before_visibility_claim") is not True:
            raise RoutingError("communication_assessment_guard_disabled")
        if rules.get("never_claim_all_communications_from_mirror_snapshot_or_handoff") is not True:
            raise RoutingError("communication_overclaim_guard_disabled")


def _validate_v14_continuity_contract(registry: Mapping[str, Any]) -> None:
    version = _parse_contract_version(registry.get("routing_contract_version", "1.0.0"))
    if version < (1, 4, 0):
        return
    authority = registry.get("authority_model")
    if not isinstance(authority, Mapping):
        raise RoutingError("missing_authority_model")
    if tuple(authority.get("persistent_roles", ())) != PERSISTENT_AUTHORITY_ROLES:
        raise RoutingError("invalid_persistent_authority_roles")
    execution_modes = authority.get("execution_modes")
    if not isinstance(execution_modes, list) or not execution_modes:
        raise RoutingError("invalid_execution_modes")
    if set(execution_modes) & set(PERSISTENT_AUTHORITY_ROLES):
        raise RoutingError("role_execution_mode_overlap")
    if authority.get("mode_does_not_expand_role_authority") is not True:
        raise RoutingError("execution_mode_authority_expansion_not_blocked")
    handoff = registry.get("master_handoff")
    if not isinstance(handoff, Mapping):
        raise RoutingError("missing_master_handoff_contract")
    if handoff.get("path") != "MASTER_HANDOFF.json":
        raise RoutingError("invalid_master_handoff_path")
    _safe_repo_path(handoff.get("protocol_path"), field="master_handoff_protocol_path")
    if handoff.get("required_before_mutation") is not True:
        raise RoutingError("master_handoff_gate_disabled")
    if handoff.get("manual_checkpoint_after_material_transition") is not True:
        raise RoutingError("master_handoff_checkpoint_disabled")
    if handoff.get("expired_agent_state_preservation") is not True:
        raise RoutingError("expired_agent_state_preservation_disabled")
    rules = registry.get("rules")
    if rules.get("master_handoff_before_repository_mutation") is not True:
        raise RoutingError("master_handoff_registry_guard_disabled")
    if rules.get("active_project_context_precedes_implicit_history") is not True:
        raise RoutingError("active_project_context_precedence_disabled")


def _validate_v15_autonomous_continuation(registry: Mapping[str, Any]) -> None:
    version = _parse_contract_version(registry.get("routing_contract_version", "1.0.0"))
    if version < (1, 5, 0):
        return
    fresh = registry.get("fresh_agent_context")
    if not isinstance(fresh, Mapping):
        raise RoutingError("missing_fresh_agent_context")
    if fresh.get("default_path") != "AGENT_CONTEXT_REFERENCE.md":
        raise RoutingError("invalid_fresh_agent_context_path")
    if fresh.get("authority") != "ORIENTATION_ONLY":
        raise RoutingError("fresh_agent_context_authority_expansion")
    if fresh.get("required_after_exact_project_resolution") is not True:
        raise RoutingError("fresh_agent_context_not_required")
    if fresh.get("recover_durable_context_before_human_reprompt") is not True:
        raise RoutingError("durable_context_recovery_disabled")

    continuation = registry.get("autonomous_continuation")
    if not isinstance(continuation, Mapping):
        raise RoutingError("missing_autonomous_continuation")
    repository = continuation.get("protocol_repository")
    if not isinstance(repository, str) or repository.count("/") != 1:
        raise RoutingError("invalid_autonomous_continuation_repository")
    _safe_repo_path(continuation.get("protocol_path"), field="autonomous_continuation_protocol_path")
    if continuation.get("routine_confirmation") != "DENY_AFTER_VALID_ASSIGNMENT":
        raise RoutingError("routine_confirmation_not_denied")
    if continuation.get("fail_closed_scope") != "AFFECTED_MUTATION_OR_BRANCH_ONLY":
        raise RoutingError("unsafe_continuation_fail_closed_scope")
    if continuation.get("continue_unaffected_safe_work") is not True:
        raise RoutingError("unaffected_safe_work_continuation_disabled")
    if continuation.get("human_escalation") != "TRUE_HUMAN_GATE_ONLY":
        raise RoutingError("unsafe_human_escalation_policy")

    rules = registry.get("rules")
    if not isinstance(rules, Mapping):
        raise RoutingError("missing_registry_rules")
    expected_rules = {
        "cross_project_write_default": "DENY",
        "conflicting_identity": "STOP_AFFECTED_MUTATION_DO_NOT_GUESS",
        "context_reference_is_authority": False,
        "recover_context_before_asking_human_to_repeat": True,
        "routine_confirmation": "DENY_AFTER_VALID_ASSIGNMENT",
        "continue_unaffected_safe_work": True,
    }
    for key, expected in expected_rules.items():
        if rules.get(key) != expected:
            raise RoutingError(f"unsafe_v15_registry_rule_{key}")


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
    mode, path = view.get("mode"), view.get("path")
    if mode not in {"LIVE_MIRROR", "SNAPSHOT_BACKUP", "NONE"}:
        raise RoutingError("invalid_forum_repository_view_mode")
    if mode == "NONE":
        if path is not None:
            raise RoutingError("forum_repository_view_path_must_be_null")
    else:
        _safe_repo_path(path, field="forum_repository_view_path")


def _validate_project_contract_version(project: Mapping[str, Any], registry_version: tuple[int, int, int], registry_version_text: str) -> None:
    project_version = _parse_contract_version(project.get("routing_contract_version"))
    if project_version == registry_version:
        return
    if registry_version < (1, 5, 0) or project_version >= registry_version:
        raise RoutingError("project_routing_contract_version_mismatch")
    if project.get("effective_continuation_overlay_version") != registry_version_text:
        raise RoutingError("project_routing_contract_version_mismatch")
    authority = project.get("continuation_overlay_authority")
    if not isinstance(authority, str) or not authority.strip():
        raise RoutingError("missing_continuation_overlay_authority")
    if project.get("local_bootstrap_migration_state") != "LEGACY_LOCAL_BOOTSTRAP_RETAINED":
        raise RoutingError("invalid_legacy_bootstrap_migration_state")


def validate_registry(registry: Mapping[str, Any]) -> None:
    if registry.get("schema") != "org-agent-mesh/project-role-routing-registry/v1":
        raise RoutingError("unsupported_registry_schema")
    registry_version_text = registry.get("routing_contract_version", "1.0.0")
    registry_version = _parse_contract_version(registry_version_text)
    _validate_mode(registry.get("mode"), registry_version)
    _validate_communication_awareness(registry)
    _validate_v14_continuity_contract(registry)
    _validate_v15_autonomous_continuation(registry)
    projects = registry.get("projects")
    if not isinstance(projects, Mapping) or not projects:
        raise RoutingError("missing_projects")
    seen_repositories, seen_repository_ids, seen_forums, seen_artifacts = set(), set(), set(), set()
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
        if not isinstance(roles, list) or not roles or not all(isinstance(role, str) and role for role in roles) or len(set(roles)) != len(roles):
            raise RoutingError("invalid_roles")
        if registry_version >= (1, 4, 0) and tuple(roles) != PERSISTENT_AUTHORITY_ROLES:
            raise RoutingError("invalid_persistent_authority_roles")
        if registry_version >= (1, 4, 0):
            modes = project.get("execution_modes")
            if not isinstance(modes, list) or not modes:
                raise RoutingError("missing_execution_modes")
            if set(modes) & set(roles):
                raise RoutingError("role_execution_mode_overlap")
            _safe_repo_path(project.get("master_handoff_path"), field="master_handoff_path")
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
        if registry_version >= (1, 4, 0) and project["master_handoff_path"] not in handoff:
            raise RoutingError("master_handoff_missing_from_handoff_paths")
        if registry_version >= (1, 5, 0):
            context_path = _safe_repo_path(project.get("context_reference_path"), field="context_reference_path")
            if context_path not in handoff:
                raise RoutingError("context_reference_missing_from_handoff_paths")
        local_contract_path = project.get("local_contract_path")
        if local_contract_path is not None:
            _safe_repo_path(local_contract_path, field="local_contract_path")
        _validate_project_contract_version(project, registry_version, registry_version_text)


def _communication_core(value: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "protocol_repository",
        "protocol_path",
        "required_on_startup",
        "required_on_visibility_question",
        "default_visibility_claim",
        "full_visibility_requires",
    )
    return {key: value.get(key) for key in keys}


def _validate_v15_local_contract(contract: Mapping[str, Any], registry: Mapping[str, Any], project: Mapping[str, Any]) -> None:
    fresh = contract.get("fresh_agent_context")
    if not isinstance(fresh, Mapping):
        raise RoutingError("missing_local_fresh_agent_context")
    if fresh.get("reference_path") != project.get("context_reference_path"):
        raise RoutingError("local_context_reference_path_mismatch")
    if fresh.get("authority") != "ORIENTATION_ONLY":
        raise RoutingError("local_context_reference_authority_expansion")
    for key in ("required_on_startup", "use_when_chat_context_missing", "must_not_invent_task", "current_human_instruction_overrides_likely_intent"):
        if fresh.get(key) is not True:
            raise RoutingError(f"unsafe_local_fresh_context_{key}")

    continuation = contract.get("autonomous_continuation")
    if not isinstance(continuation, Mapping):
        raise RoutingError("missing_local_autonomous_continuation")
    if continuation.get("protocol_repository") != registry["autonomous_continuation"].get("protocol_repository"):
        raise RoutingError("local_continuation_repository_mismatch")
    if continuation.get("protocol_path") != registry["autonomous_continuation"].get("protocol_path"):
        raise RoutingError("local_continuation_protocol_mismatch")
    if continuation.get("default_after_valid_assignment") != "CONTINUE_UNTIL_CONVERGENCE_OR_TRUE_HUMAN_GATE":
        raise RoutingError("unsafe_local_continuation_default")
    if continuation.get("routine_confirmation") != "DENY":
        raise RoutingError("local_routine_confirmation_not_denied")
    if continuation.get("localized_fail_closed") is not True:
        raise RoutingError("local_fail_closed_disabled")
    if continuation.get("continue_unaffected_work") is not True:
        raise RoutingError("local_unaffected_work_continuation_disabled")
    gates = continuation.get("human_interrupt_only_for")
    required_gates = {
        "NON_DELEGABLE_AUTHORITY",
        "IRRECOVERABLE_DATA_INTEGRITY",
        "SECURITY_BOUNDARY_DECISION",
        "REQUIRED_EXTERNAL_CAPABILITY",
    }
    if not isinstance(gates, list) or not required_gates.issubset(set(gates)):
        raise RoutingError("unsafe_local_human_interrupt_policy")

    rules = contract.get("rules")
    expected_rules = {
        "fresh_agent_reference_before_task_interpretation": True,
        "recover_context_before_asking_human_to_repeat": True,
        "routine_confirmation": "DENY",
        "fail_closed_scope": "AFFECTED_MUTATION_OR_BRANCH_ONLY",
        "continue_unaffected_safe_work": True,
        "cross_project_write_default": "DENY",
        "identity_conflict": "STOP_AFFECTED_MUTATION_DO_NOT_GUESS",
    }
    for key, expected in expected_rules.items():
        if rules.get(key) != expected:
            raise RoutingError(f"unsafe_local_v15_rule_{key}")


def validate_local_contract(registry: Mapping[str, Any], *, project_id: str, contract: Mapping[str, Any]) -> None:
    validate_registry(registry)
    project = registry["projects"].get(project_id)
    if not isinstance(project, Mapping):
        raise RoutingError("unknown_project")
    if contract.get("schema") != "org-agent-mesh/local-agent-bootstrap/v1":
        raise RoutingError("unsupported_local_contract_schema")
    project_version = _parse_contract_version(project.get("routing_contract_version"))
    _validate_mode(contract.get("mode"), project_version, local=True)
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
    forum, locator = contract.get("forum"), project.get("forum_locator")
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
    if project_version >= (1, 3, 0):
        local_awareness = contract.get("communication_awareness")
        registry_awareness = registry.get("communication_awareness")
        if not isinstance(local_awareness, Mapping) or not isinstance(registry_awareness, Mapping):
            raise RoutingError("local_contract_communication_awareness_mismatch")
        if project_version >= (1, 5, 0):
            if _communication_core(local_awareness) != _communication_core(registry_awareness):
                raise RoutingError("local_contract_communication_awareness_mismatch")
        elif local_awareness != registry_awareness:
            raise RoutingError("local_contract_communication_awareness_mismatch")
        rules = contract.get("rules")
        if not isinstance(rules, Mapping):
            raise RoutingError("missing_local_contract_rules")
        expected_identity_conflict = "STOP_AFFECTED_MUTATION_DO_NOT_GUESS" if project_version >= (1, 5, 0) else "STOP_BEFORE_MUTATION"
        for key, expected in {
            "identity_lock_first": True,
            "forum_authority_separate_from_repository_view": True,
            "forum_before_mutation": True,
            "handoff_before_mutation": True,
            "communication_assessment_before_visibility_claim": True,
            "never_claim_all_communications_from_mirror_snapshot_or_handoff": True,
            "cross_project_write_default": "DENY",
            "identity_conflict": expected_identity_conflict,
        }.items():
            if rules.get(key) != expected:
                raise RoutingError(f"unsafe_local_rule_{key}")
    if project_version >= (1, 4, 0):
        if contract.get("execution_modes") != project.get("execution_modes"):
            raise RoutingError("local_contract_execution_modes_mismatch")
        handoff = contract.get("master_handoff")
        if not isinstance(handoff, Mapping):
            raise RoutingError("missing_local_master_handoff")
        if handoff.get("path") != project.get("master_handoff_path"):
            raise RoutingError("local_master_handoff_path_mismatch")
        if handoff.get("required_before_mutation") is not True:
            raise RoutingError("local_master_handoff_gate_disabled")
        rules = contract["rules"]
        for key, expected in {
            "master_handoff_before_mutation": True,
            "manual_master_handoff_checkpoint_after_material_transition": True,
            "instance_fenced_lease_ownership": True,
        }.items():
            if rules.get(key) != expected:
                raise RoutingError(f"unsafe_local_rule_{key}")
    if project_version >= (1, 5, 0):
        _validate_v15_local_contract(contract, registry, project)


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
    if role_id not in project["roles"]:
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
        execution_modes=tuple(project.get("execution_modes", ())),
        master_handoff_path=project.get("master_handoff_path"),
    )
