from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Iterable


CANONICAL_ARTIFACTORY_BOARD = "/Intercommunication enhancements/AgentBus/messages"
CANONICAL_GITHUB_REPOSITORY = "boberino93-bit/intercommunicationsenhancements"
GITHUB_COORDINATION_BACKUP_PREFIX = "agentbus-backup/coordination-messages/"


class MemoryPolicyViolation(RuntimeError):
    """A persistence source or authority claim violates IEP-MEM-001."""


class ExternalPersistenceUnavailable(MemoryPolicyViolation):
    """Required external authoritative persistence cannot be read."""


class ExternalPersistenceConflict(MemoryPolicyViolation):
    """External authoritative records materially disagree."""


def _normalize(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MemoryPolicyViolation("PERSISTENCE_SOURCE_REQUIRED")
    return value.strip().lower().replace(" ", "_")


_NATIVE_ALIASES = {
    "native_chatgpt_memory",
    "chatgpt_memory",
    "native_memory",
    "saved_memory",
    "saved_memories",
    "memory_recall",
    "chatgpt_memory_recall",
    "host_memory",
}

_ARTIFACTORY_ALIASES = {
    "artifactory",
    "agentbus",
    "internal_artifactory",
    "canonical_message_board",
    _normalize(CANONICAL_ARTIFACTORY_BOARD),
}

_GITHUB_ALIASES = {
    "github",
    "github_repository",
    "github_backup",
    _normalize(CANONICAL_GITHUB_REPOSITORY),
}

_LOCAL_ALIASES = {
    "local",
    "local_file",
    "local_filesystem",
    "filesystem",
    "sqlite",
    "process_memory",
    "session_memory",
    "test_fixture",
}


def classify_persistence_source(source: str) -> str:
    normalized = _normalize(source)
    if normalized in _NATIVE_ALIASES:
        return "NATIVE_CHATGPT_MEMORY_DENIED"
    if normalized in _ARTIFACTORY_ALIASES:
        return "ARTIFACTORY_CANONICAL"
    if normalized in _GITHUB_ALIASES:
        return "GITHUB_EXTERNAL_BACKUP"
    if normalized in _LOCAL_ALIASES:
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

    @classmethod
    def from_payload(
        cls,
        backend: str,
        reference: str,
        payload: bytes | str,
        *,
        readback_verified: bool,
    ) -> "PersistenceReceipt":
        raw = payload.encode("utf-8") if isinstance(payload, str) else bytes(payload)
        return cls(
            backend=backend,
            reference=reference,
            readback_verified=bool(readback_verified),
            payload_sha256=sha256(raw).hexdigest(),
        )


def validate_external_receipts(
    receipts: Iterable[PersistenceReceipt],
    *,
    require_artifactory: bool = True,
    require_github: bool = True,
) -> tuple[PersistenceReceipt, ...]:
    items = tuple(receipts)
    classifications: set[str] = set()
    for receipt in items:
        if not isinstance(receipt, PersistenceReceipt):
            raise TypeError("receipts must contain PersistenceReceipt values")
        classification = assert_collective_persistence_source(receipt.backend)
        if not receipt.reference.strip():
            raise MemoryPolicyViolation("PERSISTENCE_RECEIPT_REFERENCE_REQUIRED")
        if not receipt.readback_verified:
            raise MemoryPolicyViolation("EXTERNAL_PERSISTENCE_READBACK_REQUIRED")
        classifications.add(classification)

    if require_artifactory and "ARTIFACTORY_CANONICAL" not in classifications:
        raise MemoryPolicyViolation("ARTIFACTORY_READBACK_RECEIPT_REQUIRED")
    if require_github and "GITHUB_EXTERNAL_BACKUP" not in classifications:
        raise MemoryPolicyViolation("GITHUB_READBACK_RECEIPT_REQUIRED")
    return items


def resolve_authoritative_collective_state(
    *,
    artifactory_state: Any = None,
    github_state: Any = None,
    artifactory_available: bool = True,
    github_available: bool = True,
    native_memory_state: Any = None,
) -> Any:
    """Resolve swarm state without ever ingesting native ChatGPT memory.

    Artifactory is the canonical live coordination authority. GitHub may corroborate
    or back up that state, but a material mismatch is a fail-closed conflict.
    """

    if native_memory_state is not None:
        raise MemoryPolicyViolation("NATIVE_CHATGPT_MEMORY_INGESTION_DENIED")
    if not artifactory_available:
        raise ExternalPersistenceUnavailable("CANONICAL_ARTIFACTORY_STATE_UNAVAILABLE")
    if artifactory_state is None:
        raise ExternalPersistenceUnavailable("CANONICAL_ARTIFACTORY_STATE_MISSING")

    if github_available and github_state is not None and github_state != artifactory_state:
        raise ExternalPersistenceConflict("ARTIFACTORY_GITHUB_STATE_CONFLICT")

    return artifactory_state
