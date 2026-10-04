from __future__ import annotations

from datetime import datetime
from typing import Mapping

from .project_scope import (
    ProjectScopeError,
    require_project_id,
    require_repository_identity,
    require_resource_id,
)


COORDINATOR_REQUIRED_FIELDS = {
    "coordinator_agent_id",
    "coordinator_project_id",
    "epoch_id",
    "scope",
    "allowed_reads",
    "allowed_writes",
    "prohibited_actions",
    "start_time",
    "expiry_or_review_condition",
    "human_assignment_ref",
}

SANITIZED_PROJECT_SUMMARY_FIELDS = {
    "project_id",
    "project_name",
    "purpose",
    "status",
    "repository_identity",
    "canonical_branch",
    "board_root",
    "protocol_version",
    "package_version",
    "capacity_state",
    "backup_state",
    "recovery_state",
    "allowed_cross_project_links",
    "last_verified",
}


def _parse_utc(value, field):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware")
    return parsed


def validate_coordinator_claim(claim: Mapping):
    """Validate a human-designated ecosystem coordinator claim.

    This is intentionally a validation/detection contract, not a peer-project write
    authority service. A coordinator remains an existing PRIMARY and cross-project
    mutation stays denied unless a separate approved bridge authorizes it.
    """
    if not isinstance(claim, Mapping):
        raise ValueError("coordinator claim must be an object")
    missing = sorted(COORDINATOR_REQUIRED_FIELDS - set(claim))
    if missing:
        raise ValueError(f"coordinator claim missing fields: {missing}")
    require_resource_id(claim["coordinator_agent_id"], field="coordinator_agent_id")
    require_project_id(claim["coordinator_project_id"])
    require_resource_id(claim["epoch_id"], field="epoch_id")
    if claim["scope"] not in {"ECOSYSTEM_SCOPE", "BRIDGE_SCOPE"}:
        raise ValueError("unsupported coordinator scope")
    for field in ("allowed_reads", "allowed_writes", "prohibited_actions"):
        if not isinstance(claim[field], list):
            raise ValueError(f"{field} must be a list")
    if not claim["human_assignment_ref"]:
        raise ProjectScopeError("ecosystem coordinator claim requires human assignment")
    _parse_utc(claim["start_time"], "start_time")
    return True


def compare_coordinator_claims(first: Mapping, second: Mapping):
    """Detect duplicate coordinator claims without electing by assumption."""
    validate_coordinator_claim(first)
    validate_coordinator_claim(second)
    if first["epoch_id"] != second["epoch_id"]:
        return {
            "state": "DIFFERENT_EPOCHS",
            "freeze_global_mutations": False,
            "authoritative_claim": None,
        }
    first_identity = (first["coordinator_project_id"], first["coordinator_agent_id"])
    second_identity = (second["coordinator_project_id"], second["coordinator_agent_id"])
    if first_identity == second_identity:
        return {
            "state": "DUPLICATE_IDENTICAL_COORDINATOR",
            "freeze_global_mutations": False,
            "authoritative_claim": first_identity,
        }
    return {
        "state": "SPLIT_BRAIN_DETECTED",
        "freeze_global_mutations": True,
        "authoritative_claim": None,
        "preserve_both_claims": True,
        "resolution": "COMPARE_HUMAN_AND_ACTIVE_CONTRACT_AUTHORITY_THEN_SUPERSEDE",
    }


def validate_sanitized_project_summary(summary: Mapping):
    """Allow only the V2 ecosystem registry's sanitized project-summary fields."""
    if not isinstance(summary, Mapping):
        raise ValueError("project summary must be an object")
    unknown = sorted(set(summary) - SANITIZED_PROJECT_SUMMARY_FIELDS)
    if unknown:
        raise ProjectScopeError(
            f"sanitized project summary contains non-approved fields: {unknown}"
        )
    missing = sorted(SANITIZED_PROJECT_SUMMARY_FIELDS - set(summary))
    if missing:
        raise ValueError(f"sanitized project summary missing fields: {missing}")
    require_project_id(summary["project_id"])
    require_repository_identity(summary["repository_identity"])
    if not isinstance(summary["allowed_cross_project_links"], list):
        raise ValueError("allowed_cross_project_links must be a list")
    if not all(
        isinstance(item, str) and item for item in summary["allowed_cross_project_links"]
    ):
        raise ValueError("allowed_cross_project_links entries must be non-empty strings")
    for field in (
        "project_name",
        "purpose",
        "status",
        "canonical_branch",
        "board_root",
        "protocol_version",
        "package_version",
        "capacity_state",
        "backup_state",
        "recovery_state",
        "last_verified",
    ):
        if not isinstance(summary[field], str) or not summary[field].strip():
            raise ValueError(f"{field} must be a non-empty string")
    return True
