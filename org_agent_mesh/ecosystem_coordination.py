from __future__ import annotations

from datetime import datetime
from typing import Mapping

from .control_plane import StaleVersion, require_active_session
from .durable_backend import CorruptDurableRecord, DurableRecordBackend
from .project_scope import (
    ProjectScopeError,
    require_project_id,
    require_repository_identity,
    require_resource_id,
)


COORDINATOR_REQUIRED_FIELDS = {
    "coordinator_agent_id",
    "coordinator_project_id",
    "epoch_id",
    "scope",
    "allowed_reads",
    "allowed_writes",
    "prohibited_actions",
    "start_time",
    "expiry_or_review_condition",
    "human_assignment_ref",
}

SANITIZED_PROJECT_SUMMARY_FIELDS = {
    "project_id",
    "project_name",
    "purpose",
    "status",
    "repository_identity",
    "canonical_branch",
    "board_root",
    "protocol_version",
    "package_version",
    "capacity_state",
    "backup_state",
    "recovery_state",
    "allowed_cross_project_links",
    "last_verified",
}


def _parse_utc(value, field):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware")
    return parsed


def validate_coordinator_claim(claim: Mapping):
    """Validate a human-designated ecosystem coordinator claim.

    This is intentionally a validation/detection contract, not a peer-project write
    authority service. A coordinator remains an existing PRIMARY and cross-project
    mutation stays denied unless a separate approved bridge authorizes it.
    """
    if not isinstance(claim, Mapping):
        raise ValueError("coordinator claim must be an object")
    missing = sorted(COORDINATOR_REQUIRED_FIELDS - set(claim))
    if missing:
        raise ValueError(f"coordinator claim missing fields: {missing}")
    require_resource_id(claim["coordinator_agent_id"], field="coordinator_agent_id")
    require_project_id(claim["coordinator_project_id"])
    require_resource_id(claim["epoch_id"], field="epoch_id")
    if claim["scope"] not in {"ECOSYSTEM_SCOPE", "BRIDGE_SCOPE"}:
        raise ValueError("unsupported coordinator scope")
    for field in ("allowed_reads", "allowed_writes", "prohibited_actions"):
        if not isinstance(claim[field], list):
            raise ValueError(f"{field} must be a list")
    if not claim["human_assignment_ref"]:
        raise ProjectScopeError("ecosystem coordinator claim requires human assignment")
    _parse_utc(claim["start_time"], "start_time")
    return True


def compare_coordinator_claims(first: Mapping, second: Mapping):
    """Detect duplicate coordinator claims without electing by assumption."""
    validate_coordinator_claim(first)
    validate_coordinator_claim(second)
    if first["epoch_id"] != second["epoch_id"]:
        return {
            "state": "DIFFERENT_EPOCHS",
            "freeze_global_mutations": False,
            "authoritative_claim": None,
        }
    first_identity = (first["coordinator_project_id"], first["coordinator_agent_id"])
    second_identity = (second["coordinator_project_id"], second["coordinator_agent_id"])
    if first_identity == second_identity:
        return {
            "state": "DUPLICATE_IDENTICAL_COORDINATOR",
            "freeze_global_mutations": False,
            "authoritative_claim": first_identity,
        }
    return {
        "state": "SPLIT_BRAIN_DETECTED",
        "freeze_global_mutations": True,
        "authoritative_claim": None,
        "preserve_both_claims": True,
        "resolution": "COMPARE_HUMAN_AND_ACTIVE_CONTRACT_AUTHORITY_THEN_SUPERSEDE",
    }


def validate_sanitized_project_summary(summary: Mapping):
    """Allow only the V2 ecosystem registry's sanitized project-summary fields."""
    if not isinstance(summary, Mapping):
        raise ValueError("project summary must be an object")
    unknown = sorted(set(summary) - SANITIZED_PROJECT_SUMMARY_FIELDS)
    if unknown:
        raise ProjectScopeError(
            f"sanitized project summary contains non-approved fields: {unknown}"
        )
    missing = sorted(SANITIZED_PROJECT_SUMMARY_FIELDS - set(summary))
    if missing:
        raise ValueError(f"sanitized project summary missing fields: {missing}")
    require_project_id(summary["project_id"])
    require_repository_identity(summary["repository_identity"])
    if not isinstance(summary["allowed_cross_project_links"], list):
        raise ValueError("allowed_cross_project_links must be a list")
    if not all(
        isinstance(item, str) and item for item in summary["allowed_cross_project_links"]
    ):
        raise ValueError("allowed_cross_project_links entries must be non-empty strings")
    for field in (
        "project_name",
        "purpose",
        "status",
        "canonical_branch",
        "board_root",
        "protocol_version",
        "package_version",
        "capacity_state",
        "backup_state",
        "recovery_state",
        "last_verified",
    ):
        if not isinstance(summary[field], str) or not summary[field].strip():
            raise ValueError(f"{field} must be a non-empty string")
    return True


