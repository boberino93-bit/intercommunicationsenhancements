from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Mapping

from .control_plane import require_active_session
from .cross_project import validate_cross_project_exchange
from .durable_backend import CorruptDurableRecord, DurableRecordBackend
from .operational_intelligence import AVAILABILITY_STATES
from .project_scope import ProjectScopeError, require_project_id, require_resource_id


REGISTRY_FIELDS = {
    "schema",
    "entry_id",
    "peer_project_id",
    "consumer_project_id",
    "themes",
    "expertise_tags",
    "capability_refs",
    "availability_state",
    "validated_at_utc",
    "expires_at_utc",
    "provenance_refs",
    "authority_conveyed",
}

ACCEPTANCE_FIELDS = {
    "schema",
    "receipt_id",
    "request_ref",
    "correlation_id",
    "requesting_project_id",
    "target_project_id",
    "status",
    "local_task_ref",
    "update_ref",
    "supersedes_ref",
    "created_at_utc",
    "expires_at_utc",
    "provenance_refs",
    "authority_conveyed",
}

ACCEPTANCE_STATES = {
    "ACCEPTED",
    "DECLINED",
    "UPDATE_PENDING",
    "UPDATE_ACCEPTED",
    "UPDATE_REJECTED",
    "SUPERSEDED",
}

SAFE_SNAPSHOT_CLASSIFICATIONS = {"PUBLIC", "INTERNAL_SANITIZED"}


def _parse_utc(value, field):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _now(now):
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return value.astimezone(timezone.utc)


def _require_string_list(value, field, *, nonempty=False):
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    if nonempty and not value:
        raise ValueError(f"{field} must not be empty")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{field} entries must be non-empty strings")


def _canonical_digest(payload):
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


def validate_registry_entry(entry: Mapping, *, now=None):
    if not isinstance(entry, Mapping):
        raise ValueError("registry entry must be an object")
    unknown = sorted(set(entry) - REGISTRY_FIELDS)
    if unknown:
        raise ProjectScopeError(f"registry entry contains non-sanitized fields: {unknown}")
    missing = sorted(REGISTRY_FIELDS - set(entry))
    if missing:
        raise ValueError(f"registry entry missing fields: {missing}")
    if entry["schema"] != "org-agent-mesh/operational-intelligence-registry-entry/v1":
        raise ValueError("unsupported registry entry schema")
    require_resource_id(entry["entry_id"], field="entry_id")
    peer = require_project_id(entry["peer_project_id"])
    consumer = require_project_id(entry["consumer_project_id"])
    if peer == consumer:
        raise ValueError("registry entry requires a distinct peer project")
    for field in ("themes", "expertise_tags", "capability_refs", "provenance_refs"):
        _require_string_list(entry[field], field, nonempty=(field == "provenance_refs"))
    if entry["availability_state"] not in AVAILABILITY_STATES - {"NOT_APPLICABLE"}:
        raise ValueError("registry entry requires explicit availability, including UNKNOWN")
    if entry["authority_conveyed"] is not False:
        raise ProjectScopeError("operational intelligence registry never conveys authority")
    validated = _parse_utc(entry["validated_at_utc"], "validated_at_utc")
    expires = _parse_utc(entry["expires_at_utc"], "expires_at_utc")
    current = _now(now)
    if expires <= validated:
        raise ValueError("expires_at_utc must be after validated_at_utc")
    if expires <= current:
        raise ProjectScopeError("registry entry is expired")
    if validated > current:
        raise ProjectScopeError("registry entry cannot be validated in the future")
    return True


