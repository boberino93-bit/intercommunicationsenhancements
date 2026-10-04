from dataclasses import dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
from threading import RLock

from .control_plane import StaleVersion, require_active_session
from .project_scope import qualify, require_resource_id


def _utc_iso(now=None):
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _digest(payload):
    if not isinstance(payload, (bytes, bytearray)):
        raise TypeError("artifact payload must be bytes")
    return sha256(bytes(payload)).hexdigest()


@dataclass(frozen=True)
class ArtifactRecord:
    project_id: str
    artifact_id: str
    creator_agent_id: str
    creator_agent_instance_id: str
    task_id: str | None
    artifact_type: str
    source: str
    content_sha256: str
    version: int
    created_at_utc: str
    updated_at_utc: str


class ArtifactRegistry:
    def __init__(self):
        self._records = {}
        self._lock = RLock()

    def publish(self, session, target_project_id, artifact_id, payload, *, artifact_type, source, task_id=None, now=None):
        binding = require_active_session(session, target_project_id, operation="artifact publication", capability="WRITE_ARTIFACTS")
        artifact_id = require_resource_id(artifact_id, field="artifact_id")
        if task_id is not None:
            task_id = require_resource_id(task_id, field="task_id")
        if not artifact_type or not source:
            raise ValueError("artifact_type and source are required")
        key = qualify(target_project_id, artifact_id)
        timestamp = _utc_iso(now)
        with self._lock:
            if key in self._records:
                raise StaleVersion("artifact already exists")
            record = ArtifactRecord(target_project_id, artifact_id, binding.agent_id, binding.agent_instance_id, task_id, str(artifact_type), str(source), _digest(payload), 1, timestamp, timestamp)
            self._records[key] = record
            return record

    def read(self, session, target_project_id, artifact_id):
        require_active_session(session, target_project_id, operation="artifact read", capability="READ_ARTIFACTS")
        with self._lock:
            return self._records.get(qualify(target_project_id, artifact_id))

    def replace(self, session, target_project_id, artifact_id, payload, *, expected_version, source, now=None):
        binding = require_active_session(session, target_project_id, operation="artifact replacement", capability="WRITE_ARTIFACTS")
        key = qualify(target_project_id, require_resource_id(artifact_id, field="artifact_id"))
        with self._lock:
            current = self._records.get(key)
            if current is None:
                raise KeyError("artifact not found")
            if current.version != expected_version:
                raise StaleVersion(f"stale artifact version: expected {expected_version}, current {current.version}")
            updated = replace(current, creator_agent_id=binding.agent_id, creator_agent_instance_id=binding.agent_instance_id, source=str(source), content_sha256=_digest(payload), version=current.version + 1, updated_at_utc=_utc_iso(now))
            self._records[key] = updated
            return updated