def assert_summary_promotable(summary: Mapping):
    """Reject quarantined, recovering, or otherwise unverified peer state at promotion boundaries.

    Untrusted summaries may still be retained as evidence in a local sanitized registry;
    callers must pass this guard before treating a peer summary as promotable ecosystem truth.
    """
    validate_sanitized_project_summary(summary)
    if summary["status"] != "ACTIVE":
        raise ProjectScopeError("peer project is not ACTIVE and cannot be promoted")
    if summary["recovery_state"] != "VERIFIED":
        raise ProjectScopeError("peer recovery state is not VERIFIED")
    if summary["capacity_state"] in {"UNKNOWN", "UNSAFE", "EXHAUSTED", "QUARANTINED"}:
        raise ProjectScopeError("peer capacity/health state is not promotable")
    return True


class SanitizedEcosystemRegistry:
    """Project-owned copy-by-value registry of approved sanitized peer summaries.

    The durable record is owned by ``target_project_id`` (the local coordinator
    project). The summarized peer project remains data inside that local record.
    This never writes to the peer project and therefore does not grant cross-project
    mutation authority. The caller must obtain peer data through an independently
    authorized read/export path before publishing it here.
    """

    NAMESPACE = "ecosystem-summaries"

    def __init__(self, backend):
        if not isinstance(backend, DurableRecordBackend):
            raise TypeError("backend must implement DurableRecordBackend")
        self.backend = backend

    @staticmethod
    def _resource_id(peer_project_id):
        return require_resource_id(f"project-{require_project_id(peer_project_id)}")

    @staticmethod
    def _verify(record, peer_project_id):
        if record is None:
            return None
        payload = record.payload
        if not isinstance(payload, dict):
            raise CorruptDurableRecord("ecosystem summary payload must be an object")
        summary = payload.get("summary")
        validate_sanitized_project_summary(summary)
        if summary["project_id"] != peer_project_id:
            raise CorruptDurableRecord("ecosystem summary peer identity mismatch")
        if not payload.get("source_exchange_ref") or not payload.get("recorded_by_agent_instance_id"):
            raise CorruptDurableRecord("ecosystem summary provenance is incomplete")
        return record

    def read(self, local_project_id, peer_project_id):
        local_project_id = require_project_id(local_project_id)
        peer_project_id = require_project_id(peer_project_id)
        record = self.backend.read(
            self.NAMESPACE,
            local_project_id,
            self._resource_id(peer_project_id),
        )
        return self._verify(record, peer_project_id)

    def publish(
        self,
        session,
        target_project_id,
        summary,
        *,
        source_exchange_ref,
        expected_version=None,
        now=None,
    ):
        binding = require_active_session(
            session,
            target_project_id,
            operation="sanitized ecosystem summary publication",
            capability="WRITE_ACCEPTED_STATE",
        )
        validate_sanitized_project_summary(summary)
        if not source_exchange_ref:
            raise ValueError("source_exchange_ref is required")
        peer_project_id = summary["project_id"]
        resource_id = self._resource_id(peer_project_id)
        payload = {
            "summary": dict(summary),
            "source_exchange_ref": str(source_exchange_ref),
            "recorded_by_agent_instance_id": binding.agent_instance_id,
        }
        current = self.backend.read(self.NAMESPACE, target_project_id, resource_id)
        if current is None:
            if expected_version not in (None, 0):
                raise StaleVersion("ecosystem summary does not yet exist")
            record = self.backend.create(
                self.NAMESPACE,
                target_project_id,
                resource_id,
                payload,
                now=now,
            )
            return self._verify(record, peer_project_id)
        verified = self._verify(current, peer_project_id)
        if verified.payload == payload:
            return verified
        if expected_version is None:
            raise StaleVersion("expected_version is required to replace ecosystem summary")
        if current.version != expected_version:
            raise StaleVersion(
                f"stale ecosystem summary version: expected {expected_version}, current {current.version}"
            )
        record = self.backend.compare_and_set(
            self.NAMESPACE,
            target_project_id,
            resource_id,
            expected_version=expected_version,
            payload=payload,
            now=now,
        )
        return self._verify(record, peer_project_id)

    def list_local(self, local_project_id):
        local_project_id = require_project_id(local_project_id)
        records = []
        for record in self.backend.list_records(self.NAMESPACE, project_id=local_project_id):
            payload = record.payload
            if not isinstance(payload, dict) or not isinstance(payload.get("summary"), dict):
                raise CorruptDurableRecord("ecosystem registry contains malformed record")
            records.append(self._verify(record, payload["summary"].get("project_id")))
        return records
