from __future__ import annotations

from datetime import datetime, timezone

from .control_plane import StaleVersion, require_active_session
from .durable_backend import CorruptDurableRecord, DurableRecordBackend
from .project_scope import require_project_id, require_resource_id


GENERATION_HEAD_RESOURCE = "current-generation"


class StaleGeneration(StaleVersion):
    """Raised when work targets a generation that is no longer current."""


def _utc_now(now=None):
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return value.astimezone(timezone.utc)


def _utc_iso(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _payload(record):
    if record is None:
        return None
    if not isinstance(record.payload, dict):
        raise CorruptDurableRecord("generation payload must be an object")
    return record.payload


class GenerationRegistry:
    """Crash-durable project-local generation head with CAS transition history.

    A generation is an accepted integration boundary. It is deliberately distinct
    from swarm_kernel ``global_run_id``, which identifies an operational execution
    run. This registry supplies a current-generation fence for V2-aware mutation
    paths; existing mutation surfaces must explicitly call ``assert_current``
    before the framework can claim a universal stale-generation guarantee.
    """

    NAMESPACE = "generation-heads"

    def __init__(self, backend):
        if not isinstance(backend, DurableRecordBackend):
            raise TypeError("backend must implement DurableRecordBackend")
        self.backend = backend

    @staticmethod
    def _snapshot(payload):
        return {
            "generation_id": payload["generation_id"],
            "parent_generation_id": payload.get("parent_generation_id"),
            "coordinator_epoch": payload.get("coordinator_epoch"),
            "protocol_version": payload["protocol_version"],
            "package_version": payload["package_version"],
            "reason": payload["reason"],
            "created_at_utc": payload["created_at_utc"],
            "status": payload.get("status", "SUPERSEDED"),
        }

    def initialize(
        self,
        session,
        target_project_id,
        generation_id,
        *,
        coordinator_epoch,
        protocol_version,
        package_version,
        reason,
        now=None,
    ):
        binding = require_active_session(
            session,
            target_project_id,
            operation="generation initialization",
            capability="WRITE_ACCEPTED_STATE",
        )
        generation_id = require_resource_id(generation_id, field="generation_id")
        coordinator_epoch = require_resource_id(coordinator_epoch, field="coordinator_epoch")
        if not protocol_version or not package_version or not reason:
            raise ValueError("protocol_version, package_version and reason are required")
        timestamp = _utc_iso(_utc_now(now))
        payload = {
            "generation_id": generation_id,
            "parent_generation_id": None,
            "coordinator_epoch": coordinator_epoch,
            "protocol_version": str(protocol_version),
            "package_version": str(package_version),
            "reason": str(reason),
            "status": "ACTIVE",
            "created_at_utc": timestamp,
            "updated_at_utc": timestamp,
            "updated_by_agent_instance_id": binding.agent_instance_id,
            "history": [],
        }
        return self.backend.create(
            self.NAMESPACE,
            target_project_id,
            GENERATION_HEAD_RESOURCE,
            payload,
            now=now,
        )

    def read_current(self, project_id):
        return self.backend.read(
            self.NAMESPACE,
            require_project_id(project_id),
            GENERATION_HEAD_RESOURCE,
        )

    def current_generation_id(self, project_id):
        current = self.read_current(project_id)
        return None if current is None else _payload(current).get("generation_id")

    def assert_current(self, project_id, generation_id):
        generation_id = require_resource_id(generation_id, field="generation_id")
        current = self.read_current(project_id)
        if current is None:
            raise StaleGeneration("no current generation is registered")
        payload = _payload(current)
        if payload.get("generation_id") != generation_id:
            raise StaleGeneration(
                f"stale generation {generation_id!r}; current generation is "
                f"{payload.get('generation_id')!r}"
            )
        return current

    def advance(
        self,
        session,
        target_project_id,
        generation_id,
        *,
        expected_version,
        coordinator_epoch,
        protocol_version,
        package_version,
        reason,
        now=None,
    ):
        binding = require_active_session(
            session,
            target_project_id,
            operation="generation transition",
            capability="WRITE_ACCEPTED_STATE",
        )
        generation_id = require_resource_id(generation_id, field="generation_id")
        coordinator_epoch = require_resource_id(coordinator_epoch, field="coordinator_epoch")
        current = self.read_current(target_project_id)
        if current is None:
            raise StaleGeneration("cannot advance an uninitialized generation registry")
        if current.version != expected_version:
            raise StaleVersion(
                f"stale generation-head version: expected {expected_version}, current {current.version}"
            )
        current_payload = dict(_payload(current))
        if current_payload.get("generation_id") == generation_id:
            return current
        if not protocol_version or not package_version or not reason:
            raise ValueError("protocol_version, package_version and reason are required")
        timestamp = _utc_iso(_utc_now(now))
        history = list(current_payload.get("history") or [])
        previous = self._snapshot(current_payload)
        previous["status"] = "SUPERSEDED"
        previous["superseded_at_utc"] = timestamp
        history.append(previous)
        payload = {
            "generation_id": generation_id,
            "parent_generation_id": current_payload["generation_id"],
            "coordinator_epoch": coordinator_epoch,
            "protocol_version": str(protocol_version),
            "package_version": str(package_version),
            "reason": str(reason),
            "status": "ACTIVE",
            "created_at_utc": timestamp,
            "updated_at_utc": timestamp,
            "updated_by_agent_instance_id": binding.agent_instance_id,
            "history": history,
        }
        return self.backend.compare_and_set(
            self.NAMESPACE,
            target_project_id,
            GENERATION_HEAD_RESOURCE,
            expected_version=expected_version,
            payload=payload,
            now=now,
        )