class OperationalIntelligenceRegistry:
    """Project-owned copy-by-value registry of sanitized peer expertise/capability metadata."""

    NAMESPACE = "operational-intelligence-index"

    def __init__(self, backend: DurableRecordBackend):
        if not isinstance(backend, DurableRecordBackend):
            raise TypeError("backend must implement DurableRecordBackend")
        self.backend = backend

    def publish(self, session, local_project_id, entry, *, source_exchange_ref, expected_version=None, now=None):
        binding = require_active_session(
            session,
            local_project_id,
            operation="operational intelligence registry publication",
            capability="WRITE_ACCEPTED_STATE",
        )
        validate_registry_entry(entry, now=now)
        if entry["consumer_project_id"] != local_project_id:
            raise ProjectScopeError("registry entry consumer does not match local project")
        if not isinstance(source_exchange_ref, str) or not source_exchange_ref.strip():
            raise ValueError("source_exchange_ref is required")
        resource_id = require_resource_id(entry["entry_id"], field="entry_id")
        payload = {
            "entry": dict(entry),
            "source_exchange_ref": source_exchange_ref,
            "recorded_by_agent_instance_id": binding.agent_instance_id,
        }
        current = self.backend.read(self.NAMESPACE, local_project_id, resource_id)
        if current is None:
            if expected_version not in (None, 0):
                raise ProjectScopeError("registry entry does not yet exist")
            return self.backend.create(self.NAMESPACE, local_project_id, resource_id, payload, now=now)
        if current.payload == payload:
            return current
        if expected_version is None or current.version != expected_version:
            raise ProjectScopeError("registry entry replacement requires current expected_version")
        return self.backend.compare_and_set(
            self.NAMESPACE,
            local_project_id,
            resource_id,
            expected_version=expected_version,
            payload=payload,
            now=now,
        )

    def discover(self, local_project_id, *, themes=(), expertise_tags=(), capability_refs=(), now=None):
        local_project_id = require_project_id(local_project_id)
        wanted_themes = {str(item).lower() for item in themes}
        wanted_expertise = {str(item).lower() for item in expertise_tags}
        wanted_capabilities = {str(item).lower() for item in capability_refs}
        current = _now(now)
        matches = []
        for record in self.backend.list_records(self.NAMESPACE, project_id=local_project_id):
            payload = record.payload
            if not isinstance(payload, dict) or not isinstance(payload.get("entry"), dict):
                raise CorruptDurableRecord("operational intelligence registry payload is malformed")
            entry = payload["entry"]
            try:
                validate_registry_entry(entry, now=current)
            except ProjectScopeError as exc:
                if "expired" in str(exc):
                    continue
                raise
            entry_themes = {str(item).lower() for item in entry["themes"]}
            entry_expertise = {str(item).lower() for item in entry["expertise_tags"]}
            entry_capabilities = {str(item).lower() for item in entry["capability_refs"]}
            if wanted_themes and not wanted_themes.intersection(entry_themes):
                continue
            if wanted_expertise and not wanted_expertise.intersection(entry_expertise):
                continue
            if wanted_capabilities and not wanted_capabilities.intersection(entry_capabilities):
                continue
            matches.append(record)
        matches.sort(key=lambda rec: (rec.payload["entry"]["peer_project_id"], rec.payload["entry"]["entry_id"]))
        return matches


def validate_routing_lineage(*, correlation_id, origin_project_id, target_project_id, visited_project_ids):
    require_resource_id(correlation_id, field="correlation_id")
    origin = require_project_id(origin_project_id)
    target = require_project_id(target_project_id)
    if origin == target:
        raise ProjectScopeError("routing target cannot be the origin project")
    if not isinstance(visited_project_ids, list):
        raise ValueError("visited_project_ids must be a list")
    visited = [require_project_id(project_id) for project_id in visited_project_ids]
    if len(visited) != len(set(visited)):
        raise ProjectScopeError("routing lineage contains a cycle")
    if visited and visited[0] != origin:
        raise ProjectScopeError("routing lineage must begin with the origin project")
    if target in visited:
        raise ProjectScopeError("routing target already appears in lineage")
    return tuple(visited + [target])


