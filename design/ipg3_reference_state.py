"""Thread-safe design reference state machines for IPG3 approval and effect semantics.

These classes demonstrate required atomic/CAS behavior only. They are not durable adapters
and MUST NOT be treated as production enforcement.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock

from ipg3_validators import IPG3ValidationError, _parse_utc, validate_human_approval


class StateConflict(RuntimeError):
    pass


class ApprovalDenied(RuntimeError):
    pass


class EffectConflict(RuntimeError):
    pass


@dataclass(frozen=True)
class VersionedRecord:
    record: dict
    version: int


def _now(now=None):
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return value.astimezone(timezone.utc)


def _iso(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _key(project_id, identity):
    return f"{project_id}::{identity}"


class ApprovalLedger:
    """In-memory reference for atomic single/multi-use approval consumption."""

    def __init__(self):
        self._records = {}
        self._lock = RLock()

    def register(self, approval: dict, *, now=None) -> VersionedRecord:
        validate_human_approval(approval, now=_now(now))
        key = _key(approval["project_id"], approval["approval_id"])
        with self._lock:
            existing = self._records.get(key)
            if existing is not None:
                if existing.record != approval:
                    raise StateConflict("approval identity already exists with different content")
                return existing
            value = VersionedRecord(deepcopy(approval), 0)
            self._records[key] = value
            return value

    def get(self, project_id: str, approval_id: str) -> VersionedRecord | None:
        with self._lock:
            value = self._records.get(_key(project_id, approval_id))
            return None if value is None else VersionedRecord(deepcopy(value.record), value.version)

    def consume(
        self,
        project_id: str,
        approval_id: str,
        *,
        operation_class: str,
        target_system: str,
        target_resource: str,
        scope_digest: str | None,
        expected_version: int,
        now=None,
    ) -> VersionedRecord:
        current_time = _now(now)
        key = _key(project_id, approval_id)
        with self._lock:
            current = self._records.get(key)
            if current is None:
                raise ApprovalDenied("approval not found")
            if current.version != expected_version:
                raise StateConflict("stale approval version")
            record = deepcopy(current.record)
            validate_human_approval(record, now=current_time)
            if record["status"] != "ISSUED":
                raise ApprovalDenied(f"approval is not actionable: {record['status']}")
            if _parse_utc(record["expires_at_utc"]) <= current_time:
                raise ApprovalDenied("approval expired")
            if record["operation_class"] != operation_class:
                raise ApprovalDenied("operation class outside approval")
            target = record["target"]
            if target["system"] != target_system or target["resource"] != target_resource:
                raise ApprovalDenied("effect target outside approval")
            if target.get("scope_digest") is not None and target["scope_digest"] != scope_digest:
                raise ApprovalDenied("scope digest outside approval")

            record["uses"] += 1
            if record["uses"] >= record["max_uses"]:
                record["status"] = "CONSUMED"
            updated = VersionedRecord(record, current.version + 1)
            self._records[key] = updated
            return VersionedRecord(deepcopy(record), updated.version)

    def revoke(self, project_id: str, approval_id: str, *, expected_version: int) -> VersionedRecord:
        key = _key(project_id, approval_id)
        with self._lock:
            current = self._records.get(key)
            if current is None:
                raise ApprovalDenied("approval not found")
            if current.version != expected_version:
                raise StateConflict("stale approval version")
            record = deepcopy(current.record)
            if record["status"] == "CONSUMED":
                raise ApprovalDenied("consumed approval cannot be retroactively revoked")
            record["status"] = "REVOKED"
            updated = VersionedRecord(record, current.version + 1)
            self._records[key] = updated
            return VersionedRecord(deepcopy(record), updated.version)


class EffectLedger:
    """In-memory reference for idempotent effect prepare/commit/recovery semantics."""

    def __init__(self):
        self._records = {}
        self._lock = RLock()

    def prepare(self, request: dict, *, now=None) -> tuple[str, VersionedRecord]:
        required = {
            "effect_id", "project_id", "task_id", "message_id", "idempotency_key", "operation",
            "target", "request_sha256", "committing_agent"
        }
        missing = sorted(required - set(request))
        if missing:
            raise IPG3ValidationError(f"effect request missing fields: {missing}")
        key = _key(request["project_id"], request["idempotency_key"])
        with self._lock:
            existing = self._records.get(key)
            if existing is not None:
                if existing.record["request_sha256"] != request["request_sha256"]:
                    raise EffectConflict("idempotency key reused with different request digest")
                return "REPLAY_MATCHED", VersionedRecord(deepcopy(existing.record), existing.version)

            timestamp = _iso(_now(now))
            record = {
                "schema": "org-agent-mesh/effect-receipt/v1-draft",
                "effect_id": request["effect_id"], "project_id": request["project_id"],
                "task_id": request["task_id"], "message_id": request["message_id"],
                "idempotency_key": request["idempotency_key"], "operation": request["operation"],
                "target": deepcopy(request["target"]), "request_sha256": request["request_sha256"],
                "committing_agent": deepcopy(request["committing_agent"]), "status": "PREPARED",
                "prepared_at_utc": timestamp, "committed_at_utc": None, "result": None,
                "resulting_version": None, "external_receipt": None,
                "replay_disposition": "NOT_APPLICABLE", "evidence_refs": [],
            }
            value = VersionedRecord(record, 0)
            self._records[key] = value
            return "PREPARED", VersionedRecord(deepcopy(record), 0)

    def get(self, project_id: str, idempotency_key: str) -> VersionedRecord | None:
        with self._lock:
            value = self._records.get(_key(project_id, idempotency_key))
            return None if value is None else VersionedRecord(deepcopy(value.record), value.version)

    def commit(
        self,
        project_id: str,
        idempotency_key: str,
        *,
        request_sha256: str,
        external_receipt,
        result,
        resulting_version=None,
        evidence_refs=None,
        expected_version: int,
        now=None,
    ) -> VersionedRecord:
        key = _key(project_id, idempotency_key)
        with self._lock:
            current = self._records.get(key)
            if current is None:
                raise EffectConflict("effect not prepared")
            if current.record["request_sha256"] != request_sha256:
                raise EffectConflict("effect request digest mismatch")
            if current.record["status"] == "COMMITTED":
                duplicate = deepcopy(current.record)
                duplicate["status"] = "DUPLICATE_NOOP"
                duplicate["committed_at_utc"] = None
                duplicate["replay_disposition"] = "REPLAY_MATCHED"
                return VersionedRecord(duplicate, current.version)
            if current.version != expected_version:
                raise StateConflict("stale effect version")
            if current.record["status"] not in {"PREPARED", "UNKNOWN"}:
                raise EffectConflict(f"effect cannot commit from {current.record['status']}")

            record = deepcopy(current.record)
            record["status"] = "COMMITTED"
            record["committed_at_utc"] = _iso(_now(now))
            record["result"] = deepcopy(result)
            record["resulting_version"] = resulting_version
            record["external_receipt"] = deepcopy(external_receipt)
            record["replay_disposition"] = "FIRST_COMMIT"
            record["evidence_refs"] = list(evidence_refs or [])
            updated = VersionedRecord(record, current.version + 1)
            self._records[key] = updated
            return VersionedRecord(deepcopy(record), updated.version)

    def mark_unknown(self, project_id: str, idempotency_key: str, *, expected_version: int) -> VersionedRecord:
        key = _key(project_id, idempotency_key)
        with self._lock:
            current = self._records.get(key)
            if current is None:
                raise EffectConflict("effect not prepared")
            if current.version != expected_version:
                raise StateConflict("stale effect version")
            if current.record["status"] != "PREPARED":
                raise EffectConflict("only prepared effects may become UNKNOWN")
            record = deepcopy(current.record)
            record["status"] = "UNKNOWN"
            record["replay_disposition"] = "NOT_APPLICABLE"
            updated = VersionedRecord(record, current.version + 1)
            self._records[key] = updated
            return VersionedRecord(deepcopy(record), updated.version)

    def fail_unknown(self, project_id: str, idempotency_key: str, *, expected_version: int, evidence_refs=None) -> VersionedRecord:
        key = _key(project_id, idempotency_key)
        with self._lock:
            current = self._records.get(key)
            if current is None or current.record["status"] != "UNKNOWN":
                raise EffectConflict("only UNKNOWN effects may be resolved as failed")
            if current.version != expected_version:
                raise StateConflict("stale effect version")
            record = deepcopy(current.record)
            record["status"] = "FAILED"
            record["evidence_refs"] = list(evidence_refs or [])
            record["replay_disposition"] = "REPLAY_REJECTED"
            updated = VersionedRecord(record, current.version + 1)
            self._records[key] = updated
            return VersionedRecord(deepcopy(record), updated.version)
