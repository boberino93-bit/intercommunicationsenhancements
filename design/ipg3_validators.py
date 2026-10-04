"""Relational validators for IPG3 draft records.

JSON Schema validates local shape. These validators enforce cross-field invariants that
portable JSON Schema cannot express safely. This module is design-only and has no
mutation or deployment authority.
"""

from __future__ import annotations

from datetime import datetime, timezone


class IPG3ValidationError(ValueError):
    pass


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise IPG3ValidationError("timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def validate_cross_project_exchange(record: dict, *, now: datetime | None = None) -> bool:
    if record.get("schema") != "org-agent-mesh/cross-project-exchange/v2-draft":
        raise IPG3ValidationError("wrong exchange schema")
    source = record.get("source_project_id")
    destination = record.get("destination_project_id")
    if not source or not destination or source == destination:
        raise IPG3ValidationError("cross-project exchange requires two distinct projects")

    session = record.get("source_session") or {}
    requester = record.get("requester") or {}
    if session.get("project_id") != source:
        raise IPG3ValidationError("source session project does not match source project")
    if session.get("capability") != "CROSS_PROJECT_EXCHANGE":
        raise IPG3ValidationError("source session lacks CROSS_PROJECT_EXCHANGE capability")
    if requester.get("agent_id") != session.get("agent_id"):
        raise IPG3ValidationError("requester agent does not match source session")
    if requester.get("agent_instance_id") != session.get("agent_instance_id"):
        raise IPG3ValidationError("requester execution instance does not match source session")

    created = _parse_utc(record["created_at_utc"])
    expires = _parse_utc(record["expires_at_utc"])
    if expires <= created:
        raise IPG3ValidationError("exchange expiry must follow creation")
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise IPG3ValidationError("now must be timezone-aware")
    if expires <= current.astimezone(timezone.utc):
        raise IPG3ValidationError("exchange is expired")

    sanitization = record.get("sanitization") or {}
    if not sanitization.get("remove_secrets"):
        raise IPG3ValidationError("sanitized exchange must remove secrets")
    if not sanitization.get("remove_personal_data"):
        raise IPG3ValidationError("sanitized exchange must remove personal data")
    if not sanitization.get("remove_project_instance_state"):
        raise IPG3ValidationError("sanitized exchange must remove project-instance state")

    scope = record.get("scope") or {}
    artifacts = record.get("artifacts") or []
    if len(artifacts) > scope.get("max_artifacts", -1):
        raise IPG3ValidationError("artifact count exceeds approved scope")
    if sum(item.get("size_bytes", 0) for item in artifacts) > scope.get("max_total_bytes", -1):
        raise IPG3ValidationError("artifact bytes exceed approved scope")

    decision = (record.get("destination_validation") or {}).get("decision")
    status = record.get("status")
    if status == "DESTINATION_ACCEPTED" and decision != "ACCEPT":
        raise IPG3ValidationError("accepted status requires destination ACCEPT decision")
    if status == "DESTINATION_REJECTED" and decision != "REJECT":
        raise IPG3ValidationError("rejected status requires destination REJECT decision")
    if status == "QUARANTINED" and decision != "QUARANTINE":
        raise IPG3ValidationError("quarantine status requires destination QUARANTINE decision")
    return True


def validate_human_approval(record: dict, *, now: datetime | None = None) -> bool:
    if record.get("schema") != "org-agent-mesh/human-approval/v1-draft":
        raise IPG3ValidationError("wrong approval schema")
    issued = _parse_utc(record["issued_at_utc"])
    expires = _parse_utc(record["expires_at_utc"])
    if expires <= issued:
        raise IPG3ValidationError("approval expiry must follow issue time")
    if record["uses"] > record["max_uses"]:
        raise IPG3ValidationError("approval uses exceed max_uses")
    current = now or datetime.now(timezone.utc)
    expired = expires <= current.astimezone(timezone.utc)
    status = record["status"]
    if expired and status not in {"EXPIRED", "REVOKED"}:
        raise IPG3ValidationError("expired approval cannot remain actionable")
    if status == "CONSUMED" and record["uses"] < record["max_uses"]:
        raise IPG3ValidationError("CONSUMED requires all authorized uses to be spent")
    if status == "ISSUED" and record["uses"] >= record["max_uses"]:
        raise IPG3ValidationError("ISSUED approval has no remaining uses")
    if not record.get("decision_evidence_ref"):
        raise IPG3ValidationError("approval requires decision evidence")
    return True


def validate_effect_receipt(record: dict) -> bool:
    if record.get("schema") != "org-agent-mesh/effect-receipt/v1-draft":
        raise IPG3ValidationError("wrong effect receipt schema")
    status = record["status"]
    prepared = record.get("prepared_at_utc")
    committed = record.get("committed_at_utc")
    replay = record["replay_disposition"]

    if status == "PREPARED" and not prepared:
        raise IPG3ValidationError("PREPARED effect requires prepared_at_utc")
    if status == "COMMITTED":
        if not committed:
            raise IPG3ValidationError("COMMITTED effect requires committed_at_utc")
        if replay not in {"FIRST_COMMIT", "REPLAY_MATCHED"}:
            raise IPG3ValidationError("COMMITTED effect has invalid replay disposition")
    if status == "DUPLICATE_NOOP":
        if replay != "REPLAY_MATCHED":
            raise IPG3ValidationError("duplicate no-op must match an existing committed effect")
        if committed:
            raise IPG3ValidationError("duplicate no-op must not claim a second commit time")
    if status in {"FAILED", "REJECTED"} and replay == "FIRST_COMMIT":
        raise IPG3ValidationError("failed/rejected effect cannot claim FIRST_COMMIT")
    if prepared and committed and _parse_utc(committed) < _parse_utc(prepared):
        raise IPG3ValidationError("effect commit cannot precede preparation")
    return True