def validate_acceptance_receipt(receipt: Mapping, *, now=None):
    if not isinstance(receipt, Mapping):
        raise ValueError("acceptance receipt must be an object")
    unknown = sorted(set(receipt) - ACCEPTANCE_FIELDS)
    if unknown:
        raise ProjectScopeError(f"acceptance receipt contains unsupported fields: {unknown}")
    missing = sorted(ACCEPTANCE_FIELDS - set(receipt))
    if missing:
        raise ValueError(f"acceptance receipt missing fields: {missing}")
    if receipt["schema"] != "org-agent-mesh/cross-project-acceptance-receipt/v1":
        raise ValueError("unsupported acceptance receipt schema")
    for field in ("receipt_id", "request_ref", "correlation_id"):
        require_resource_id(receipt[field], field=field)
    requester = require_project_id(receipt["requesting_project_id"])
    target = require_project_id(receipt["target_project_id"])
    if requester == target:
        raise ValueError("acceptance receipt requires distinct projects")
    status = receipt["status"]
    if status not in ACCEPTANCE_STATES:
        raise ValueError("unsupported acceptance receipt status")
    _require_string_list(receipt["provenance_refs"], "provenance_refs", nonempty=True)
    if receipt["authority_conveyed"] is not False:
        raise ProjectScopeError("acceptance receipts never convey authority")
    created = _parse_utc(receipt["created_at_utc"], "created_at_utc")
    expires = _parse_utc(receipt["expires_at_utc"], "expires_at_utc")
    current = _now(now)
    if expires <= created:
        raise ValueError("receipt expiry must be after creation")
    if expires <= current:
        raise ProjectScopeError("acceptance receipt is expired")
    if status == "ACCEPTED":
        if not isinstance(receipt["local_task_ref"], str) or not receipt["local_task_ref"].strip():
            raise ValueError("ACCEPTED receipt requires local_task_ref")
        if receipt["update_ref"] is not None or receipt["supersedes_ref"] is not None:
            raise ValueError("initial ACCEPTED receipt must not masquerade as an update")
    elif status == "DECLINED":
        if any(receipt[field] is not None for field in ("local_task_ref", "update_ref", "supersedes_ref")):
            raise ValueError("DECLINED receipt cannot carry task/update references")
    else:
        for field in ("update_ref", "supersedes_ref"):
            if not isinstance(receipt[field], str) or not receipt[field].strip():
                raise ValueError(f"{status} receipt requires {field}")
    return True


def routing_state(receipt: Mapping | None, *, now=None):
    if receipt is None:
        return "REQUESTED"
    validate_acceptance_receipt(receipt, now=now)
    return receipt["status"]


