"""IPG3 design-only durable adapter contract API.

The API intentionally exposes only the atomic primitives needed by protocol invariants.
Adapters are candidates until they pass the black-box conformance suite; none of these
classes participate in the current G2 runtime.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


class AdapterConflict(RuntimeError):
    pass


class AdapterNotFound(KeyError):
    pass


class LeaseConflict(RuntimeError):
    pass


class LeaseOwnershipError(RuntimeError):
    pass


@dataclass(frozen=True)
class StoredValue:
    value: Any
    version: int


@dataclass(frozen=True)
class LeaseValue:
    project_id: str
    resource_id: str
    holder_instance_id: str
    expires_at_utc: str
    version: int


class DurableAdapter(ABC):
    """Minimum primitive contract used by the IPG3 conformance suite."""

    capabilities: frozenset[str] = frozenset()

    @abstractmethod
    def exclusive_create(self, namespace: str, project_id: str, key: str, value: Any) -> StoredValue:
        """Create once. Concurrent duplicate creates must produce one winner."""

    @abstractmethod
    def get(self, namespace: str, project_id: str, key: str) -> StoredValue | None:
        """Read current durable value/version."""

    @abstractmethod
    def compare_and_set(
        self,
        namespace: str,
        project_id: str,
        key: str,
        *,
        expected_version: int,
        value: Any,
    ) -> StoredValue:
        """Atomically replace only if expected_version matches."""

    @abstractmethod
    def atomic_consume(
        self,
        namespace: str,
        project_id: str,
        key: str,
        *,
        expected_version: int,
        counter_field: str,
        limit_field: str,
        terminal_field: str,
        terminal_value: Any,
    ) -> StoredValue:
        """Atomically consume one remaining unit and mark terminal at the limit."""

    @abstractmethod
    def claim_lease(
        self,
        project_id: str,
        resource_id: str,
        holder_instance_id: str,
        *,
        expires_at: datetime,
        now: datetime,
    ) -> LeaseValue:
        """Atomically acquire an absent/expired lease or idempotently return own lease."""

    @abstractmethod
    def renew_lease(
        self,
        project_id: str,
        resource_id: str,
        holder_instance_id: str,
        *,
        expires_at: datetime,
        now: datetime,
        expected_version: int,
    ) -> LeaseValue:
        """Renew only the current unexpired lease held by this execution instance."""

    @abstractmethod
    def release_lease(
        self,
        project_id: str,
        resource_id: str,
        holder_instance_id: str,
        *,
        expected_version: int,
    ) -> None:
        """Release only current holder/version."""

    @abstractmethod
    def append_event(self, project_id: str, sequence: int, event_id: str, event: Any) -> None:
        """Append exactly one event at project-local sequence; no overwrite."""

    @abstractmethod
    def read_events(self, project_id: str) -> list[Any]:
        """Read project-local events ordered by sequence."""

    @abstractmethod
    def close(self) -> None:
        """Release local resources without deleting durable state."""
