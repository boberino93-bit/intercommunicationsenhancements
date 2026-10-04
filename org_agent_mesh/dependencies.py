from __future__ import annotations

from datetime import datetime, timezone

from .control_plane import StaleVersion, require_active_session
from .durable_backend import CorruptDurableRecord, DurableRecordBackend
from .project_scope import require_project_id, require_resource_id


DEPENDENCY_STATUSES = {"OPEN", "IN_PROGRESS", "RESOLVED", "INVALIDATED", "SUPERSEDED", "BLOCKED"}


class DependencyCycleError(RuntimeError):
    pass


class RendezvousStateError(RuntimeError):
    pass


def _utc_now(now=None):
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return value.astimezone(timezone.utc)


def _utc_iso(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_utc(value, field):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _payload(record):
    if record is None:
        return None
    if not isinstance(record.payload, dict):
        raise CorruptDurableRecord("coordination payload must be an object")
    return record.payload


class DependencyRegistry:
    """Durable project-local dependency graph using backend CAS records.

    Edges describe data/work dependency only. They never convey capabilities or
    authority. Topology is generation-scoped so stale-generation evidence cannot
    alter the current generation's cycle analysis. Optional generation_registry
    fencing rejects normal stale-generation writes before persistence as well.
    """

    NAMESPACE = "dependencies"

    def __init__(self, backend, *, generation_registry=None):
        if not isinstance(backend, DurableRecordBackend):
            raise TypeError("backend must implement DurableRecordBackend")
        self.backend = backend
        self.generation_registry = generation_registry

    def _edges(self, project_id, generation_id):
        edges = []
        for durable in self.backend.list_records(self.NAMESPACE, project_id=project_id):
            payload = _payload(durable)
            if payload.get("generation_id") != generation_id:
                continue
            if payload.get("status") in {"INVALIDATED", "SUPERSEDED"}:
                continue
            producer = payload.get("producer_task_or_node")
            consumer = payload.get("consumer_task_or_node")
            if producer and consumer:
                edges.append((producer, consumer))
        return edges

    def _would_cycle(self, project_id, generation_id, producer, consumer):
        graph = {}
        for source, target in self._edges(project_id, generation_id):
            graph.setdefault(source, set()).add(target)
        graph.setdefault(producer, set()).add(consumer)
        stack = [consumer]
        visited = set()
        while stack:
            node = stack.pop()
            if node == producer:
                return True
            if node in visited:
                continue
            visited.add(node)
            stack.extend(graph.get(node, ()))
        return False

    def create(
        self,
        session,
        target_project_id,
        dependency_id,
        *,
        generation_id,
        producer_task_or_node,
        consumer_task_or_node,
        required_output,
        now=None,
    ):
        binding = require_active_session(
            session,
            target_project_id,
            operation="dependency creation",
            capability="CLAIM_TASK",
        )
        dependency_id = require_resource_id(dependency_id, field="dependency_id")
        generation_id = require_resource_id(generation_id, field="generation_id")
        producer = require_resource_id(producer_task_or_node, field="producer_task_or_node")
        consumer = require_resource_id(consumer_task_or_node, field="consumer_task_or_node")
        if producer == consumer:
            raise DependencyCycleError("dependency cannot target itself")
        if not required_output:
            raise ValueError("required_output is required")
        if self.generation_registry is not None:
            self.generation_registry.assert_current(target_project_id, generation_id)
        if self._would_cycle(target_project_id, generation_id, producer, consumer):
            raise DependencyCycleError("dependency would introduce a cycle")
        timestamp = _utc_iso(_utc_now(now))
        payload = {
            "dependency_id": dependency_id,
            "generation_id": generation_id,
            "producer_task_or_node": producer,
            "consumer_task_or_node": consumer,
            "required_output": str(required_output),
            "status": "OPEN",
            "created_at_utc": timestamp,
            "resolved_at_utc": None,
            "evidence_ref": None,
            "updated_by_agent_instance_id": binding.agent_instance_id,
        }
        return self.backend.create(
            self.NAMESPACE,
            target_project_id,
            dependency_id,
            payload,
            now=now,
        )

    def read(self, project_id, dependency_id):
        return self.backend.read(
            self.NAMESPACE,
            require_project_id(project_id),
            require_resource_id(dependency_id, field="dependency_id"),
        )

    def transition(
        self,
        session,
        target_project_id,
        dependency_id,
        *,
        expected_version,
        status,
        evidence_ref=None,
        now=None,
    ):
        binding = require_active_session(
            session,
            target_project_id,
            operation="dependency transition",
            capability="CLAIM_TASK",
        )
        if status not in DEPENDENCY_STATUSES:
            raise ValueError("unsupported dependency status")
        dependency_id = require_resource_id(dependency_id, field="dependency_id")
        current = self.read(target_project_id, dependency_id)
        if current is None:
            raise KeyError("dependency not found")
        if current.version != expected_version:
            raise StaleVersion(
                f"stale dependency version: expected {expected_version}, current {current.version}"
            )
        payload = dict(_payload(current))
        if self.generation_registry is not None:
            self.generation_registry.assert_current(target_project_id, payload["generation_id"])
        if status == "RESOLVED" and not evidence_ref:
            raise ValueError("resolved dependency requires evidence_ref")
        if payload.get("status") == "RESOLVED" and status != "RESOLVED":
            raise RuntimeError("resolved dependency is terminal in the reference registry")
        payload["status"] = status
        payload["evidence_ref"] = evidence_ref or payload.get("evidence_ref")
        if status == "RESOLVED":
            payload["resolved_at_utc"] = _utc_iso(_utc_now(now))
        payload["updated_by_agent_instance_id"] = binding.agent_instance_id
        return self.backend.compare_and_set(
            self.NAMESPACE,
            target_project_id,
            dependency_id,
            expected_version=expected_version,
            payload=payload,
            now=now,
        )


class RendezvousRegistry:
    """Durable convergence points with versioned immutable membership."""

    NAMESPACE = "rendezvous"

    def __init__(self, backend, *, generation_registry=None):
        if not isinstance(backend, DurableRecordBackend):
            raise TypeError("backend must implement DurableRecordBackend")
        self.backend = backend
        self.generation_registry = generation_registry

    def create(
        self,
        session,
        target_project_id,
        rendezvous_id,
        *,
        generation_id,
        required_nodes,
        optional_nodes=(),
        consumer,
        timeout_at_utc,
        now=None,
    ):
        binding = require_active_session(
            session,
            target_project_id,
            operation="rendezvous creation",
            capability="CLAIM_TASK",
        )
        rendezvous_id = require_resource_id(rendezvous_id, field="rendezvous_id")
        generation_id = require_resource_id(generation_id, field="generation_id")
        required = tuple(sorted({require_resource_id(node, field="required_node") for node in required_nodes}))
        optional = tuple(sorted({require_resource_id(node, field="optional_node") for node in optional_nodes}))
        if not required:
            raise ValueError("at least one required rendezvous node is required")
        if set(required) & set(optional):
            raise ValueError("required and optional rendezvous membership must be disjoint")
        consumer = require_resource_id(consumer, field="consumer")
        timeout = _parse_utc(timeout_at_utc, "timeout_at_utc")
        current_time = _utc_now(now)
        if timeout <= current_time:
            raise ValueError("rendezvous timeout must be in the future")
        if self.generation_registry is not None:
            self.generation_registry.assert_current(target_project_id, generation_id)
        payload = {
            "rendezvous_id": rendezvous_id,
            "generation_id": generation_id,
            "required_nodes": list(required),
            "optional_nodes": list(optional),
            "consumer": consumer,
            "timeout_at_utc": _utc_iso(timeout),
            "status": "OPEN",
            "arrivals": {},
            "created_at_utc": _utc_iso(current_time),
            "completed_at_utc": None,
            "updated_by_agent_instance_id": binding.agent_instance_id,
        }
        return self.backend.create(
            self.NAMESPACE,
            target_project_id,
            rendezvous_id,
            payload,
            now=now,
        )

    def read(self, project_id, rendezvous_id):
        return self.backend.read(
            self.NAMESPACE,
            require_project_id(project_id),
            require_resource_id(rendezvous_id, field="rendezvous_id"),
        )

    def record_arrival(
        self,
        session,
        target_project_id,
        rendezvous_id,
        *,
        expected_version,
        node_id,
        evidence_ref,
        now=None,
    ):
        binding = require_active_session(
            session,
            target_project_id,
            operation="rendezvous arrival",
            capability="CLAIM_TASK",
        )
        if not evidence_ref:
            raise ValueError("rendezvous arrival requires evidence_ref")
        node_id = require_resource_id(node_id, field="node_id")
        current = self.read(target_project_id, rendezvous_id)
        if current is None:
            raise KeyError("rendezvous not found")
        if current.version != expected_version:
            raise StaleVersion(
                f"stale rendezvous version: expected {expected_version}, current {current.version}"
            )
        payload = dict(_payload(current))
        if payload.get("status") != "OPEN":
            raise RendezvousStateError("rendezvous is no longer open")
        if self.generation_registry is not None:
            self.generation_registry.assert_current(target_project_id, payload["generation_id"])
        members = set(payload["required_nodes"]) | set(payload["optional_nodes"])
        if node_id not in members:
            raise RendezvousStateError("node is not a rendezvous member")
        arrivals = dict(payload.get("arrivals") or {})
        existing = arrivals.get(node_id)
        if existing is not None:
            if existing.get("evidence_ref") == evidence_ref:
                return current
            raise RendezvousStateError("node already arrived with different evidence")
        timestamp = _utc_iso(_utc_now(now))
        arrivals[node_id] = {
            "evidence_ref": str(evidence_ref),
            "arrived_at_utc": timestamp,
            "agent_instance_id": binding.agent_instance_id,
        }
        payload["arrivals"] = arrivals
        if set(payload["required_nodes"]).issubset(arrivals):
            payload["status"] = "COMPLETED"
            payload["completed_at_utc"] = timestamp
        payload["updated_by_agent_instance_id"] = binding.agent_instance_id
        return self.backend.compare_and_set(
            self.NAMESPACE,
            target_project_id,
            require_resource_id(rendezvous_id, field="rendezvous_id"),
            expected_version=expected_version,
            payload=payload,
            now=now,
        )

    def timeout(self, session, target_project_id, rendezvous_id, *, expected_version, now=None):
        binding = require_active_session(
            session,
            target_project_id,
            operation="rendezvous timeout",
            capability="CLAIM_TASK",
        )
        current = self.read(target_project_id, rendezvous_id)
        if current is None:
            raise KeyError("rendezvous not found")
        if current.version != expected_version:
            raise StaleVersion(
                f"stale rendezvous version: expected {expected_version}, current {current.version}"
            )
        payload = dict(_payload(current))
        if payload.get("status") != "OPEN":
            return current
        current_time = _utc_now(now)
        if current_time < _parse_utc(payload["timeout_at_utc"], "timeout_at_utc"):
            raise RendezvousStateError("rendezvous timeout has not been reached")
        payload["status"] = "TIMED_OUT"
        payload["missing_required_nodes"] = sorted(
            set(payload["required_nodes"]) - set(payload.get("arrivals") or {})
        )
        payload["timed_out_at_utc"] = _utc_iso(current_time)
        payload["updated_by_agent_instance_id"] = binding.agent_instance_id
        return self.backend.compare_and_set(
            self.NAMESPACE,
            target_project_id,
            require_resource_id(rendezvous_id, field="rendezvous_id"),
            expected_version=expected_version,
            payload=payload,
            now=now,
        )