class SanitizedSnapshotBridge:
    """Two-phase immutable, copy-by-value bridge over an explicitly approved exchange.

    Export requires source-project authority and validates the canonical exchange.
    Import requires destination-project authority and copies only the immutable export
    into a destination-owned evidence namespace. Import never promotes accepted state.
    """

    EXPORT_NAMESPACE = "cross-project-snapshot-exports"
    IMPORT_NAMESPACE = "cross-project-snapshot-imports"

    def __init__(self, backend: DurableRecordBackend):
        if not isinstance(backend, DurableRecordBackend):
            raise TypeError("backend must implement DurableRecordBackend")
        self.backend = backend

    @staticmethod
    def _validate_snapshot(snapshot, *, now=None):
        required = {
            "schema", "snapshot_id", "subject", "summary", "artifact_refs", "provenance_refs",
            "created_at_utc", "expires_at_utc", "authority_conveyed"
        }
        if not isinstance(snapshot, Mapping):
            raise ValueError("snapshot must be an object")
        unknown = sorted(set(snapshot) - required)
        if unknown:
            raise ProjectScopeError(f"snapshot contains non-sanitized fields: {unknown}")
        missing = sorted(required - set(snapshot))
        if missing:
            raise ValueError(f"snapshot missing fields: {missing}")
        if snapshot["schema"] != "org-agent-mesh/sanitized-intelligence-snapshot/v1":
            raise ValueError("unsupported snapshot schema")
        require_resource_id(snapshot["snapshot_id"], field="snapshot_id")
        for field in ("subject", "summary"):
            if not isinstance(snapshot[field], str) or not snapshot[field].strip():
                raise ValueError(f"snapshot {field} must be non-empty")
        if len(snapshot["summary"]) > 12000:
            raise ValueError("snapshot summary exceeds sanitized bridge size bound")
        _require_string_list(snapshot["artifact_refs"], "artifact_refs")
        _require_string_list(snapshot["provenance_refs"], "provenance_refs", nonempty=True)
        if snapshot["authority_conveyed"] is not False:
            raise ProjectScopeError("snapshot never conveys authority")
        created = _parse_utc(snapshot["created_at_utc"], "created_at_utc")
        expires = _parse_utc(snapshot["expires_at_utc"], "expires_at_utc")
        current = _now(now)
        if expires <= created:
            raise ValueError("snapshot expiry must be after creation")
        if expires <= current:
            raise ProjectScopeError("snapshot is expired")
        return True

    def publish_export(self, source_session, exchange, snapshot, *, now=None):
        validate_cross_project_exchange(exchange, requester_session=source_session, now=now)
        binding = require_active_session(
            source_session,
            exchange["source_project_id"],
            operation="sanitized cross-project snapshot export",
            capability="WRITE_ACCEPTED_STATE",
        )
        self._validate_snapshot(snapshot, now=now)
        if exchange["data_classification"] not in SAFE_SNAPSHOT_CLASSIFICATIONS:
            raise ProjectScopeError("snapshot bridge accepts only PUBLIC or INTERNAL_SANITIZED exchanges")
        snapshot_id = require_resource_id(snapshot["snapshot_id"], field="snapshot_id")
        if _parse_utc(snapshot["expires_at_utc"], "snapshot expires_at_utc") > _parse_utc(exchange["expires_at_utc"], "exchange expires_at_utc"):
            raise ProjectScopeError("snapshot cannot outlive its approved exchange")
        package = {
            "schema": "org-agent-mesh/sanitized-snapshot-export/v1",
            "snapshot": dict(snapshot),
            "exchange": dict(exchange),
            "source_project_id": exchange["source_project_id"],
            "destination_project_id": exchange["destination_project_id"],
            "data_classification": exchange["data_classification"],
            "allowed_use": exchange["allowed_use"],
            "source_agent_instance_id": binding.agent_instance_id,
        }
        package["digest_sha256"] = _canonical_digest(package)
        current = self.backend.read(self.EXPORT_NAMESPACE, exchange["source_project_id"], snapshot_id)
        if current is not None:
            if current.payload == package:
                return current
            raise ProjectScopeError("snapshot export IDs are immutable")
        return self.backend.create(
            self.EXPORT_NAMESPACE,
            exchange["source_project_id"],
            snapshot_id,
            package,
            now=now,
        )

    def import_export(self, destination_session, *, source_project_id, snapshot_id, now=None):
        source_project_id = require_project_id(source_project_id)
        snapshot_id = require_resource_id(snapshot_id, field="snapshot_id")
        source_record = self.backend.read(self.EXPORT_NAMESPACE, source_project_id, snapshot_id)
        if source_record is None:
            raise ProjectScopeError("canonical source export does not exist")
        package = source_record.payload
        if not isinstance(package, dict):
            raise CorruptDurableRecord("snapshot export package is malformed")
        digest = package.get("digest_sha256")
        unsigned = dict(package)
        unsigned.pop("digest_sha256", None)
        if not isinstance(digest, str) or digest != _canonical_digest(unsigned):
            raise CorruptDurableRecord("snapshot export digest mismatch")
        if package.get("source_project_id") != source_project_id:
            raise CorruptDurableRecord("snapshot export source identity mismatch")
        destination_project_id = require_project_id(package.get("destination_project_id"))
        require_active_session(
            destination_session,
            destination_project_id,
            operation="sanitized cross-project snapshot import",
            capability="CROSS_PROJECT_EXCHANGE",
        )
        binding = require_active_session(
            destination_session,
            destination_project_id,
            operation="sanitized cross-project snapshot import",
            capability="WRITE_ACCEPTED_STATE",
        )
        exchange = package.get("exchange")
        if not isinstance(exchange, dict) or exchange.get("destination_project_id") != destination_project_id:
            raise CorruptDurableRecord("snapshot export destination identity mismatch")
        if exchange.get("source_project_id") != source_project_id:
            raise CorruptDurableRecord("snapshot export exchange source mismatch")
        if exchange.get("data_classification") not in SAFE_SNAPSHOT_CLASSIFICATIONS:
            raise ProjectScopeError("snapshot classification is not importable")
        current_time = _now(now)
        if _parse_utc(exchange.get("expires_at_utc"), "exchange expires_at_utc") <= current_time:
            raise ProjectScopeError("approved exchange is expired")
        snapshot = package.get("snapshot")
        self._validate_snapshot(snapshot, now=current_time)
        local_payload = {
            "schema": "org-agent-mesh/sanitized-snapshot-import/v1",
            "snapshot": dict(snapshot),
            "source_project_id": source_project_id,
            "source_export_version": source_record.version,
            "source_export_digest_sha256": digest,
            "source_exchange_id": exchange.get("exchange_id"),
            "data_classification": package.get("data_classification"),
            "allowed_use": package.get("allowed_use"),
            "imported_by_agent_instance_id": binding.agent_instance_id,
            "accepted_state": False,
            "authority_conveyed": False,
        }
        current = self.backend.read(self.IMPORT_NAMESPACE, destination_project_id, snapshot_id)
        if current is not None:
            if current.payload == local_payload:
                return current
            raise ProjectScopeError("snapshot import IDs are immutable")
        return self.backend.create(
            self.IMPORT_NAMESPACE,
            destination_project_id,
            snapshot_id,
            local_payload,
            now=now,
        )
