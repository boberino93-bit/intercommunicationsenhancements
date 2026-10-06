from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Iterable, Mapping

from .durable_record_guard import validate_durable_record
from .project_scope import require_project_id

WORK_RECORD_SCHEMA = "org-agent-mesh/material-work-record/v1"
PERSISTENCE_RECEIPT_SCHEMA = "org-agent-mesh/dual-persistence-receipt/v1"
PERSISTENCE_HEALTH_SCHEMA = "org-agent-mesh/persistence-health/v1"

PERSISTENCE_PREPARED = "PERSISTENCE_PREPARED"
ARTIFACTORY_ONLY = "ARTIFACTORY_ONLY_RECOVERY_REQUIRED"
GITHUB_ONLY = "GITHUB_ONLY_RECOVERY_REQUIRED"
DIGEST_MISMATCH = "DIGEST_MISMATCH_QUARANTINED"
RECORD_CONFLICT = "RECORD_ID_DIGEST_CONFLICT_QUARANTINED"
DUAL_PERSISTENCE_CONFIRMED = "DUAL_PERSISTENCE_CONFIRMED"

SINK_ARTIFACTORY = "ARTIFACTORY_MESSAGE_FORUM"
SINK_GITHUB = "GITHUB_PROJECT_BACKUP"
SINKS = frozenset({SINK_ARTIFACTORY, SINK_GITHUB})

TERMINAL_OR_HANDOFF_STATES = frozenset({
    "READY",
    "HANDOFF_READY",
    "COMPLETE",
    "PROPOSAL_READY",
    "MANAGER_REVIEW_READY",
    "PRIMARY_REVIEW_READY",
    "RESEARCH_HANDOFF_READY",
    "MANAGER_HANDOFF_READY",
    "PRIMARY_PROPOSAL_READY",
})

PROHIBITED_FIELDS = frozenset({"ephemeral_value", "enrollment_material", "recovery_value"})
PROHIBITED_LABELS = (
    "Security-Token",
    "Primary-Security-Token",
    "Global-Security-Review-Token",
)


class DualPersistenceError(ValueError):
    pass


class PersistenceConflictError(DualPersistenceError):
    pass


class PersistenceBarrierError(DualPersistenceError):
    pass


def _require_nonempty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DualPersistenceError(f"{field_name} is required")
    return value.strip()


