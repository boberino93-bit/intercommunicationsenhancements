from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any, Mapping


class UserControlContractError(ValueError):
    """Raised when a user control-message contract weakens continuation safety."""


PROTOCOL_PATH = "protocols/user_control_messages.md"
PERCENTAGE_POLICY = "APPROXIMATE_FROM_KNOWN_REMAINING_PHASES_UNLESS_TELEMETRY_EXISTS"
LEGACY_RESUME_STEP = "when_user_control_message_arrives_respond_then_resume_active_assignment"
AUTHORIZATION_AWARE_RESUME_STEP = "when_user_control_message_arrives_respond_then_resume_only_non_mutating_or_valid_coordination_work_unless_a_current_mutation_case_exists"


def _safe_protocol_path(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise UserControlContractError("invalid_user_control_protocol_path")
    if "\\" in value:
        raise UserControlContractError("unsafe_user_control_protocol_path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise UserControlContractError("unsafe_user_control_protocol_path")
    return value


def _validate_common(policy: Mapping[str, Any], *, local: bool) -> None:
    prefix = "local_" if local else "registry_"
    repository = policy.get("protocol_repository")
    if not isinstance(repository, str) or repository.count("/") != 1:
        raise UserControlContractError(f"{prefix}invalid_user_control_repository")
    if _safe_protocol_path(policy.get("protocol_path")) != PROTOCOL_PATH:
        raise UserControlContractError(f"{prefix}user_control_protocol_mismatch")
    if policy.get("status_request_is_cancellation") is not False:
        raise UserControlContractError(f"{prefix}status_request_treated_as_cancellation")
    if policy.get("immediate_status_response") is not True:
        raise UserControlContractError(f"{prefix}immediate_status_response_disabled")
    if policy.get("preserve_active_assignment") is not True:
        raise UserControlContractError(f"{prefix}active_assignment_preservation_disabled")
    if policy.get("automatic_resume_after_control_message") is not True:
        raise UserControlContractError(f"{prefix}automatic_resume_disabled")
    if policy.get("routine_continue_reprompt") != "DENY":
        raise UserControlContractError(f"{prefix}continue_reprompt_not_denied")
    if policy.get("progress_percentage_policy") != PERCENTAGE_POLICY:
        raise UserControlContractError(f"{prefix}unsafe_percentage_policy")


def validate_registry_control_message_contract(registry: Mapping[str, Any]) -> None:
    policy = registry.get("user_control_messages")
    if not isinstance(policy, Mapping):
        raise UserControlContractError("missing_registry_user_control_messages")
    _validate_common(policy, local=False)
    rules = registry.get("rules")
    if not isinstance(rules, Mapping):
        raise UserControlContractError("missing_registry_rules")
    for key in (
        "user_control_message_is_not_cancellation",
        "respond_to_control_message_before_resuming",
        "resume_interrupted_assignment_automatically",
    ):
        if rules.get(key) is not True:
            raise UserControlContractError(f"unsafe_registry_rule_{key}")


def validate_local_control_message_contract(
    contract: Mapping[str, Any],
    *,
    registry: Mapping[str, Any] | None = None,
) -> None:
    policy = contract.get("user_control_messages")
    if not isinstance(policy, Mapping):
        raise UserControlContractError("missing_local_user_control_messages")
    _validate_common(policy, local=True)
    if policy.get("explicit_stop_cancel_pause_or_redirect_overrides_resume") is not True:
        raise UserControlContractError("local_explicit_stop_override_disabled")
    if registry is not None:
        registry_policy = registry.get("user_control_messages")
        if not isinstance(registry_policy, Mapping):
            raise UserControlContractError("missing_registry_user_control_messages")
        for key in ("protocol_repository", "protocol_path", "progress_percentage_policy"):
            if policy.get(key) != registry_policy.get(key):
                raise UserControlContractError(f"local_registry_user_control_mismatch_{key}")
    rules = contract.get("rules")
    if not isinstance(rules, Mapping):
        raise UserControlContractError("missing_local_rules")
    for key in (
        "user_control_message_is_not_cancellation",
        "respond_to_control_message_before_resuming",
        "resume_interrupted_assignment_automatically",
    ):
        if rules.get(key) is not True:
            raise UserControlContractError(f"unsafe_local_rule_{key}")


def validate_global_entrypoint_control_policy(entrypoint: Mapping[str, Any]) -> None:
    rendezvous = entrypoint.get("rendezvous")
    if not isinstance(rendezvous, Mapping) or rendezvous.get("user_control_message_protocol") != PROTOCOL_PATH:
        raise UserControlContractError("global_entrypoint_missing_user_control_protocol")
    policy = entrypoint.get("control_message_policy")
    if not isinstance(policy, Mapping):
        raise UserControlContractError("global_entrypoint_missing_control_message_policy")
    expected = {
        "status_progress_or_explanation_request_is_task_completion": False,
        "respond_before_resuming": True,
        "preserve_active_assignment": True,
        "automatic_resume": True,
        "require_continue_reprompt": False,
        "percentage_policy": PERCENTAGE_POLICY,
    }
    for key, value in expected.items():
        if policy.get(key) != value:
            raise UserControlContractError(f"unsafe_global_control_policy_{key}")
    sequence = entrypoint.get("sequence")
    if not isinstance(sequence, list):
        raise UserControlContractError("global_control_resume_step_missing")
    if LEGACY_RESUME_STEP not in sequence and AUTHORIZATION_AWARE_RESUME_STEP not in sequence:
        raise UserControlContractError("global_control_resume_step_missing")
