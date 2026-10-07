from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping

from .project_scope import ProjectScopeError, require_project_id, require_resource_id


BENEFIT_CLASSES = {
    "PASSIVE_KNOWLEDGE",
    "DISCOVERY",
    "EXPERTISE_AWARENESS",
    "CAPABILITY_AWARENESS",
    "MANAGERIAL_AWARENESS",
    "ROUTING_REQUEST",
    "ACTIVE_EXECUTION",
}

VALIDATION_STATES = {
    "RAW",
    "CANDIDATE",
    "VALIDATED",
    "SUPERSEDED",
    "NOT_APPLICABLE",
}

AVAILABILITY_STATES = {
    "AVAILABLE",
    "ACTIVE",
    "BUSY",
    "BLOCKED",
    "WAITING",
    "COMPLETED",
    "OFFLINE",
    "UNKNOWN",
    "NOT_APPLICABLE",
}

REQUIRED_FIELDS = {
    "schema",
    "message_id",
    "benefit_class",
    "source_project_id",
    "consumer_project_id",
    "created_at_utc",
    "expires_at_utc",
    "correlation_id",
    "subject",
    "scope",
    "artifact_refs",
    "provenance_refs",
    "validation_state",
    "availability_state",
    "capability_refs",
    "request_ref",
    "assignment_ref",
    "authority_conveyed",
}

ASSIGNMENT_EVIDENCE_FIELDS = {
    "project_id",
    "task_id",
    "assignee_agent_id",
    "status",
    "observed_at_utc",
    "evidence_ref",
}


def _parse_utc(value, field):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _require_string_list(value, field, *, nonempty=False):
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    if nonempty and not value:
        raise ValueError(f"{field} must not be empty")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{field} entries must be non-empty strings")


def validate_operational_intelligence_envelope(envelope: Mapping, *, now=None):
    """Validate the semantic envelope for cross-project operational benefit.

    This function validates representation and safety invariants only. It does not
    grant cross-project read, write, routing, assignment, or mutation authority.
    Existing project binding, exchange, delegation, and mutation controls remain
    authoritative for the underlying operation.
    """
    if not isinstance(envelope, Mapping):
        raise ValueError("operational intelligence envelope must be an object")
    missing = sorted(REQUIRED_FIELDS - set(envelope))
    if missing:
        raise ValueError(f"operational intelligence envelope missing fields: {missing}")
    if envelope["schema"] != "org-agent-mesh/project-intelligence-envelope/v1":
        raise ValueError("unsupported operational intelligence schema")

    require_resource_id(envelope["message_id"], field="message_id")
    require_resource_id(envelope["correlation_id"], field="correlation_id")
    source = require_project_id(envelope["source_project_id"])
    consumer = require_project_id(envelope["consumer_project_id"])
    if source == consumer:
        raise ValueError("operational intelligence envelope requires distinct projects")

    benefit_class = envelope["benefit_class"]
    if benefit_class not in BENEFIT_CLASSES:
        raise ValueError("unsupported benefit_class")
    if envelope["validation_state"] not in VALIDATION_STATES:
        raise ValueError("unsupported validation_state")
    if envelope["availability_state"] not in AVAILABILITY_STATES:
        raise ValueError("unsupported availability_state")
    if envelope["authority_conveyed"] is not False:
        raise ProjectScopeError("cross-project intelligence never conveys authority")

    for field in ("subject", "scope"):
        if not isinstance(envelope[field], str) or not envelope[field].strip():
            raise ValueError(f"{field} must be a non-empty string")
    _require_string_list(envelope["artifact_refs"], "artifact_refs")
    _require_string_list(envelope["provenance_refs"], "provenance_refs", nonempty=True)
    _require_string_list(envelope["capability_refs"], "capability_refs")

    created = _parse_utc(envelope["created_at_utc"], "created_at_utc")
    expires = _parse_utc(envelope["expires_at_utc"], "expires_at_utc")
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    current = current.astimezone(timezone.utc)
    if expires <= created:
        raise ValueError("expires_at_utc must be after created_at_utc")
    if expires <= current:
        raise ProjectScopeError("operational intelligence envelope is expired")

    if benefit_class == "PASSIVE_KNOWLEDGE":
        if envelope["validation_state"] != "VALIDATED":
            raise ProjectScopeError("passive knowledge benefit requires VALIDATED knowledge")
        if not envelope["artifact_refs"]:
            raise ValueError("passive knowledge benefit requires artifact_refs")
        if envelope["assignment_ref"] is not None:
            raise ProjectScopeError("passive knowledge must not imply active assignment")

    if benefit_class in {"EXPERTISE_AWARENESS", "CAPABILITY_AWARENESS", "MANAGERIAL_AWARENESS"}:
        if envelope["availability_state"] == "NOT_APPLICABLE":
            raise ValueError("awareness benefit requires explicit availability state, including UNKNOWN")
        if envelope["assignment_ref"] is not None:
            raise ProjectScopeError("awareness does not imply active assignment")

    if benefit_class == "ROUTING_REQUEST":
        if not isinstance(envelope["request_ref"], str) or not envelope["request_ref"].strip():
            raise ValueError("routing request requires request_ref")
        if envelope["assignment_ref"] is not None:
            raise ProjectScopeError("routing request is not an active assignment")

    if benefit_class != "ACTIVE_EXECUTION" and envelope["assignment_ref"] is not None:
        raise ProjectScopeError("only ACTIVE_EXECUTION may carry assignment_ref")

    if benefit_class == "ACTIVE_EXECUTION":
        if not isinstance(envelope["assignment_ref"], str) or not envelope["assignment_ref"].strip():
            raise ValueError("active execution requires assignment_ref")
        if envelope["availability_state"] != "ACTIVE":
            raise ProjectScopeError("active execution requires ACTIVE availability state")

    return True