def _parse_time(value: str, field_name: str) -> datetime:
    text = _require_nonempty(value, field_name)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DualPersistenceError(f"{field_name} must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DualPersistenceError(f"{field_name} must be offset-aware")
    return parsed.astimezone(timezone.utc)


def _require_sha256(value: str, field_name: str) -> str:
    text = _require_nonempty(value, field_name)
    if not text.startswith("sha256:") or len(text) != 71:
        raise DualPersistenceError(f"{field_name} must be sha256")
    try:
        int(text[7:], 16)
    except ValueError as exc:
        raise DualPersistenceError(f"{field_name} must be sha256") from exc
    return text


def canonical_json(value: Mapping[str, object]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_digest(value: Mapping[str, object]) -> str:
    return "sha256:" + sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MaterialWorkRecord:
    record_id: str
    project_id: str
    run_id: str
    agent_id: str
    role: str
    work_id: str
    event_type: str
    sequence: int
    created_at: str
    summary: str
    payload: Mapping[str, object] = field(default_factory=dict)
    lane_id: str | None = None
    previous_record_digest: str | None = None
    supersedes_record_id: str | None = None
    authority_conveyed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_id", require_project_id(self.project_id))
        for name in ("record_id", "run_id", "agent_id", "role", "work_id", "event_type"):
            _require_nonempty(getattr(self, name), name)
        if not isinstance(self.sequence, int) or self.sequence < 0:
            raise DualPersistenceError("sequence must be a non-negative integer")
        _parse_time(self.created_at, "created_at")
        if not isinstance(self.summary, str):
            raise DualPersistenceError("summary must be a string")
        if not isinstance(self.payload, Mapping):
            raise DualPersistenceError("payload must be a mapping")
        if self.authority_conveyed is not False:
            raise DualPersistenceError("material work persistence cannot convey authority")
        if self.previous_record_digest is not None:
            _require_sha256(self.previous_record_digest, "previous_record_digest")
        if self.supersedes_record_id is not None:
            _require_nonempty(self.supersedes_record_id, "supersedes_record_id")
            if self.supersedes_record_id == self.record_id:
                raise DualPersistenceError("record cannot supersede itself")
        validate_durable_record(
            self.as_dict(),
            prohibited_fields=PROHIBITED_FIELDS,
            prohibited_labels=PROHIBITED_LABELS,
            context="material_work_record",
        )

    def as_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "schema": WORK_RECORD_SCHEMA,
            "record_id": self.record_id,
            "project_id": self.project_id,
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "role": self.role,
            "work_id": self.work_id,
            "event_type": self.event_type,
            "sequence": self.sequence,
            "created_at": self.created_at,
            "summary": self.summary,
            "payload": dict(self.payload),
            "authority_conveyed": False,
        }
        if self.lane_id is not None:
            result["lane_id"] = self.lane_id
        if self.previous_record_digest is not None:
            result["previous_record_digest"] = self.previous_record_digest
        if self.supersedes_record_id is not None:
            result["supersedes_record_id"] = self.supersedes_record_id
        return result

    @property
    def content_digest(self) -> str:
        return sha256_digest(self.as_dict())


@dataclass(frozen=True)
class SinkAck:
    sink: str
    project_id: str
    record_id: str
    content_digest: str
    location: str
    acknowledged_at: str
    operation: str = "CREATE_NEW_RECORD"
    append_only: bool = True

    def __post_init__(self) -> None:
        if self.sink not in SINKS:
            raise DualPersistenceError("unsupported persistence sink")
        object.__setattr__(self, "project_id", require_project_id(self.project_id))
        _require_nonempty(self.record_id, "record_id")
        _require_sha256(self.content_digest, "content_digest")
        _require_nonempty(self.location, "location")
        _parse_time(self.acknowledged_at, "acknowledged_at")
        if self.operation != "CREATE_NEW_RECORD":
            raise DualPersistenceError("persistence acknowledgement must be create-new-record")
        if self.append_only is not True:
            raise DualPersistenceError("persistence acknowledgement must be append-only")

    def as_dict(self) -> dict[str, object]:
        return {
            "sink": self.sink,
            "project_id": self.project_id,
            "record_id": self.record_id,
            "content_digest": self.content_digest,
            "location": self.location,
            "acknowledged_at": self.acknowledged_at,
            "operation": self.operation,
            "append_only": True,
        }


@dataclass(frozen=True)
class DualPersistenceReceipt:
    receipt_id: str
    project_id: str
    record_id: str
    content_digest: str
    prepared_at: str
    artifactory_ack: SinkAck | None = None
    github_ack: SinkAck | None = None
    previous_receipt_digest: str | None = None
    recovery_of_receipt_id: str | None = None
    authority_conveyed: bool = False

    def __post_init__(self) -> None:
        _require_nonempty(self.receipt_id, "receipt_id")
        object.__setattr__(self, "project_id", require_project_id(self.project_id))
        _require_nonempty(self.record_id, "record_id")
        _require_sha256(self.content_digest, "content_digest")
        _parse_time(self.prepared_at, "prepared_at")
        if self.previous_receipt_digest is not None:
            _require_sha256(self.previous_receipt_digest, "previous_receipt_digest")
        if self.recovery_of_receipt_id is not None:
            _require_nonempty(self.recovery_of_receipt_id, "recovery_of_receipt_id")
        if self.authority_conveyed is not False:
            raise DualPersistenceError("persistence receipts cannot convey authority")

    def _ack_valid(self, ack: SinkAck | None, expected_sink: str) -> bool:
        return bool(
            ack is not None
            and ack.sink == expected_sink
            and ack.project_id == self.project_id
            and ack.record_id == self.record_id
            and ack.content_digest == self.content_digest
            and ack.operation == "CREATE_NEW_RECORD"
            and ack.append_only is True
        )

    @property
    def state(self) -> str:
        a, g = self.artifactory_ack, self.github_ack
        if a is None and g is None:
            return PERSISTENCE_PREPARED
        if a is not None and g is None:
            return ARTIFACTORY_ONLY if self._ack_valid(a, SINK_ARTIFACTORY) else DIGEST_MISMATCH
        if a is None and g is not None:
            return GITHUB_ONLY if self._ack_valid(g, SINK_GITHUB) else DIGEST_MISMATCH
        if not self._ack_valid(a, SINK_ARTIFACTORY) or not self._ack_valid(g, SINK_GITHUB):
            return DIGEST_MISMATCH
        return DUAL_PERSISTENCE_CONFIRMED

    def require_confirmed(self) -> bool:
        if self.state != DUAL_PERSISTENCE_CONFIRMED:
            raise PersistenceBarrierError(f"DUAL_PERSISTENCE_REQUIRED:{self.state}")
        return True

    def require_confirmed_binding(self, *, project_id: str, record_id: str, content_digest: str) -> bool:
        if self.project_id != require_project_id(project_id):
            raise PersistenceBarrierError("PERSISTENCE_PROJECT_MISMATCH")
        if self.record_id != _require_nonempty(record_id, "record_id"):
            raise PersistenceBarrierError("PERSISTENCE_RECORD_ID_MISMATCH")
        if self.content_digest != _require_sha256(content_digest, "content_digest"):
            raise PersistenceBarrierError("PERSISTENCE_CONTENT_DIGEST_MISMATCH")
        return self.require_confirmed()

    def require_confirmed_for(self, record: MaterialWorkRecord) -> bool:
        return self.require_confirmed_binding(
            project_id=record.project_id,
            record_id=record.record_id,
            content_digest=record.content_digest,
        )

    def as_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "schema": PERSISTENCE_RECEIPT_SCHEMA,
            "receipt_id": self.receipt_id,
            "project_id": self.project_id,
            "record_id": self.record_id,
            "content_digest": self.content_digest,
            "prepared_at": self.prepared_at,
            "state": self.state,
            "authority_conveyed": False,
            "artifactory_ack": self.artifactory_ack.as_dict() if self.artifactory_ack else None,
            "github_ack": self.github_ack.as_dict() if self.github_ack else None,
        }
        if self.previous_receipt_digest is not None:
            result["previous_receipt_digest"] = self.previous_receipt_digest
        if self.recovery_of_receipt_id is not None:
            result["recovery_of_receipt_id"] = self.recovery_of_receipt_id
        return result

    @property
    def receipt_digest(self) -> str:
        return sha256_digest(self.as_dict())


