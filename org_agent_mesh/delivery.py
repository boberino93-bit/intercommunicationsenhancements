from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
import hashlib
import json
import os

from .control_plane import require_active_session
from .message_bus import append_message, validate_message
from .project_scope import qualify, require_project_id

ACK_STATES = ("RECEIVED", "ACCEPTED", "STARTED", "COMPLETED", "FAILED", "REJECTED")
TERMINAL_ACK_STATES = {"COMPLETED", "REJECTED"}


class DeliveryStateError(RuntimeError):
    pass


class RetryExhausted(RuntimeError):
    pass


def _utc_now(now=None):
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return value.astimezone(timezone.utc)


def _utc_iso(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class DeliveryRecord:
    project_id: str
    message_id: str
    idempotency_key: str
    status: str
    attempts: int
    max_attempts: int
    last_error: str | None
    updated_at_utc: str


_ALLOWED = {
    "RECEIVED": {"ACCEPTED", "REJECTED"},
    "ACCEPTED": {"STARTED", "FAILED", "REJECTED"},
    "STARTED": {"COMPLETED", "FAILED", "REJECTED"},
    "FAILED": {"ACCEPTED", "REJECTED"},
    "COMPLETED": set(),
    "REJECTED": set(),
}


class DeliveryLedger:
    def __init__(self):
        self._records = {}
        self._lock = RLock()

    def register(self, message, *, recipient_session, max_attempts=3, now=None):
        binding = require_active_session(
            recipient_session,
            message.get("destination_project_id"),
            operation="delivery registration",
            capability="PUBLISH_MESSAGE",
        )
        validate_message(message, expected_project_id=binding.project_id, now=now)
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        project_id = require_project_id(message["project_id"])
        idempotency_key = message.get("idempotency_key") or message["id"]
        key = qualify(project_id, idempotency_key)
        with self._lock:
            existing = self._records.get(key)
            if existing is not None:
                return existing
            record = DeliveryRecord(project_id, message["id"], idempotency_key, "RECEIVED", 1, max_attempts, None, _utc_iso(_utc_now(now)))
            self._records[key] = record
            return record

    def get(self, project_id, idempotency_key):
        with self._lock:
            return self._records.get(qualify(project_id, idempotency_key))

    def transition(self, session, target_project_id, idempotency_key, status, *, error=None, now=None):
        require_active_session(
            session, target_project_id, operation="delivery acknowledgement", capability="PUBLISH_MESSAGE"
        )
        if status not in ACK_STATES:
            raise ValueError("unsupported acknowledgement state")
        key = qualify(target_project_id, idempotency_key)
        with self._lock:
            current = self._records.get(key)
            if current is None:
                raise DeliveryStateError("delivery record not found")
            if status == current.status:
                return current
            if status not in _ALLOWED[current.status]:
                raise DeliveryStateError(f"invalid acknowledgement transition: {current.status} -> {status}")
            updated = replace(current, status=status, last_error=error if status == "FAILED" else current.last_error, updated_at_utc=_utc_iso(_utc_now(now)))
            self._records[key] = updated
            return updated

    def retry(self, session, target_project_id, idempotency_key, *, now=None):
        require_active_session(
            session, target_project_id, operation="delivery retry", capability="PUBLISH_MESSAGE"
        )
        key = qualify(target_project_id, idempotency_key)
        with self._lock:
            current = self._records.get(key)
            if current is None:
                raise DeliveryStateError("delivery record not found")
            if current.status != "FAILED":
                raise DeliveryStateError("only failed delivery may be retried")
            if current.attempts >= current.max_attempts:
                raise RetryExhausted("delivery retry budget exhausted")
            updated = replace(current, status="ACCEPTED", attempts=current.attempts + 1, updated_at_utc=_utc_iso(_utc_now(now)))
            self._records[key] = updated
            return updated


def quarantine_message(quarantine_dir, message, reason, *, expected_project_id=None, now=None):
    local_project = expected_project_id or "unbound"
    try:
        local_project = require_project_id(local_project)
    except Exception:
        local_project = "unbound"
    directory = Path(quarantine_dir) / local_project
    directory.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(message, sort_keys=True, default=str).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    timestamp = _utc_iso(_utc_now(now))
    record = {
        "schema": "org-agent-mesh/quarantine-record/v1",
        "local_project_id": local_project,
        "claimed_project_id": message.get("project_id") if isinstance(message, dict) else None,
        "message_id": message.get("id") if isinstance(message, dict) else None,
        "reason": str(reason),
        "payload_sha256": digest,
        "quarantined_at_utc": timestamp,
        "payload": message,
    }
    path = directory / f"{digest}.json"
    payload = json.dumps(record, indent=2, sort_keys=True, default=str) + "\n"
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return path
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    return path


def safe_append_message(messages_dir, quarantine_dir, message, *, sender_session, expected_project_id=None, now=None):
    try:
        validate_message(
            message,
            expected_project_id=expected_project_id,
            sender_session=sender_session,
            now=now,
        )
    except Exception as exc:
        path = quarantine_message(quarantine_dir, message, exc, expected_project_id=expected_project_id, now=now)
        outcome = "EXPIRED" if "expired" in str(exc).lower() else "QUARANTINED"
        return {"outcome": outcome, "quarantine_path": path, "error": str(exc)}
    try:
        path = append_message(
            messages_dir,
            message,
            sender_session=sender_session,
            expected_project_id=expected_project_id,
            now=now,
        )
    except FileExistsError as exc:
        return {"outcome": "DUPLICATE", "error": str(exc)}
    return {"outcome": "ACCEPTED", "message_path": path}
