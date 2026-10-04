from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Mapping

from .control_plane import StaleVersion, require_active_session
from .durable_backend import CorruptDurableRecord, DurableRecordBackend
from .project_scope import ProjectScopeError, require_project_id, require_repository_identity, require_resource_id

PROJECT_FIELDS = {
    "project_id", "repository_identity", "repository_revision", "protocol_version",
    "package_version", "health_state", "generation_id", "active_objective_id",
    "active_claims", "open_dependencies", "blocked_tasks", "last_checkpoint_ref",
    "updated_at_utc",
}
SWARM_FIELDS = {
    "swarm_id", "coordinator_epoch", "protocol_version", "project_capsules",
    "quarantined_projects", "global_freeze", "updated_at_utc",
}


def _utc_now(now=None):
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return value.astimezone(timezone.utc)


def _utc_iso(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def capsule_digest(payload):
    return sha256(_canonical(payload).encode()).hexdigest()


def validate_project_capsule(capsule: Mapping):
    if not isinstance(capsule, Mapping):
        raise ValueError("project capsule must be an object")
    unknown = sorted(set(capsule) - PROJECT_FIELDS)
    missing = sorted(PROJECT_FIELDS - set(capsule))
    if unknown:
        raise ProjectScopeError(f"project capsule contains unknown fields: {unknown}")
    if missing:
        raise ValueError(f"project capsule missing fields: {missing}")
    require_project_id(capsule["project_id"])
    require_repository_identity(capsule["repository_identity"])
    for field in ("repository_revision", "protocol_version", "package_version", "health_state", "updated_at_utc"):
        if not isinstance(capsule[field], str) or not capsule[field].strip():
            raise ValueError(f"{field} must be a non-empty string")
    for field in ("active_claims", "open_dependencies", "blocked_tasks"):
        if not isinstance(capsule[field], list) or not all(isinstance(v, str) and v for v in capsule[field]):
            raise ValueError(f"{field} must be a list of non-empty strings")
    for field in ("generation_id", "active_objective_id", "last_checkpoint_ref"):
        if capsule[field] is not None and (not isinstance(capsule[field], str) or not capsule[field]):
            raise ValueError(f"{field} must be null or a non-empty string")
    return True


def validate_swarm_capsule(capsule: Mapping):
    if not isinstance(capsule, Mapping):
        raise ValueError("swarm capsule must be an object")
    unknown = sorted(set(capsule) - SWARM_FIELDS)
    missing = sorted(SWARM_FIELDS - set(capsule))
    if unknown:
        raise ProjectScopeError(f"swarm capsule contains unknown fields: {unknown}")
    if missing:
        raise ValueError(f"swarm capsule missing fields: {missing}")
    require_resource_id(capsule["swarm_id"], field="swarm_id")
    require_resource_id(capsule["coordinator_epoch"], field="coordinator_epoch")
    if not isinstance(capsule["project_capsules"], list) or not capsule["project_capsules"]:
        raise ValueError("project_capsules must be a non-empty list")
    ids = []
    for item in capsule["project_capsules"]:
        validate_project_capsule(item)
        ids.append(item["project_id"])
    if len(ids) != len(set(ids)):
        raise ValueError("swarm capsule contains duplicate project ids")
    if not isinstance(capsule["quarantined_projects"], list):
        raise ValueError("quarantined_projects must be a list")
    if not isinstance(capsule["global_freeze"], bool):
        raise ValueError("global_freeze must be boolean")
    return True


class StateCapsuleRegistry:
    PROJECT_NAMESPACE = "project-capsules"
    SWARM_NAMESPACE = "swarm-capsules"

    def __init__(self, backend: DurableRecordBackend):
        if not isinstance(backend, DurableRecordBackend):
            raise TypeError("backend must implement DurableRecordBackend")
        self.backend = backend

    @staticmethod
    def _write(backend, namespace, session, target_project_id, resource_id, payload, *, expected_version=None, now=None):
        require_active_session(session, target_project_id, operation="state capsule publication", capability="WRITE_ACCEPTED_STATE")
        current = backend.read(namespace, target_project_id, resource_id)
        if current is None:
            if expected_version not in (None, 0):
                raise StaleVersion("capsule does not exist")
            return backend.create(namespace, target_project_id, resource_id, payload, now=now)
        if current.payload == payload:
            return current
        if expected_version is None:
            raise StaleVersion("expected_version required for capsule replacement")
        if current.version != expected_version:
            raise StaleVersion(f"stale capsule version: expected {expected_version}, current {current.version}")
        return backend.compare_and_set(namespace, target_project_id, resource_id, expected_version=expected_version, payload=payload, now=now)

    def publish_project(self, session, target_project_id, capsule, *, expected_version=None, now=None):
        validate_project_capsule(capsule)
        if capsule["project_id"] != target_project_id:
            raise ProjectScopeError("project capsule identity does not match owning project")
        payload = dict(capsule)
        payload["updated_at_utc"] = _utc_iso(_utc_now(now))
        record = self._write(self.backend, self.PROJECT_NAMESPACE, session, target_project_id, "current", payload, expected_version=expected_version, now=now)
        if not isinstance(record.payload, dict):
            raise CorruptDurableRecord("project capsule payload corrupt")
        return record

    def read_project(self, project_id):
        return self.backend.read(self.PROJECT_NAMESPACE, require_project_id(project_id), "current")

    def publish_swarm(self, session, target_project_id, capsule, *, expected_version=None, now=None):
        validate_swarm_capsule(capsule)
        payload = dict(capsule)
        payload["updated_at_utc"] = _utc_iso(_utc_now(now))
        return self._write(self.backend, self.SWARM_NAMESPACE, session, target_project_id, require_resource_id(capsule["swarm_id"], field="swarm_id"), payload, expected_version=expected_version, now=now)

    def read_swarm(self, project_id, swarm_id):
        return self.backend.read(self.SWARM_NAMESPACE, require_project_id(project_id), require_resource_id(swarm_id, field="swarm_id"))
