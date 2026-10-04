from __future__ import annotations

from hashlib import sha256

from .control_plane import StaleVersion, require_active_session
from .durable_backend import CorruptDurableRecord, DurableRecordBackend
from .generation import StaleGeneration
from .project_scope import require_project_id, require_resource_id


class GenerationStateStore:
    """Generation-partitioned accepted state.

    Generation and logical resource identity are embedded in each payload while the
    durable storage key is a collision-checked SHA-256 digest. A stale writer can at
    worst append or update its old generation partition; ``read_current`` never
    treats that record as current after the generation head advances.

    The store checks generation both before and after mutation. If a transition races
    the write, the write remains isolated in the origin generation and the caller gets
    ``StaleGeneration`` instead of an accepted-current result.
    """

    NAMESPACE = "generation-state"

    def __init__(self, backend, generation_registry):
        if not isinstance(backend, DurableRecordBackend):
            raise TypeError("backend must implement DurableRecordBackend")
        self.backend = backend
        self.generation_registry = generation_registry

    @staticmethod
    def _storage_id(generation_id, resource_id):
        generation_id = require_resource_id(generation_id, field="generation_id")
        resource_id = require_resource_id(resource_id, field="resource_id")
        identity = f"{len(generation_id)}:{generation_id}:{resource_id}"
        return f"gs-{sha256(identity.encode('utf-8')).hexdigest()}"

    @staticmethod
    def _verify(record, generation_id, resource_id):
        if record is None:
            return None
        payload = record.payload
        if not isinstance(payload, dict):
            raise CorruptDurableRecord("generation-state payload must be an object")
        if payload.get("generation_id") != generation_id or payload.get("resource_id") != resource_id:
            raise CorruptDurableRecord("generation-state storage-key collision or identity mismatch")
        if "value" not in payload or not payload.get("updated_by_agent_instance_id"):
            raise CorruptDurableRecord("generation-state payload is missing required fields")
        return record

    def read_generation(self, project_id, generation_id, resource_id):
        project_id = require_project_id(project_id)
        generation_id = require_resource_id(generation_id, field="generation_id")
        resource_id = require_resource_id(resource_id, field="resource_id")
        record = self.backend.read(
            self.NAMESPACE,
            project_id,
            self._storage_id(generation_id, resource_id),
        )
        return self._verify(record, generation_id, resource_id)

    def read_current(self, project_id, resource_id):
        generation_id = self.generation_registry.current_generation_id(project_id)
        if generation_id is None:
            return None
        return self.read_generation(project_id, generation_id, resource_id)

    def initialize(self, session, target_project_id, generation_id, resource_id, value, *, now=None):
        binding = require_active_session(
            session,
            target_project_id,
            operation="generation-state initialize",
            capability="WRITE_ACCEPTED_STATE",
        )
        generation_id = require_resource_id(generation_id, field="generation_id")
        resource_id = require_resource_id(resource_id, field="resource_id")
        self.generation_registry.assert_current(target_project_id, generation_id)
        record = self.backend.create(
            self.NAMESPACE,
            target_project_id,
            self._storage_id(generation_id, resource_id),
            {
                "generation_id": generation_id,
                "resource_id": resource_id,
                "value": value,
                "updated_by_agent_instance_id": binding.agent_instance_id,
            },
            now=now,
        )
        try:
            self.generation_registry.assert_current(target_project_id, generation_id)
        except StaleGeneration as exc:
            raise StaleGeneration(
                "generation advanced during write; record is isolated in the origin generation"
            ) from exc
        return self._verify(record, generation_id, resource_id)

    def compare_and_set(
        self,
        session,
        target_project_id,
        generation_id,
        resource_id,
        *,
        expected_version,
        value,
        now=None,
    ):
        binding = require_active_session(
            session,
            target_project_id,
            operation="generation-state mutation",
            capability="WRITE_ACCEPTED_STATE",
        )
        generation_id = require_resource_id(generation_id, field="generation_id")
        resource_id = require_resource_id(resource_id, field="resource_id")
        self.generation_registry.assert_current(target_project_id, generation_id)
        current = self.read_generation(target_project_id, generation_id, resource_id)
        if current is None:
            raise KeyError("generation-state record not found")
        if current.version != expected_version:
            raise StaleVersion(
                f"stale generation-state version: expected {expected_version}, current {current.version}"
            )
        record = self.backend.compare_and_set(
            self.NAMESPACE,
            target_project_id,
            self._storage_id(generation_id, resource_id),
            expected_version=expected_version,
            payload={
                "generation_id": generation_id,
                "resource_id": resource_id,
                "value": value,
                "updated_by_agent_instance_id": binding.agent_instance_id,
            },
            now=now,
        )
        try:
            self.generation_registry.assert_current(target_project_id, generation_id)
        except StaleGeneration as exc:
            raise StaleGeneration(
                "generation advanced during write; record is isolated in the origin generation"
            ) from exc
        return self._verify(record, generation_id, resource_id)
