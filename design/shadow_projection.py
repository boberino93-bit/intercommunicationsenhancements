"""Non-authoritative Message v2 -> IPG3 Message v3 shadow projection.

This module is deliberately stored under design/. It does not authorize mutation, publish
messages, alter the current protocol version, or participate in deployment packages.
Its purpose is to project accepted v2-shaped messages into the proposed v3 envelope so
semantic gaps can be measured before any migration decision.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy


V2_REQUIRED = {
    "schema", "protocol_version", "id", "project_id", "destination_project_id", "timestamp_utc",
    "from_agent", "from_agent_instance_id", "from_role", "to", "kind", "priority", "subject", "summary",
    "applies_to_state", "evidence", "artifacts", "reply_to", "supersedes", "requires_ack", "tags",
    "correlation_id", "causation_id", "idempotency_key", "expires_at_utc",
}

_KIND_CLASS = {
    "CLAIM": "WORK",
    "FINDING": "EVIDENCE",
    "BLOCKER": "CONTROL",
    "REQUEST": "WORK",
    "REVIEW_REQUEST": "REVIEW",
    "REVIEW_DISPOSITION": "REVIEW",
    "CONTRADICTION": "EVIDENCE",
    "HANDOFF": "CONTROL",
    "DECISION": "DECISION",
    "SUPERSESSION": "CONTROL",
    "SERVICE_CHECKPOINT": "OBSERVABILITY",
    "RELEASE_CLOSE": "CONTROL",
}

_ROLE_NAMES = {"PRIMARY", "MANAGER", "RESEARCH", "ORCHESTRATOR", "REVIEWER", "SPECIALIST"}


def _canonical_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(value) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _recipient(value: str) -> dict:
    upper = value.upper()
    if value in {"project-forum", "forum"}:
        kind = "FORUM"
    elif upper in _ROLE_NAMES:
        kind = "ROLE"
    elif value.startswith("service:"):
        kind = "SERVICE"
    else:
        kind = "AGENT"
    return {"type": kind, "id": value}


def _validate_v2_shape(message: dict) -> None:
    if not isinstance(message, dict):
        raise TypeError("v2 message must be an object")
    missing = sorted(V2_REQUIRED - set(message))
    if missing:
        raise ValueError(f"v2 message missing fields: {missing}")
    if message["schema"] != "org-agent-mesh/message/v2":
        raise ValueError("shadow projection accepts only org-agent-mesh/message/v2")
    if message["project_id"] != message["destination_project_id"]:
        raise ValueError("ordinary v2 AgentBus traffic must remain intra-project")
    if not message["id"] or not message["from_agent_instance_id"]:
        raise ValueError("v2 message identity is incomplete")
    if not isinstance(message["to"], list) or not message["to"]:
        raise ValueError("v2 recipients must be a non-empty list")


def _envelope_digest_input(projected: dict) -> dict:
    stable = deepcopy(projected)
    stable["integrity"] = {
        "payload_sha256": projected["integrity"]["payload_sha256"],
        "canonical_envelope_sha256": None,
        "signature": None,
    }
    return stable


def project_v2_to_v3(message: dict, *, channel_id: str = "agentbus", max_attempts: int = 3) -> dict:
    """Return a deterministic, non-authoritative v3 shadow representation of a v2 message."""
    _validate_v2_shape(message)
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    payload = {
        "subject": message["subject"],
        "summary": message["summary"],
        "body": {
            "applies_to_state": deepcopy(message["applies_to_state"]),
            "legacy_tags": deepcopy(message["tags"]),
            "legacy_protocol_version": message["protocol_version"],
        },
        "evidence": deepcopy(message["evidence"]),
        "artifacts": deepcopy(message["artifacts"]),
        "supersedes": deepcopy(message["supersedes"]),
    }

    projected = {
        "schema": "org-agent-mesh/message/v3-draft",
        "protocol_version": "3.0.0-draft",
        "protocol_features": ["CAUSALITY", "SHADOW_PROJECTION", "TRUST_CLASSIFICATION"],
        "message_id": message["id"],
        "project_id": message["project_id"],
        "channel_id": channel_id,
        "created_at_utc": message["timestamp_utc"],
        "expires_at_utc": message["expires_at_utc"],
        "sender": {
            "agent_id": message["from_agent"],
            "agent_instance_id": message["from_agent_instance_id"],
            "role": message["from_role"],
            "principal_id": None,
        },
        "recipients": [_recipient(item) for item in message["to"]],
        "class": _KIND_CLASS.get(message["kind"], "CONTROL"),
        "kind": message["kind"],
        "priority": message["priority"],
        "task": {
            "task_id": None,
            "delegation_contract_id": None,
            "approval_id": None,
        },
        "causality": {
            "trace_id": message["correlation_id"] or message["id"],
            "correlation_id": message["correlation_id"],
            "causation_id": message["causation_id"],
            "parent_message_id": message["reply_to"],
            "project_event_sequence": None,
        },
        "delivery": {
            "idempotency_key": message["idempotency_key"] or message["id"],
            "ack_policy": "EXECUTION" if message["requires_ack"] else "NONE",
            "max_attempts": max_attempts,
        },
        "trust": {
            "trust_class": "EXECUTION_EVIDENCE",
            "provenance_refs": [],
        },
        "policy": {
            "sensitivity": "INTERNAL",
            "retention_class": "PROJECT_DEFAULT",
        },
        "payload": payload,
        "integrity": {
            "payload_sha256": _sha256(payload),
            "canonical_envelope_sha256": None,
            "signature": None,
        },
    }
    projected["integrity"]["canonical_envelope_sha256"] = _sha256(_envelope_digest_input(projected))
    return projected


def assert_semantic_projection(v2: dict, v3: dict) -> bool:
    """Fail if projection changed security-relevant v2 semantics."""
    _validate_v2_shape(v2)
    checks = [
        v3["schema"] == "org-agent-mesh/message/v3-draft",
        v3["message_id"] == v2["id"],
        v3["project_id"] == v2["project_id"],
        v3["sender"]["agent_id"] == v2["from_agent"],
        v3["sender"]["agent_instance_id"] == v2["from_agent_instance_id"],
        v3["kind"] == v2["kind"],
        v3["priority"] == v2["priority"],
        v3["delivery"]["idempotency_key"] == (v2["idempotency_key"] or v2["id"]),
        v3["causality"]["correlation_id"] == v2["correlation_id"],
        v3["causality"]["causation_id"] == v2["causation_id"],
        v3["payload"]["evidence"] == v2["evidence"],
        v3["payload"]["artifacts"] == v2["artifacts"],
        v3["payload"]["supersedes"] == v2["supersedes"],
        v3["integrity"]["payload_sha256"] == _sha256(v3["payload"]),
        v3["integrity"]["canonical_envelope_sha256"] == _sha256(_envelope_digest_input(v3)),
    ]
    if not all(checks):
        raise AssertionError("v2 -> v3 shadow projection changed protected semantics")
    return True


def shadow_projection_fingerprint(message: dict) -> str:
    projected = project_v2_to_v3(message)
    assert_semantic_projection(message, projected)
    return projected["integrity"]["canonical_envelope_sha256"]