class PersistenceIndex:
    """Project-scoped idempotency/conflict model. No external writes are performed here."""

    def __init__(self) -> None:
        self._digests: dict[tuple[str, str], str] = {}
        self._acks: dict[tuple[str, str, str], SinkAck] = {}
        self._quarantined: set[tuple[str, str]] = set()

    def observe(self, ack: SinkAck) -> str:
        record_key = (ack.project_id, ack.record_id)
        existing = self._digests.get(record_key)
        if existing is not None and existing != ack.content_digest:
            self._quarantined.add(record_key)
            raise PersistenceConflictError(f"{RECORD_CONFLICT}:{ack.project_id}:{ack.record_id}")
        self._digests.setdefault(record_key, ack.content_digest)
        ack_key = (ack.project_id, ack.record_id, ack.sink)
        previous = self._acks.get(ack_key)
        if previous is not None and previous.content_digest != ack.content_digest:
            self._quarantined.add(record_key)
            raise PersistenceConflictError(f"{RECORD_CONFLICT}:{ack.project_id}:{ack.record_id}")
        self._acks[ack_key] = ack
        if record_key in self._quarantined:
            return RECORD_CONFLICT
        has_a = (*record_key, SINK_ARTIFACTORY) in self._acks
        has_g = (*record_key, SINK_GITHUB) in self._acks
        if has_a and has_g:
            return DUAL_PERSISTENCE_CONFIRMED
        return ARTIFACTORY_ONLY if has_a else GITHUB_ONLY

    def receipt(self, *, receipt_id: str, record: MaterialWorkRecord, prepared_at: str) -> DualPersistenceReceipt:
        key = (record.project_id, record.record_id)
        return DualPersistenceReceipt(
            receipt_id=receipt_id,
            project_id=record.project_id,
            record_id=record.record_id,
            content_digest=record.content_digest,
            prepared_at=prepared_at,
            artifactory_ack=self._acks.get((*key, SINK_ARTIFACTORY)),
            github_ack=self._acks.get((*key, SINK_GITHUB)),
        )


