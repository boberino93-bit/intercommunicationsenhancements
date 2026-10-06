from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Mapping

ACTIVE = "ACTIVE_ARTIFACTORY_HOT_PATH"
LOCAL_PERSISTENCE_CONFIRMED = "ARTIFACTORY_PERSISTENCE_CONFIRMED"
FINALIZATION_REQUESTED = "FINALIZATION_REQUESTED"
GITHUB_BACKUP_VERIFIED = "GITHUB_BACKUP_VERIFIED"
RUN_COMPLETE = "RUN_COMPLETE"
STALE_RECOVERY = "STALE_RECOVERY"
RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
RECORD_CONFLICT = "RECORD_ID_DIGEST_CONFLICT_QUARANTINED"

READY_STATES = frozenset({"READY", "HANDOFF_READY", "PROPOSAL_READY", "MANAGER_REVIEW_READY", "PRIMARY_REVIEW_READY"})
FINAL_STATES = frozenset({"COMPLETE", "RUN_COMPLETE", "CONVERSATION_COMPLETE"})

class SessionPersistenceError(ValueError):
    pass

class PersistenceConflictError(SessionPersistenceError):
    pass

class PersistenceBarrierError(SessionPersistenceError):
    pass


def _nonempty(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SessionPersistenceError(f"{name} is required")
    return value.strip()


def _sha256(value: str, name: str) -> str:
    text = _nonempty(value, name)
    if not text.startswith("sha256:") or len(text) != 71:
        raise SessionPersistenceError(f"{name} must be sha256:<64 hex>")
    try:
        int(text[7:], 16)
    except ValueError as exc:
        raise SessionPersistenceError(f"{name} must be sha256:<64 hex>") from exc
    return text


def _time(value: str, name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(_nonempty(value, name).replace("Z", "+00:00"))
    except ValueError as exc:
        raise SessionPersistenceError(f"{name} must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SessionPersistenceError(f"{name} must be offset-aware")
    return parsed.astimezone(timezone.utc)


def canonical_json(value: Mapping[str, object]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest_json(value: Mapping[str, object]) -> str:
    return "sha256:" + sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class LocalPersistenceAck:
    project_id: str
    record_id: str
    content_digest: str
    location: str
    acknowledged_at: str
    append_only: bool = True
    authority_conveyed: bool = False

    def __post_init__(self) -> None:
        _nonempty(self.project_id, "project_id")
        _nonempty(self.record_id, "record_id")
        _sha256(self.content_digest, "content_digest")
        _nonempty(self.location, "location")
        _time(self.acknowledged_at, "acknowledged_at")
        if not self.location.startswith("/"):
            raise SessionPersistenceError("location must be an absolute project-local board path")
        if self.append_only is not True:
            raise SessionPersistenceError("local persistence must be append-only")
        if self.authority_conveyed is not False:
            raise SessionPersistenceError("persistence acknowledgement cannot convey authority")


@dataclass(frozen=True)
class FinalizationManifest:
    project_id: str
    run_id: str
    sealed_at: str
    records: tuple[tuple[str, str], ...]
    previous_manifest_digest: str | None = None

    def __post_init__(self) -> None:
        _nonempty(self.project_id, "project_id")
        _nonempty(self.run_id, "run_id")
        _time(self.sealed_at, "sealed_at")
        ids = [rid for rid, _ in self.records]
        if ids != sorted(ids) or len(ids) != len(set(ids)):
            raise SessionPersistenceError("manifest records must be uniquely sorted by record_id")
        for rid, digest in self.records:
            _nonempty(rid, "record_id")
            _sha256(digest, "content_digest")
        if self.previous_manifest_digest is not None:
            _sha256(self.previous_manifest_digest, "previous_manifest_digest")

    def as_dict(self) -> dict[str, object]:
        body: dict[str, object] = {
            "schema": "org-agent-mesh/finalization-manifest/v1",
            "project_id": self.project_id,
            "run_id": self.run_id,
            "sealed_at": self.sealed_at,
            "records": [{"record_id": rid, "content_digest": dig} for rid, dig in self.records],
            "record_count": len(self.records),
            "authority_conveyed": False,
        }
        if self.previous_manifest_digest is not None:
            body["previous_manifest_digest"] = self.previous_manifest_digest
        return body

    @property
    def manifest_digest(self) -> str:
        return digest_json(self.as_dict())


@dataclass(frozen=True)
class GithubBackupReceipt:
    project_id: str
    run_id: str
    manifest_digest: str
    repository: str
    branch: str
    path: str
    commit_sha: str
    verified_at: str
    readback_manifest_digest: str
    record_count: int

    def __post_init__(self) -> None:
        for name in ("project_id", "run_id", "repository", "branch", "path", "commit_sha"):
            _nonempty(getattr(self, name), name)
        _sha256(self.manifest_digest, "manifest_digest")
        _sha256(self.readback_manifest_digest, "readback_manifest_digest")
        _time(self.verified_at, "verified_at")
        if self.record_count < 0:
            raise SessionPersistenceError("record_count must be non-negative")
        if self.manifest_digest != self.readback_manifest_digest:
            raise PersistenceBarrierError("GITHUB_VERIFICATION_FAILED:DIGEST_MISMATCH")


@dataclass
class ArtifactoryFirstSession:
    project_id: str
    run_id: str
    state: str = ACTIVE
    _records: dict[str, str] = field(default_factory=dict)
    _locations: dict[str, str] = field(default_factory=dict)
    _manifest: FinalizationManifest | None = None
    _github_receipt: GithubBackupReceipt | None = None

    def __post_init__(self) -> None:
        _nonempty(self.project_id, "project_id")
        _nonempty(self.run_id, "run_id")

    def observe_local_ack(self, ack: LocalPersistenceAck) -> str:
        if ack.project_id != self.project_id:
            raise PersistenceBarrierError("PERSISTENCE_PROJECT_MISMATCH")
        previous = self._records.get(ack.record_id)
        if previous is not None and previous != ack.content_digest:
            self.state = RECONCILIATION_REQUIRED
            raise PersistenceConflictError(f"{RECORD_CONFLICT}:{ack.record_id}")
        previous_location = self._locations.get(ack.record_id)
        if previous_location is not None and previous_location != ack.location:
            self.state = RECONCILIATION_REQUIRED
            raise PersistenceConflictError(f"RECORD_LOCATION_CONFLICT:{ack.record_id}")
        self._records.setdefault(ack.record_id, ack.content_digest)
        self._locations.setdefault(ack.record_id, ack.location)
        return LOCAL_PERSISTENCE_CONFIRMED

    def require_ready(self, *, target_state: str, record_id: str, content_digest: str) -> bool:
        state = _nonempty(target_state, "target_state").upper()
        if state in FINAL_STATES:
            return self.require_complete()
        if state not in READY_STATES:
            return True
        rid = _nonempty(record_id, "record_id")
        digest = _sha256(content_digest, "content_digest")
        if self._records.get(rid) != digest:
            raise PersistenceBarrierError(f"ARTIFACTORY_PERSISTENCE_REQUIRED:{state}:{rid}")
        return True

    def request_finalization(self, *, sealed_at: str, previous_manifest_digest: str | None = None) -> FinalizationManifest:
        if self.state == STALE_RECOVERY:
            raise PersistenceBarrierError("STALE_RECOVERY_CANNOT_FINALIZE")
        manifest = FinalizationManifest(self.project_id, self.run_id, sealed_at, tuple(sorted(self._records.items())), previous_manifest_digest)
        self._manifest = manifest
        self.state = FINALIZATION_REQUESTED
        return manifest

    def verify_github_backup(self, receipt: GithubBackupReceipt) -> bool:
        if self._manifest is None or self.state != FINALIZATION_REQUESTED:
            raise PersistenceBarrierError("FINALIZATION_NOT_REQUESTED")
        if receipt.project_id != self.project_id or receipt.run_id != self.run_id:
            raise PersistenceBarrierError("GITHUB_BACKUP_BINDING_MISMATCH")
        if receipt.manifest_digest != self._manifest.manifest_digest:
            raise PersistenceBarrierError("GITHUB_BACKUP_MANIFEST_MISMATCH")
        if receipt.record_count != len(self._manifest.records):
            raise PersistenceBarrierError("GITHUB_BACKUP_COUNT_MISMATCH")
        self._github_receipt = receipt
        self.state = GITHUB_BACKUP_VERIFIED
        return True

    def require_complete(self) -> bool:
        if self.state != GITHUB_BACKUP_VERIFIED or self._manifest is None or self._github_receipt is None:
            raise PersistenceBarrierError("VERIFIED_GITHUB_FINALIZATION_REQUIRED")
        self.state = RUN_COMPLETE
        return True

    def enter_stale_recovery(self) -> None:
        self.state = STALE_RECOVERY

    @property
    def record_count(self) -> int:
        return len(self._records)
