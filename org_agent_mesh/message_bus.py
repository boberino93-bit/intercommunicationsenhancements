from pathlib import Path
import hashlib
import json
import os
from datetime import datetime, timezone

from .constants import MESSAGE_KINDS, PROTOCOL_VERSION
from .control_plane import require_active_session
from .project_scope import ProjectScopeError, require_project_id, require_resource_id

REQUIRED = {
    "schema", "protocol_version", "id", "project_id", "destination_project_id", "timestamp_utc",
    "from_agent", "from_agent_instance_id", "from_role", "to", "kind", "priority", "subject", "summary",
    "applies_to_state", "evidence", "artifacts", "reply_to", "supersedes", "requires_ack", "tags",
    "correlation_id", "causation_id", "idempotency_key", "expires_at_utc"
}


def _parse_utc(value):
    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _storage_key(message):
    identity = message.get("idempotency_key") or message["id"]
    raw = f"{message['project_id']}\0{identity}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _atomic_create(path, payload):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError:
        raise
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def validate_message(message, *, expected_project_id=None, sender_session=None, now=None):
    if not isinstance(message, dict):
        raise ValueError("message must be an object")
    missing = sorted(REQUIRED - set(message))
    if missing:
        raise ValueError(f"Message missing fields: {missing}")

    project_id = require_project_id(message["project_id"])
    destination_project_id = require_project_id(message["destination_project_id"])
    require_resource_id(message["id"], field="message id")
    if message.get("correlation_id") is not None:
        require_resource_id(message["correlation_id"], field="correlation_id")
    if message.get("causation_id") is not None:
        require_resource_id(message["causation_id"], field="causation_id")
    if message.get("idempotency_key") is not None:
        require_resource_id(message["idempotency_key"], field="idempotency_key")

    if expected_project_id is not None and project_id != require_project_id(expected_project_id):
        raise ProjectScopeError("message project does not match expected local project")
    if project_id != destination_project_id:
        raise ProjectScopeError(
            "Internal message bus cannot cross project boundaries; use explicit exchange protocol"
        )

    if message["protocol_version"] != PROTOCOL_VERSION:
        raise ValueError(
            f"Protocol mismatch: {message['protocol_version']!r} != {PROTOCOL_VERSION!r}"
        )
    if message["kind"] not in MESSAGE_KINDS:
        raise ValueError("Unsupported message kind")
    if message["priority"] not in {"normal", "high", "critical"}:
        raise ValueError("Unsupported priority")
    if not isinstance(message["to"], list) or not message["to"]:
        raise ValueError("to must be a non-empty list")
    if not isinstance(message["supersedes"], list):
        raise ValueError("supersedes must be a list")
    if not isinstance(message["requires_ack"], bool):
        raise ValueError("requires_ack must be boolean")
    if not message["from_agent_instance_id"]:
        raise ValueError("from_agent_instance_id is required")

    if sender_session is not None:
        binding = require_active_session(
            sender_session,
            project_id,
            operation="message publication",
            capability="PUBLISH_MESSAGE",
        )
        if message["from_agent"] != binding.agent_id:
            raise ProjectScopeError("claimed message agent does not match bound session")
        if message["from_agent_instance_id"] != binding.agent_instance_id:
            raise ProjectScopeError("claimed message execution instance does not match bound session")

    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    expires = _parse_utc(message.get("expires_at_utc"))
    if expires is not None and expires <= now.astimezone(timezone.utc):
        raise ValueError("Message expired")
    return True


def append_message(messages_dir, message, *, sender_session, expected_project_id=None, now=None):
    validate_message(
        message,
        expected_project_id=expected_project_id,
        sender_session=sender_session,
        now=now,
    )
    directory = Path(messages_dir)
    directory.mkdir(parents=True, exist_ok=True)
    key = _storage_key(message)
    path = directory / f"{message['project_id']}__{key}.json"
    payload = json.dumps(message, indent=2, sort_keys=True) + "\n"
    try:
        _atomic_create(path, payload)
    except FileExistsError as exc:
        raise FileExistsError(
            f"Duplicate project-scoped idempotency identity: {message.get('idempotency_key') or message['id']}"
        ) from exc
    return path


def supersede_message(messages_dir, old_message, replacement, *, sender_session, expected_project_id=None):
    replacement = dict(replacement)
    if old_message["project_id"] != replacement["project_id"]:
        raise ProjectScopeError("message supersession cannot cross projects")
    replacement.setdefault("supersedes", [])
    if old_message["id"] not in replacement["supersedes"]:
        replacement["supersedes"].append(old_message["id"])
    replacement["kind"] = "SUPERSESSION"
    return append_message(
        messages_dir,
        replacement,
        sender_session=sender_session,
        expected_project_id=expected_project_id,
    )


def now_utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
