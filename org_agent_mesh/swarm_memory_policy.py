from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Iterable

CANONICAL_AGENTBUS_BOARD = "/Intercommunication enhancements/AgentBus/messages"
CANONICAL_ARTIFACTORY_BOARD = CANONICAL_AGENTBUS_BOARD  # legacy compatibility alias
CANONICAL_GITHUB_REPOSITORY = "boberino93-bit/intercommunicationsenhancements"
GITHUB_COORDINATION_BACKUP_PREFIX = "agentbus-backup/coordination-messages/"


class MemoryPolicyViolation(RuntimeError):
    pass


class ExternalPersistenceUnavailable(MemoryPolicyViolation):
    pass


class ExternalPersistenceConflict(MemoryPolicyViolation):
    pass


def _normalize(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MemoryPolicyViolation("PERSISTENCE_SOURCE_REQUIRED")
    return value.strip().lower().replace(" ", "_")


_NATIVE = {"native_chatgpt_memory", "chatgpt_memory", "native_memory", "saved_memory", "saved_memories", "memory_recall", "chatgpt_memory_recall", "host_memory"}
_AGENTBUS = {"agentbus", "chatgpt_library_agentbus", "canonical_message_board", "artifactory", "internal_artifactory", _normalize(CANONICAL_AGENTBUS_BOARD)}
_GITHUB = {"github", "github_repository", "github_backup", _normalize(CANONICAL_GITHUB_REPOSITORY)}
_LOCAL = {"local", "local_file", "local_filesystem", "filesystem", "sqlite", "process_memory", "session_memory", "test_fixture"}


def classify_persistence_source(source: str) -> str:
    value = _normalize(source)
    if value in _NATIVE:
        return "NATIVE_CHATGPT_MEMORY_DENIED"
    if value in _AGENTBUS:
        return "AGENTBUS_CANONICAL"
    if value in _GITHUB:
        return "GITHUB_EXTERNAL_BACKUP"
    if value in _LOCAL:
        return "LOCAL_NONAUTHORITATIVE"
    return "UNKNOWN"


def assert_native_memory_not_used(source: str) -> None:
    if classify_persistence_source(source) == "NATIVE_CHATGPT_MEMORY_DENIED":
        raise MemoryPolicyViolation("NATIVE_CHATGPT_MEMORY_MUST_NOT_BE_USED_FOR_SWARM_STATE")


def assert_collective_persistence_source(source: str) -> str:
    classification = classify_persistence_source(source)
    if classification == "NATIVE_CHATGPT_MEMORY_DENIED":
        raise MemoryPolicyViolation("NATIVE_CHATGPT_MEMORY_MUST_NOT_BE_USED_FOR_SWARM_STATE")
    if classification == "LOCAL_NONAUTHORITATIVE":
        raise MemoryPolicyViolation("LOCAL_RUNTIME_STATE_CANNOT_BE_COLLECTIVE_AUTHORITY")
    if classification == "UNKNOWN":
        raise MemoryPolicyViolation("UNREGISTERED_COLLECTIVE_PERSISTENCE_SOURCE")
    return classification


def assert_local_state_non_authoritative(*, claimed_collective_authority: bool) -> None:
    if claimed_collective_authority:
        raise MemoryPolicyViolation("LOCAL_RUNTIME_STATE_CANNOT_BE_COLLECTIVE_AUTHORITY")


@dataclass(frozen=True)
class PersistenceReceipt:
    backend: str
    reference: str
    readback_verified: bool
    payload_sha256: str | None = None
    logical_record_id: str | None = None

    @classmethod
    def from_payload(cls, backend: str, reference: str, payload: bytes | str, *, readback_verified: bool, logical_record_id: str | None = None) -> "PersistenceReceipt":
        raw = payload.encode("utf-8") if isinstance(payload, str) else bytes(payload)
        return cls(backend, reference, bool(readback_verified), sha256(raw).hexdigest(), logical_record_id)


def validate_external_receipts(receipts: Iterable[PersistenceReceipt], *, require_artifactory: bool = True, require_github: bool = True, require_agentbus: bool | None = None) -> tuple[PersistenceReceipt, ...]:
    items = tuple(receipts)
    classes = set()
    for receipt in items:
        if not isinstance(receipt, PersistenceReceipt):
            raise TypeError("receipts must contain PersistenceReceipt values")
        classification = assert_collective_persistence_source(receipt.backend)
        if not receipt.reference.strip():
            raise MemoryPolicyViolation("PERSISTENCE_RECEIPT_REFERENCE_REQUIRED")
        if not receipt.readback_verified:
            raise MemoryPolicyViolation("EXTERNAL_PERSISTENCE_READBACK_REQUIRED")
        classes.add(classification)
    need_agentbus = require_artifactory if require_agentbus is None else require_agentbus
    if need_agentbus and "AGENTBUS_CANONICAL" not in classes:
        raise MemoryPolicyViolation("AGENTBUS_READBACK_RECEIPT_REQUIRED")
    if require_github and "GITHUB_EXTERNAL_BACKUP" not in classes:
        raise MemoryPolicyViolation("GITHUB_READBACK_RECEIPT_REQUIRED")
    return items


def _record_identity(state: Any) -> tuple[str, str] | None:
    if not isinstance(state, dict):
        return None
    record_id, digest = state.get("logical_record_id"), state.get("payload_sha256")
    if not isinstance(record_id, str) or not record_id.strip() or not isinstance(digest, str) or not digest.strip():
        return None
    return record_id.strip(), digest.strip().lower()


def records_equivalent(left: Any, right: Any) -> bool | None:
    left_id, right_id = _record_identity(left), _record_identity(right)
    if left_id is None or right_id is None or left_id[0] != right_id[0]:
        return None
    return left_id[1] == right_id[1]


def resolve_authoritative_collective_state(*, agentbus_state: Any = None, artifactory_state: Any = None, github_state: Any = None, agentbus_available: bool | None = None, artifactory_available: bool = True, github_available: bool = True, native_memory_state: Any = None, require_agentbus_for_this_branch: bool = True) -> Any:
    if native_memory_state is not None:
        raise MemoryPolicyViolation("NATIVE_CHATGPT_MEMORY_INGESTION_DENIED")
    available = artifactory_available if agentbus_available is None else agentbus_available
    board = agentbus_state if agentbus_state is not None else artifactory_state
    if not available or board is None:
        if require_agentbus_for_this_branch:
            raise ExternalPersistenceUnavailable("AGENTBUS_STATE_UNAVAILABLE")
        return github_state
    if github_available and github_state is not None and records_equivalent(board, github_state) is False:
        raise ExternalPersistenceConflict("AGENTBUS_GITHUB_RECORD_CONFLICT")
    return board
