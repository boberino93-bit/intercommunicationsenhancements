from __future__ import annotations

from datetime import datetime, timezone

from .control_plane import StaleVersion, require_active_session
from .durable_backend import CorruptDurableRecord, DurableRecordBackend
from .project_scope import require_project_id, require_resource_id


CHECKPOINT_STATUSES = {"ACTIVE", "SUSPENDED", "READY_TO_RESUME", "RESUMED", "SUPERSEDED"}


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
        raise CorruptDurableRecord("continuity checkpoint payload must be an object")
    return record.payload


class ContinuityStateError(RuntimeError):
    pass


class OperationalCheckpointRegistry:
    """Durable, reconstructable checkpoint / suspend / handback / resume state.

    Stores concise operational state only: objective, requested outcome, assumptions,
    dependency identifiers and unexecuted plan steps. It is not a chain-of-thought store.
    """

    NAMESPACE = "continuity-checkpoints"

    def __init__(self, backend: DurableRecordBackend):
        if not isinstance(backend, DurableRecordBackend):
            raise TypeError("backend must implement DurableRecordBackend")
        self.backend = backend

    def create(
        self,
        session,
        target_project_id,
        checkpoint_id,
        *,
        objective,
        latest_user_request,
        base_revision,
        assumptions=(),
        dependency_ids=(),
        unexecuted_plan_steps=(),
        next_action=None,
        now=None,
    ):
        binding = require_active_session(
            session,
            target_project_id,
            operation="continuity checkpoint creation",
            capability="CLAIM_TASK",
        )
        checkpoint_id = require_resource_id(checkpoint_id, field="checkpoint_id")
        if not objective or not latest_user_request or not base_revision:
            raise ValueError("objective, latest_user_request, and base_revision are required")
        timestamp = _utc_iso(_utc_now(now))
        payload = {
            "checkpoint_id": checkpoint_id,
            "status": "ACTIVE",
            "objective": str(objective),
            "latest_user_request": str(latest_user_request),
            "base_revision": str(base_revision),
            "assumptions": [str(v) for v in assumptions],
            "dependency_ids": [require_resource_id(v, field="dependency_id") for v in dependency_ids],
            "unexecuted_plan_steps": [str(v) for v in unexecuted_plan_steps],
            "next_action": None if next_action is None else str(next_action),
            "owner_agent_instance_id": binding.agent_instance_id,
            "created_at_utc": timestamp,
            "updated_at_utc": timestamp,
            "suspended_at_utc": None,
            "handback": None,
            "resume": None,
        }
        return self.backend.create(self.NAMESPACE, target_project_id, checkpoint_id, payload, now=now)

    def read(self, project_id, checkpoint_id):
        return self.backend.read(
            self.NAMESPACE,
            require_project_id(project_id),
            require_resource_id(checkpoint_id, field="checkpoint_id"),
        )

    def _transition(self, session, target_project_id, checkpoint_id, *, expected_version, mutate, now=None):
        binding = require_active_session(
            session,
            target_project_id,
            operation="continuity checkpoint transition",
            capability="CLAIM_TASK",
        )
        current = self.read(target_project_id, checkpoint_id)
        if current is None:
            raise KeyError("continuity checkpoint not found")
        if current.version != expected_version:
            raise StaleVersion(
                f"stale checkpoint version: expected {expected_version}, current {current.version}"
            )
        payload = dict(_payload(current))
        mutate(payload, binding, _utc_now(now))
        if payload.get("status") not in CHECKPOINT_STATUSES:
            raise ContinuityStateError("invalid continuity checkpoint status")
        payload["updated_at_utc"] = _utc_iso(_utc_now(now))
        return self.backend.compare_and_set(
            self.NAMESPACE,
            target_project_id,
            require_resource_id(checkpoint_id, field="checkpoint_id"),
            expected_version=expected_version,
            payload=payload,
            now=now,
        )

    def suspend(self, session, target_project_id, checkpoint_id, *, expected_version, reason, now=None):
        if not reason:
            raise ValueError("suspension reason is required")

        def mutate(payload, binding, current_time):
            if payload["status"] != "ACTIVE":
                raise ContinuityStateError("only ACTIVE checkpoints may suspend")
            payload["status"] = "SUSPENDED"
            payload["suspended_at_utc"] = _utc_iso(current_time)
            payload["suspension_reason"] = str(reason)
            payload["suspended_by_agent_instance_id"] = binding.agent_instance_id

        return self._transition(
            session, target_project_id, checkpoint_id,
            expected_version=expected_version, mutate=mutate, now=now,
        )

    def handback(
        self,
        session,
        target_project_id,
        checkpoint_id,
        *,
        expected_version,
        evidence_ref,
        resolved_dependency_ids=(),
        canonical_revision,
        now=None,
    ):
        if not evidence_ref or not canonical_revision:
            raise ValueError("evidence_ref and canonical_revision are required")

        def mutate(payload, binding, current_time):
            if payload["status"] != "SUSPENDED":
                raise ContinuityStateError("handback requires SUSPENDED checkpoint")
            resolved = [require_resource_id(v, field="dependency_id") for v in resolved_dependency_ids]
            unknown = sorted(set(resolved) - set(payload.get("dependency_ids", [])))
            if unknown:
                raise ContinuityStateError(f"handback references unknown dependencies: {unknown}")
            payload["status"] = "READY_TO_RESUME"
            payload["handback"] = {
                "evidence_ref": str(evidence_ref),
                "resolved_dependency_ids": resolved,
                "canonical_revision": str(canonical_revision),
                "from_agent_instance_id": binding.agent_instance_id,
                "timestamp_utc": _utc_iso(current_time),
            }

        return self._transition(
            session, target_project_id, checkpoint_id,
            expected_version=expected_version, mutate=mutate, now=now,
        )

    def resume(
        self,
        session,
        target_project_id,
        checkpoint_id,
        *,
        expected_version,
        current_canonical_revision,
        validated_dependency_ids=(),
        now=None,
    ):
        if not current_canonical_revision:
            raise ValueError("current_canonical_revision is required")

        def mutate(payload, binding, current_time):
            if payload["status"] != "READY_TO_RESUME":
                raise ContinuityStateError("resume requires READY_TO_RESUME checkpoint")
            handback = payload.get("handback") or {}
            validated = [require_resource_id(v, field="dependency_id") for v in validated_dependency_ids]
            unresolved = sorted(set(payload.get("dependency_ids", [])) - set(validated))
            if unresolved:
                raise ContinuityStateError(f"resume has unresolved dependencies: {unresolved}")
            stale_base = str(current_canonical_revision) != str(payload["base_revision"])
            invalidated = list(payload.get("unexecuted_plan_steps", [])) if stale_base else []
            payload["status"] = "RESUMED"
            payload["resume"] = {
                "resumed_by_agent_instance_id": binding.agent_instance_id,
                "timestamp_utc": _utc_iso(current_time),
                "prior_base_revision": payload["base_revision"],
                "current_canonical_revision": str(current_canonical_revision),
                "handback_revision": handback.get("canonical_revision"),
                "stale_base_detected": stale_base,
                "invalidated_plan_steps": invalidated,
                "validated_dependency_ids": validated,
            }
            payload["base_revision"] = str(current_canonical_revision)
            payload["owner_agent_instance_id"] = binding.agent_instance_id
            if stale_base:
                payload["unexecuted_plan_steps"] = []

        return self._transition(
            session, target_project_id, checkpoint_id,
            expected_version=expected_version, mutate=mutate, now=now,
        )