def require_work_state_barrier(
    target_state: str,
    *,
    record: MaterialWorkRecord | None = None,
    receipt: DualPersistenceReceipt | None = None,
) -> bool:
    state = _require_nonempty(target_state, "target_state").upper()
    if state in TERMINAL_OR_HANDOFF_STATES:
        if record is None or receipt is None:
            raise PersistenceBarrierError(f"DUAL_PERSISTENCE_REQUIRED:{state}:MISSING_BINDING")
        receipt.require_confirmed_for(record)
    return True


@dataclass(frozen=True)
class ReconciliationFinding:
    project_id: str
    record_id: str
    state: str
    artifactory_digest: str | None
    github_digest: str | None


def reconcile_digest_views(
    *,
    project_id: str,
    artifactory_records: Mapping[str, str],
    github_records: Mapping[str, str],
) -> tuple[ReconciliationFinding, ...]:
    project = require_project_id(project_id)
    findings: list[ReconciliationFinding] = []
    for record_id in sorted(set(artifactory_records) | set(github_records)):
        _require_nonempty(record_id, "record_id")
        a, g = artifactory_records.get(record_id), github_records.get(record_id)
        if a is not None:
            _require_sha256(a, "artifactory_digest")
        if g is not None:
            _require_sha256(g, "github_digest")
        if a is None:
            state = GITHUB_ONLY
        elif g is None:
            state = ARTIFACTORY_ONLY
        elif a != g:
            state = DIGEST_MISMATCH
        else:
            state = DUAL_PERSISTENCE_CONFIRMED
        findings.append(ReconciliationFinding(project, record_id, state, a, g))
    return tuple(findings)


def build_persistence_health(
    *,
    project_id: str,
    reconciled_at_utc: str,
    artifactory_records: Mapping[str, str],
    github_records: Mapping[str, str],
    route_normalized: bool,
    forum_verified: bool,
    github_backup_verified: bool,
    conflict_record_ids: Iterable[str] = (),
) -> dict[str, object]:
    project = require_project_id(project_id)
    _parse_time(reconciled_at_utc, "reconciled_at_utc")
    findings = reconcile_digest_views(
        project_id=project,
        artifactory_records=artifactory_records,
        github_records=github_records,
    )
    confirmed = sum(item.state == DUAL_PERSISTENCE_CONFIRMED for item in findings)
    single_sink = sum(item.state in {ARTIFACTORY_ONLY, GITHUB_ONLY} for item in findings)
    mismatch = sum(item.state == DIGEST_MISMATCH for item in findings)
    conflict_ids = tuple(sorted(set(conflict_record_ids or ())))
    if any(not isinstance(item, str) or not item.strip() for item in conflict_ids):
        raise DualPersistenceError("conflict_record_ids must contain non-empty strings")
    conflict_count = len(conflict_ids)
    zero_loss = bool(
        route_normalized
        and forum_verified
        and github_backup_verified
        and single_sink == 0
        and mismatch == 0
        and conflict_count == 0
    )
    return {
        "schema": PERSISTENCE_HEALTH_SCHEMA,
        "project_id": project,
        "reconciled_at_utc": reconciled_at_utc,
        "route_normalized": bool(route_normalized),
        "forum_verified": bool(forum_verified),
        "github_backup_verified": bool(github_backup_verified),
        "record_count": len(findings),
        "confirmed_count": confirmed,
        "single_sink_count": single_sink,
        "digest_mismatch_count": mismatch,
        "conflict_count": conflict_count,
        "zero_loss": zero_loss,
        "authority_conveyed": False,
    }


def validate_hash_chain(records: Iterable[MaterialWorkRecord]) -> bool:
    previous: str | None = None
    stream_key: tuple[str, str, str, str] | None = None
    seen_ids: set[str] = set()
    for record in records:
        current_stream = (record.project_id, record.run_id, record.agent_id, record.work_id)
        if stream_key is None:
            stream_key = current_stream
        elif current_stream != stream_key:
            raise DualPersistenceError("HASH_CHAIN_CROSS_STREAM")
        if record.record_id in seen_ids:
            raise DualPersistenceError(f"HASH_CHAIN_DUPLICATE_RECORD:{record.record_id}")
        if record.previous_record_digest != previous:
            raise DualPersistenceError(f"HASH_CHAIN_BREAK:{record.record_id}")
        seen_ids.add(record.record_id)
        previous = record.content_digest
    return True
