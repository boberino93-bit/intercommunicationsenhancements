from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
import uuid

from .control_plane import require_active_session
from .project_scope import require_resource_id


def _utc_iso(now=None):
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class AuditRecord:
    project_id: str
    audit_id: str
    agent_id: str
    agent_instance_id: str
    task_id: str | None
    message_id: str | None
    resource_id: str | None
    operation: str
    result: str
    before_version: int | None
    after_version: int | None
    timestamp_utc: str
    details: dict


class AuditLedger:
    """Append-only in-process audit reference ledger."""

    def __init__(self):
        self._records = []
        self._lock = RLock()

    def record(self, session, target_project_id, *, operation, result, task_id=None, message_id=None, resource_id=None, before_version=None, after_version=None, details=None, now=None):
        binding = require_active_session(session, target_project_id, operation="audit append")
        for value, field in ((task_id, "task_id"), (message_id, "message_id"), (resource_id, "resource_id")):
            if value is not None:
                require_resource_id(value, field=field)
        if not operation or not result:
            raise ValueError("operation and result are required")
        record = AuditRecord(
            target_project_id,
            f"audit-{uuid.uuid4().hex}",
            binding.agent_id,
            binding.agent_instance_id,
            task_id,
            message_id,
            resource_id,
            str(operation),
            str(result),
            before_version,
            after_version,
            _utc_iso(now),
            dict(details or {}),
        )
        with self._lock:
            self._records.append(record)
        return record

    def read_project(self, project_id):
        with self._lock:
            return tuple(record for record in self._records if record.project_id == project_id)
