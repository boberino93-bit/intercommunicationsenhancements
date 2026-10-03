from pathlib import Path
import json
import re
from datetime import datetime, timezone

from .constants import MESSAGE_KINDS, PROTOCOL_VERSION
from .project_scope import ProjectScopeError, require_project_id, require_same_project, qualify

REQUIRED = {
    "schema", "protocol_version", "id", "project_id", "destination_project_id", "timestamp_utc",
    "from_agent", "from_agent_instance_id", "from_role", "to", "kind", "priority", "subject", "summary",
    "applies_to_state", "evidence", "artifacts", "reply_to", "supersedes", "requires_ack", "tags",
    "correlation_id", "causation_id", "idempotency_key", "expires_at_utc"
}


def _safe(value):
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value)).strip("-") or "record"


def _parse_utc(value):
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_message(message, *, expected_project_id=None, allow_cross_project=False, now=None):
    missing = sorted(REQUIRED - set(message))
    if missing:
        raise ValueError(f"Message missing fields: {missing}")

    project_id = require_project_id(message["project_id"])
    destination_project_id = require_project_id(message["destination_project_id"])

    if expected_project_id is not None:
        require_same_project(expected_project_id, project_id, operation="message publication")

    if project_id != destination_project_id and not allow_cross_project:
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
    if not isinstance(message["to"], list):
        raise ValueError("to must be a list")
    if not isinstance(message["supersedes"], list):
        raise ValueError("supersedes must be a list")
    if not message["from_agent_instance_id"]:
        raise ValueError("from_agent_instance_id is required")

    now = now or datetime.now(timezone.utc)
    expires = _parse_utc(message.get("expires_at_utc"))
    if expires is not None and expires <= now:
        raise ValueError("Message expired")
    return True


def append_message(messages_dir, message, *, expected_project_id=None):
    validate_message(message, expected_project_id=expected_project_id)
    directory = Path(messages_dir)
    directory.mkdir(parents=True, exist_ok=True)
    qualified_id = qualify(message["project_id"], message["id"])
    path = directory / f"{_safe(message['timestamp_utc'])}__{_safe(qualified_id)}.json"
    if path.exists():
        raise FileExistsError(f"Immutable message already exists: {path.name}")

    idempotency_key = message.get("idempotency_key")
    if idempotency_key:
        for existing in directory.glob("*.json"):
            try:
                record = json.loads(existing.read_text(encoding="utf-8"))
            except Exception:
                continue
            if (
                record.get("project_id") == message["project_id"]
                and record.get("idempotency_key") == idempotency_key
            ):
                raise FileExistsError(
                    f"Duplicate idempotency key for project: {idempotency_key}"
                )

    path.write_text(json.dumps(message, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def supersede_message(messages_dir, old_message, replacement, *, expected_project_id=None):
    replacement = dict(replacement)
    require_same_project(
        old_message["project_id"], replacement["project_id"], operation="message supersession"
    )
    replacement.setdefault("supersedes", [])
    if old_message["id"] not in replacement["supersedes"]:
        replacement["supersedes"].append(old_message["id"])
    replacement["kind"] = "SUPERSESSION"
    return append_message(messages_dir, replacement, expected_project_id=expected_project_id)


def now_utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