def assert_active_execution_claim(envelope: Mapping, *, assignment_evidence: Mapping, now=None):
    """Require canonical assignment evidence before representing active participation.

    ``assignment_evidence`` must be resolved independently from the performing
    project's canonical local assignment/presence surface. This helper checks that
    the supplied evidence is internally consistent with the envelope; it does not
    make the evidence authoritative merely because the caller supplied it.
    """
    validate_operational_intelligence_envelope(envelope, now=now)
    if envelope["benefit_class"] != "ACTIVE_EXECUTION":
        raise ProjectScopeError("envelope does not claim active execution")
    if not isinstance(assignment_evidence, Mapping):
        raise ProjectScopeError("active execution requires canonical assignment evidence")
    missing = sorted(ASSIGNMENT_EVIDENCE_FIELDS - set(assignment_evidence))
    if missing:
        raise ValueError(f"assignment evidence missing fields: {missing}")

    evidence_project = require_project_id(assignment_evidence["project_id"])
    if evidence_project != envelope["source_project_id"]:
        raise ProjectScopeError("assignment evidence project does not match source project")
    for field in ("task_id", "assignee_agent_id", "evidence_ref"):
        if not isinstance(assignment_evidence[field], str) or not assignment_evidence[field].strip():
            raise ValueError(f"assignment evidence {field} must be non-empty")
    if assignment_evidence["status"] != "ACTIVE":
        raise ProjectScopeError("assignment evidence is not ACTIVE")
    observed = _parse_utc(assignment_evidence["observed_at_utc"], "observed_at_utc")
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    current = current.astimezone(timezone.utc)
    if observed > current:
        raise ProjectScopeError("assignment evidence cannot be from the future")
    if envelope["assignment_ref"] != assignment_evidence["evidence_ref"]:
        raise ProjectScopeError("assignment_ref does not match canonical evidence_ref")
    return True


def participation_state(envelope: Mapping, *, assignment_evidence=None, now=None):
    """Return a truth-preserving participation label for user/agent reporting."""
    validate_operational_intelligence_envelope(envelope, now=now)
    if envelope["benefit_class"] != "ACTIVE_EXECUTION":
        return "INDIRECT_BENEFIT_ONLY"
    assert_active_execution_claim(envelope, assignment_evidence=assignment_evidence, now=now)
    return "ACTIVE_PARTICIPATION_VERIFIED"
