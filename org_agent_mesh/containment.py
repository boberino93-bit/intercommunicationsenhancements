from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .control_plane import StaleVersion, require_active_session
from .durable_backend import CorruptDurableRecord, DurableRecordBackend
from .project_scope import require_project_id


HEALTH_STATES = {"HEALTHY", "DEGRADED", "QUARANTINED", "RECOVERING"}


def _utc_now(now=None):
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return value.astimezone(timezone.utc)


def _utc_iso(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)


class ContainmentStateError(RuntimeError):
    pass


class ProjectHealthRegistry:
    NAMESPACE = "project-health"
    RESOURCE = "health"

    def __init__(self, backend: DurableRecordBackend, *, required_recovery_probes=3, cooldown_seconds=60):
        if not isinstance(backend, DurableRecordBackend):
            raise TypeError("backend must implement DurableRecordBackend")
        if required_recovery_probes < 1 or cooldown_seconds < 0:
            raise ValueError("invalid recovery hysteresis configuration")
        self.backend = backend
        self.required_recovery_probes = int(required_recovery_probes)
        self.cooldown_seconds = int(cooldown_seconds)

    def initialize(self, session, target_project_id, *, now=None):
        binding = require_active_session(
            session, target_project_id, operation="health initialization", capability="WRITE_ACCEPTED_STATE"
        )
        timestamp = _utc_iso(_utc_now(now))
        payload = {
            "state": "HEALTHY",
            "reason": None,
            "trip_count": 0,
            "successful_recovery_probes": 0,
            "tripped_at_utc": None,
            "last_probe_at_utc": None,
            "updated_by_agent_instance_id": binding.agent_instance_id,
            "updated_at_utc": timestamp,
        }
        return self.backend.create(self.NAMESPACE, target_project_id, self.RESOURCE, payload, now=now)

    def read(self, project_id):
        record = self.backend.read(self.NAMESPACE, require_project_id(project_id), self.RESOURCE)
        if record is not None and not isinstance(record.payload, dict):
            raise CorruptDurableRecord("project health payload must be an object")
        return record

    def _cas(self, session, target_project_id, *, expected_version, mutate, now=None):
        binding = require_active_session(
            session, target_project_id, operation="health transition", capability="WRITE_ACCEPTED_STATE"
        )
        current = self.read(target_project_id)
        if current is None:
            raise KeyError("project health not initialized")
        if current.version != expected_version:
            raise StaleVersion(f"stale health version: expected {expected_version}, current {current.version}")
        payload = dict(current.payload)
        mutate(payload, binding, _utc_now(now))
        if payload.get("state") not in HEALTH_STATES:
            raise ContainmentStateError("invalid project health state")
        payload["updated_by_agent_instance_id"] = binding.agent_instance_id
        payload["updated_at_utc"] = _utc_iso(_utc_now(now))
        return self.backend.compare_and_set(
            self.NAMESPACE, target_project_id, self.RESOURCE,
            expected_version=expected_version, payload=payload, now=now,
        )

    def trip(self, session, target_project_id, *, expected_version, reason, hard_stop=False, now=None):
        if not reason:
            raise ValueError("trip reason is required")
        def mutate(payload, binding, current_time):
            payload["state"] = "QUARANTINED" if hard_stop else "DEGRADED"
            payload["reason"] = str(reason)
            payload["trip_count"] = int(payload.get("trip_count", 0)) + 1
            payload["successful_recovery_probes"] = 0
            payload["tripped_at_utc"] = _utc_iso(current_time)
        return self._cas(session, target_project_id, expected_version=expected_version, mutate=mutate, now=now)

    def begin_recovery(self, session, target_project_id, *, expected_version, now=None):
        def mutate(payload, binding, current_time):
            if payload["state"] not in {"DEGRADED", "QUARANTINED"}:
                raise ContainmentStateError("recovery requires degraded or quarantined state")
            payload["state"] = "RECOVERING"
            payload["successful_recovery_probes"] = 0
            payload["last_probe_at_utc"] = None
        return self._cas(session, target_project_id, expected_version=expected_version, mutate=mutate, now=now)

    def record_probe(self, session, target_project_id, *, expected_version, success, now=None):
        def mutate(payload, binding, current_time):
            if payload["state"] != "RECOVERING":
                raise ContainmentStateError("recovery probe requires RECOVERING state")
            payload["successful_recovery_probes"] = (
                int(payload.get("successful_recovery_probes", 0)) + 1 if success else 0
            )
            payload["last_probe_at_utc"] = _utc_iso(current_time)
            if not success:
                payload["state"] = "QUARANTINED"
                payload["reason"] = "recovery probe failed"
                payload["tripped_at_utc"] = _utc_iso(current_time)
        return self._cas(session, target_project_id, expected_version=expected_version, mutate=mutate, now=now)

    def rejoin(self, session, target_project_id, *, expected_version, now=None):
        def mutate(payload, binding, current_time):
            if payload["state"] != "RECOVERING":
                raise ContainmentStateError("rejoin requires RECOVERING state")
            if int(payload.get("successful_recovery_probes", 0)) < self.required_recovery_probes:
                raise ContainmentStateError("rejoin blocked by hysteresis probe threshold")
            tripped = _parse(payload["tripped_at_utc"]) if payload.get("tripped_at_utc") else current_time
            if current_time < tripped + timedelta(seconds=self.cooldown_seconds):
                raise ContainmentStateError("rejoin blocked by hysteresis cooldown")
            payload["state"] = "HEALTHY"
            payload["reason"] = None
        return self._cas(session, target_project_id, expected_version=expected_version, mutate=mutate, now=now)

    def assert_trusted_for_promotion(self, project_id):
        current = self.read(project_id)
        if current is None or current.payload.get("state") != "HEALTHY":
            raise ContainmentStateError("project is not trusted for promotion")
        return True
