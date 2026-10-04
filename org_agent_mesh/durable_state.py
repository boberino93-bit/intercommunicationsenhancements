from datetime import datetime, timedelta, timezone
import uuid

from .control_plane import (
    LeaseConflict,
    LeaseRecord,
    StaleVersion,
    StateRecord,
    require_active_session,
)
from .durable_backend import (
    CorruptDurableRecord,
    DurableRecordBackend,
)
from .project_scope import ProjectScopeError, qualify, require_resource_id


def _utc_now(now=None):
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return value.astimezone(timezone.utc)


def _utc_iso(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_utc(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as exc:
        raise CorruptDurableRecord("persisted UTC timestamp is invalid") from exc
    if parsed.tzinfo is None:
        raise CorruptDurableRecord("persisted UTC timestamp is timezone-naive")
    return parsed.astimezone(timezone.utc)


class DurableVersionedStateStore:
    """Durable counterpart of VersionedStateStore with the same authorization model."""

    NAMESPACE = "accepted_state"

    def __init__(self, backend):
        if not isinstance(backend, DurableRecordBackend):
            raise TypeError("backend must implement DurableRecordBackend")
        self.backend = backend

    @staticmethod
    def _record(durable):
        if durable is None:
            return None
        payload = durable.payload
        if not isinstance(payload, dict):
            raise CorruptDurableRecord("accepted state payload must be an object")
        if "value" not in payload or "updated_by_agent_instance_id" not in payload:
            raise CorruptDurableRecord("accepted state payload is missing required fields")
        updater = payload["updated_by_agent_instance_id"]
        if not isinstance(updater, str) or not updater:
            raise CorruptDurableRecord("accepted state updater identity is invalid")
        return StateRecord(
            project_id=durable.project_id,
            resource_id=durable.resource_id,
            version=durable.version,
            value=payload["value"],
            updated_by_agent_instance_id=updater,
            updated_at_utc=durable.updated_at_utc,
        )

    def initialize(self, session, target_project_id, resource_id, value, *, now=None):
        binding = require_active_session(
            session,
            target_project_id,
            operation="durable state initialize",
            capability="WRITE_ACCEPTED_STATE",
        )
        durable = self.backend.create(
            self.NAMESPACE,
            target_project_id,
            require_resource_id(resource_id),
            {
                "value": value,
                "updated_by_agent_instance_id": binding.agent_instance_id,
            },
            now=now,
        )
        return self._record(durable)

    def read(self, project_id, resource_id):
        return self._record(
            self.backend.read(self.NAMESPACE, project_id, require_resource_id(resource_id))
        )

    def compare_and_set(
        self,
        session,
        target_project_id,
        resource_id,
        *,
        expected_version,
        value,
        now=None,
    ):
        binding = require_active_session(
            session,
            target_project_id,
            operation="durable state mutation",
            capability="WRITE_ACCEPTED_STATE",
        )
        durable = self.backend.compare_and_set(
            self.NAMESPACE,
            target_project_id,
            require_resource_id(resource_id),
            expected_version=expected_version,
            payload={
                "value": value,
                "updated_by_agent_instance_id": binding.agent_instance_id,
            },
            now=now,
        )
        return self._record(durable)


class DurableLeaseRegistry:
    """Crash-recoverable project-scoped leases with backend-enforced CAS."""

    NAMESPACE = "leases"

    def __init__(self, backend):
        if not isinstance(backend, DurableRecordBackend):
            raise TypeError("backend must implement DurableRecordBackend")
        self.backend = backend

    @staticmethod
    def _record(durable):
        if durable is None:
            return None
        payload = durable.payload
        if not isinstance(payload, dict):
            raise CorruptDurableRecord("lease payload must be an object")
        fields = (
            "holder_agent_instance_id",
            "lease_id",
            "acquired_at_utc",
            "expires_at_utc",
        )
        if not all(field in payload for field in fields):
            raise CorruptDurableRecord("lease payload is missing required fields")
        for field in fields:
            if not isinstance(payload[field], str) or not payload[field]:
                raise CorruptDurableRecord(f"lease field {field!r} is invalid")
        _parse_utc(payload["acquired_at_utc"])
        _parse_utc(payload["expires_at_utc"])
        return LeaseRecord(
            project_id=durable.project_id,
            resource_id=durable.resource_id,
            holder_agent_instance_id=payload["holder_agent_instance_id"],
            lease_id=payload["lease_id"],
            acquired_at_utc=payload["acquired_at_utc"],
            expires_at_utc=payload["expires_at_utc"],
            version=durable.version,
        )

    @staticmethod
    def _payload(
        binding,
        project_id,
        now,
        ttl_seconds,
        *,
        lease_id=None,
        acquired_at_utc=None,
    ):
        return {
            "holder_agent_instance_id": binding.agent_instance_id,
            "lease_id": lease_id or qualify(project_id, f"lease-{uuid.uuid4().hex}"),
            "acquired_at_utc": acquired_at_utc or _utc_iso(now),
            "expires_at_utc": _utc_iso(now + timedelta(seconds=ttl_seconds)),
        }

    def claim(self, session, target_project_id, resource_id, *, ttl_seconds=300, now=None):
        binding = require_active_session(
            session,
            target_project_id,
            operation="durable lease claim",
            capability="CLAIM_TASK",
        )
        resource_id = require_resource_id(resource_id)
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        now = _utc_now(now)

        for _ in range(3):
            current = self._record(
                self.backend.read(self.NAMESPACE, target_project_id, resource_id)
            )
            if current is None:
                try:
                    durable = self.backend.create(
                        self.NAMESPACE,
                        target_project_id,
                        resource_id,
                        self._payload(binding, target_project_id, now, ttl_seconds),
                        now=now,
                    )
                    return self._record(durable)
                except StaleVersion:
                    continue

            if not current.expired(now):
                if current.holder_agent_instance_id == binding.agent_instance_id:
                    return current
                raise LeaseConflict("resource already has an active durable lease")

            try:
                durable = self.backend.compare_and_set(
                    self.NAMESPACE,
                    target_project_id,
                    resource_id,
                    expected_version=current.version,
                    payload=self._payload(
                        binding, target_project_id, now, ttl_seconds
                    ),
                    now=now,
                )
                return self._record(durable)
            except StaleVersion:
                continue

        raise LeaseConflict("durable lease changed concurrently; retry claim")

    def renew(
        self,
        session,
        target_project_id,
        resource_id,
        lease_id,
        *,
        ttl_seconds=300,
        now=None,
    ):
        binding = require_active_session(
            session,
            target_project_id,
            operation="durable lease renewal",
            capability="CLAIM_TASK",
        )
        resource_id = require_resource_id(resource_id)
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        now = _utc_now(now)
        current = self._record(
            self.backend.read(self.NAMESPACE, target_project_id, resource_id)
        )
        if current is None or current.expired(now):
            raise LeaseConflict("durable lease is missing or expired")
        if (
            current.holder_agent_instance_id != binding.agent_instance_id
            or current.lease_id != lease_id
        ):
            raise ProjectScopeError(
                "durable lease renewal denied for non-holder execution instance"
            )
        durable = self.backend.compare_and_set(
            self.NAMESPACE,
            target_project_id,
            resource_id,
            expected_version=current.version,
            payload=self._payload(
                binding,
                target_project_id,
                now,
                ttl_seconds,
                lease_id=current.lease_id,
                acquired_at_utc=current.acquired_at_utc,
            ),
            now=now,
        )
        return self._record(durable)

    def release(self, session, target_project_id, resource_id, lease_id):
        binding = require_active_session(
            session,
            target_project_id,
            operation="durable lease release",
            capability="CLAIM_TASK",
        )
        resource_id = require_resource_id(resource_id)
        current = self._record(
            self.backend.read(self.NAMESPACE, target_project_id, resource_id)
        )
        if current is None:
            return False
        if (
            current.holder_agent_instance_id != binding.agent_instance_id
            or current.lease_id != lease_id
        ):
            raise ProjectScopeError(
                "durable lease release denied for non-holder execution instance"
            )
        return self.backend.delete_if_version(
            self.NAMESPACE,
            target_project_id,
            resource_id,
            expected_version=current.version,
        )

    def get(self, project_id, resource_id, *, now=None):
        now = _utc_now(now)
        resource_id = require_resource_id(resource_id)
        current = self._record(
            self.backend.read(self.NAMESPACE, project_id, resource_id)
        )
        if current is None:
            return None
        if current.expired(now):
            try:
                self.backend.delete_if_version(
                    self.NAMESPACE,
                    project_id,
                    resource_id,
                    expected_version=current.version,
                )
            except StaleVersion:
                pass
            return None
        return current

    def recover_expired(self, *, project_id=None, now=None):
        now = _utc_now(now)
        recovered = []
        for durable in self.backend.list_records(
            self.NAMESPACE, project_id=project_id
        ):
            current = self._record(durable)
            if not current.expired(now):
                continue
            try:
                deleted = self.backend.delete_if_version(
                    self.NAMESPACE,
                    current.project_id,
                    current.resource_id,
                    expected_version=current.version,
                )
            except StaleVersion:
                deleted = False
            if deleted:
                recovered.append(current)
        return recovered
