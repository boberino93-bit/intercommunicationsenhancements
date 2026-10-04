from dataclasses import dataclass, replace
from datetime import datetime, timezone
from threading import RLock

from .control_plane import StaleVersion, require_active_session
from .project_scope import ProjectScopeError, qualify, require_resource_id

TASK_STATES = ("OPEN", "ACTIVE", "BLOCKED", "COMPLETED", "FAILED", "CANCELLED")
TERMINAL_TASK_STATES = {"COMPLETED", "FAILED", "CANCELLED"}


def _utc_iso(now=None):
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class TaskRecord:
    project_id: str
    task_id: str
    creator_agent_id: str
    creator_agent_instance_id: str
    owner_agent_id: str | None
    owner_agent_instance_id: str | None
    parent_task_id: str | None
    status: str
    version: int
    created_at_utc: str
    updated_at_utc: str


class TaskRegistry:
    """Atomic project-scoped task ownership with CAS and bound-session authorization."""

    def __init__(self):
        self._records = {}
        self._lock = RLock()

    def create(self, session, target_project_id, task_id, *, parent_task_id=None, now=None):
        binding = require_active_session(session, target_project_id, operation="task creation", capability="CLAIM_TASK")
        task_id = require_resource_id(task_id, field="task_id")
        if parent_task_id is not None:
            parent_task_id = require_resource_id(parent_task_id, field="parent_task_id")
        key = qualify(target_project_id, task_id)
        timestamp = _utc_iso(now)
        with self._lock:
            if key in self._records:
                raise StaleVersion("task already exists")
            record = TaskRecord(target_project_id, task_id, binding.agent_id, binding.agent_instance_id, None, None, parent_task_id, "OPEN", 1, timestamp, timestamp)
            self._records[key] = record
            return record

    def read(self, project_id, task_id):
        with self._lock:
            return self._records.get(qualify(project_id, task_id))

    def claim(self, session, target_project_id, task_id, *, expected_version, now=None):
        binding = require_active_session(session, target_project_id, operation="task claim", capability="CLAIM_TASK")
        key = qualify(target_project_id, require_resource_id(task_id, field="task_id"))
        with self._lock:
            current = self._records.get(key)
            if current is None:
                raise KeyError("task not found")
            if current.status == "ACTIVE" and current.owner_agent_instance_id == binding.agent_instance_id:
                return current
            if current.version != expected_version:
                raise StaleVersion(f"stale task version: expected {expected_version}, current {current.version}")
            if current.status not in {"OPEN", "BLOCKED"}:
                raise RuntimeError(f"task cannot be claimed from state {current.status}")
            updated = replace(current, owner_agent_id=binding.agent_id, owner_agent_instance_id=binding.agent_instance_id, status="ACTIVE", version=current.version + 1, updated_at_utc=_utc_iso(now))
            self._records[key] = updated
            return updated

    def transition(self, session, target_project_id, task_id, *, expected_version, status, now=None):
        binding = require_active_session(session, target_project_id, operation="task transition", capability="CLAIM_TASK")
        if status not in TASK_STATES:
            raise ValueError("unsupported task state")
        key = qualify(target_project_id, require_resource_id(task_id, field="task_id"))
        with self._lock:
            current = self._records.get(key)
            if current is None:
                raise KeyError("task not found")
            if current.version != expected_version:
                raise StaleVersion(f"stale task version: expected {expected_version}, current {current.version}")
            if current.status in TERMINAL_TASK_STATES:
                raise RuntimeError("terminal task state cannot transition")
            owner_match = current.owner_agent_instance_id == binding.agent_instance_id
            can_override = "APPROVE_CHANGE" in binding.capabilities
            if current.owner_agent_instance_id is not None and not owner_match and not can_override:
                raise ProjectScopeError("task transition denied for non-owner execution instance")
            updated = replace(current, status=status, version=current.version + 1, updated_at_utc=_utc_iso(now))
            self._records[key] = updated
            return updated
