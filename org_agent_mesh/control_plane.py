from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import RLock
import uuid

from .project_scope import (
    ProjectBinding,
    ProjectScopeError,
    new_instance_id,
    qualify,
    require_project_id,
    require_repository_identity,
    require_resource_id,
)

PROJECT_STATES = ("ACTIVE", "DRAINING", "PAUSED")
AGENT_STATES = ("UNBOUND", "BOUND", "INITIALIZED", "ACTIVE", "DRAINING", "TERMINATED")


class LeaseConflict(RuntimeError):
    pass


class StaleVersion(RuntimeError):
    pass


class ProjectLifecycleError(RuntimeError):
    pass


class AgentLifecycleError(RuntimeError):
    pass


def _utc_now(now=None):
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return value.astimezone(timezone.utc)


def _utc_iso(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_utc(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


class AgentSession:
    """Fail-closed agent lifecycle. Only ACTIVE bound sessions may authorize mutation."""

    def __init__(self, agent_id):
        self.agent_id = require_resource_id(agent_id, field="agent_id")
        self.state = "UNBOUND"
        self.binding = None

    def bind(self, binding):
        if self.state != "UNBOUND":
            raise AgentLifecycleError("agent may bind only once")
        if not isinstance(binding, ProjectBinding):
            raise TypeError("binding must be a ProjectBinding")
        if binding.agent_id != self.agent_id:
            raise AgentLifecycleError("binding agent_id does not match session")
        self.binding = binding
        self.state = "BOUND"
        return self

    def initialize(self):
        if self.state != "BOUND":
            raise AgentLifecycleError("agent must be BOUND before initialization")
        self.state = "INITIALIZED"
        return self

    def activate(self):
        if self.state != "INITIALIZED":
            raise AgentLifecycleError("agent must be INITIALIZED before activation")
        self.state = "ACTIVE"
        return self

    def drain(self):
        if self.state not in {"ACTIVE", "INITIALIZED"}:
            raise AgentLifecycleError("agent cannot enter DRAINING from current state")
        self.state = "DRAINING"
        return self

    def terminate(self):
        self.state = "TERMINATED"
        return self

    def assert_mutation(self, target_project_id, operation="mutation", capability=None):
        if self.state != "ACTIVE" or self.binding is None:
            raise AgentLifecycleError("agent must be ACTIVE and project-bound before mutation")
        self.binding.assert_target(target_project_id, operation)
        if capability is not None:
            self.binding.assert_capability(capability)
        return True


def require_active_session(session, target_project_id, *, operation="mutation", capability=None):
    if not isinstance(session, AgentSession):
        raise AgentLifecycleError("mutation requires an AgentSession, not caller-supplied identity")
    session.assert_mutation(target_project_id, operation, capability)
    return session.binding


def inherit_child_binding(parent_binding, child_agent_id, *, capabilities=None):
    if not isinstance(parent_binding, ProjectBinding):
        raise TypeError("parent_binding must be a ProjectBinding")
    child_agent_id = require_resource_id(child_agent_id, field="child_agent_id")
    inherited = set(parent_binding.capabilities)
    requested = inherited if capabilities is None else set(capabilities)
    if not requested.issubset(inherited):
        raise ProjectScopeError("child capability escalation is denied")
    return ProjectBinding(
        project_id=parent_binding.project_id,
        repository_identity=parent_binding.repository_identity,
        project_root=parent_binding.project_root,
        agent_id=child_agent_id,
        agent_instance_id=new_instance_id(parent_binding.project_id, child_agent_id),
        protocol_version=parent_binding.protocol_version,
        capabilities=tuple(sorted(requested)),
    )


@dataclass(frozen=True)
class LeaseRecord:
    project_id: str
    resource_id: str
    holder_agent_instance_id: str
    lease_id: str
    acquired_at_utc: str
    expires_at_utc: str
    version: int

    def expired(self, now=None):
        return _parse_utc(self.expires_at_utc) <= _utc_now(now)


class LeaseRegistry:
    """Thread-safe project-scoped leases authorized by bound execution sessions."""

    def __init__(self):
        self._leases = {}
        self._lock = RLock()

    def claim(self, session, target_project_id, resource_id, *, ttl_seconds=300, now=None):
        binding = require_active_session(
            session, target_project_id, operation="lease claim", capability="CLAIM_TASK"
        )
        resource_id = require_resource_id(resource_id)
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        now = _utc_now(now)
        key = qualify(target_project_id, resource_id)
        with self._lock:
            existing = self._leases.get(key)
            if existing and not existing.expired(now):
                if existing.holder_agent_instance_id == binding.agent_instance_id:
                    return existing
                raise LeaseConflict("resource already has an active lease")
            version = 1 if existing is None else existing.version + 1
            record = LeaseRecord(
                project_id=target_project_id,
                resource_id=resource_id,
                holder_agent_instance_id=binding.agent_instance_id,
                lease_id=qualify(target_project_id, f"lease-{uuid.uuid4().hex}"),
                acquired_at_utc=_utc_iso(now),
                expires_at_utc=_utc_iso(now + timedelta(seconds=ttl_seconds)),
                version=version,
            )
            self._leases[key] = record
            return record

    def renew(self, session, target_project_id, resource_id, lease_id, *, ttl_seconds=300, now=None):
        binding = require_active_session(
            session, target_project_id, operation="lease renewal", capability="CLAIM_TASK"
        )
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        now = _utc_now(now)
        key = qualify(target_project_id, require_resource_id(resource_id))
        with self._lock:
            existing = self._leases.get(key)
            if existing is None or existing.expired(now):
                raise LeaseConflict("lease is missing or expired")
            if existing.holder_agent_instance_id != binding.agent_instance_id or existing.lease_id != lease_id:
                raise ProjectScopeError("lease renewal denied for non-holder execution instance")
            renewed = LeaseRecord(
                project_id=existing.project_id,
                resource_id=existing.resource_id,
                holder_agent_instance_id=existing.holder_agent_instance_id,
                lease_id=existing.lease_id,
                acquired_at_utc=existing.acquired_at_utc,
                expires_at_utc=_utc_iso(now + timedelta(seconds=ttl_seconds)),
                version=existing.version + 1,
            )
            self._leases[key] = renewed
            return renewed

    def release(self, session, target_project_id, resource_id, lease_id):
        binding = require_active_session(
            session, target_project_id, operation="lease release", capability="CLAIM_TASK"
        )
        key = qualify(target_project_id, require_resource_id(resource_id))
        with self._lock:
            existing = self._leases.get(key)
            if existing is None:
                return False
            if existing.holder_agent_instance_id != binding.agent_instance_id or existing.lease_id != lease_id:
                raise ProjectScopeError("lease release denied for non-holder execution instance")
            del self._leases[key]
            return True

    def get(self, project_id, resource_id, *, now=None):
        key = qualify(project_id, resource_id)
        with self._lock:
            existing = self._leases.get(key)
            if existing and existing.expired(now):
                del self._leases[key]
                return None
            return existing

    def recover_expired(self, *, now=None):
        now = _utc_now(now)
        with self._lock:
            recovered = []
            for key, record in list(self._leases.items()):
                if record.expired(now):
                    recovered.append(record)
                    del self._leases[key]
            return recovered


@dataclass(frozen=True)
class StateRecord:
    project_id: str
    resource_id: str
    version: int
    value: object
    updated_by_agent_instance_id: str
    updated_at_utc: str


class VersionedStateStore:
    def __init__(self):
        self._records = {}
        self._lock = RLock()

    def initialize(self, session, target_project_id, resource_id, value, *, now=None):
        binding = require_active_session(
            session, target_project_id, operation="state initialize", capability="WRITE_ACCEPTED_STATE"
        )
        resource_id = require_resource_id(resource_id)
        key = qualify(target_project_id, resource_id)
        with self._lock:
            if key in self._records:
                raise StaleVersion("state already exists")
            record = StateRecord(target_project_id, resource_id, 1, value, binding.agent_instance_id, _utc_iso(_utc_now(now)))
            self._records[key] = record
            return record

    def read(self, project_id, resource_id):
        with self._lock:
            return self._records.get(qualify(project_id, resource_id))

    def compare_and_set(self, session, target_project_id, resource_id, *, expected_version, value, now=None):
        binding = require_active_session(
            session, target_project_id, operation="state mutation", capability="WRITE_ACCEPTED_STATE"
        )
        key = qualify(target_project_id, require_resource_id(resource_id))
        with self._lock:
            current = self._records.get(key)
            if current is None:
                raise StaleVersion("state does not exist")
            if current.version != expected_version:
                raise StaleVersion(f"stale state version: expected {expected_version}, current {current.version}")
            updated = StateRecord(target_project_id, current.resource_id, current.version + 1, value, binding.agent_instance_id, _utc_iso(_utc_now(now)))
            self._records[key] = updated
            return updated


@dataclass(frozen=True)
class ProjectRecord:
    project_id: str
    repository_identity: str
    status: str
    version: int
    updated_at_utc: str


class ProjectRegistry:
    """Global-readable registry; project lifecycle mutation requires bound lifecycle authority."""

    def __init__(self):
        self._records = {}
        self._lock = RLock()

    def register(self, session, repository_identity=None, *, now=None):
        if not isinstance(session, AgentSession) or session.binding is None:
            raise AgentLifecycleError("project registration requires bound session")
        project_id = session.binding.project_id
        binding = require_active_session(
            session, project_id, operation="project registration", capability="CONTROL_PROJECT_LIFECYCLE"
        )
        repository_identity = repository_identity or binding.repository_identity
        repository_identity = require_repository_identity(repository_identity)
        if repository_identity != binding.repository_identity:
            raise ProjectScopeError("project registration repository does not match bound session")
        with self._lock:
            if project_id in self._records:
                raise StaleVersion("project already registered")
            record = ProjectRecord(project_id, repository_identity, "ACTIVE", 1, _utc_iso(_utc_now(now)))
            self._records[project_id] = record
            return record

    def read(self, project_id):
        with self._lock:
            return self._records.get(require_project_id(project_id))

    def transition(self, session, target_project_id, *, expected_version, status, now=None):
        require_active_session(
            session, target_project_id, operation="project lifecycle transition", capability="CONTROL_PROJECT_LIFECYCLE"
        )
        if status not in PROJECT_STATES:
            raise ValueError("unsupported project lifecycle state")
        with self._lock:
            current = self._records.get(target_project_id)
            if current is None:
                raise ProjectLifecycleError("project is not registered")
            if current.version != expected_version:
                raise StaleVersion(f"stale project lifecycle version: expected {expected_version}, current {current.version}")
            updated = ProjectRecord(current.project_id, current.repository_identity, status, current.version + 1, _utc_iso(_utc_now(now)))
            self._records[target_project_id] = updated
            return updated

    def assert_operation(self, session, target_project_id, *, mutation, drain_completion=False, required_capability=None):
        require_active_session(
            session,
            target_project_id,
            operation="project operation",
            capability=required_capability if mutation else None,
        )
        with self._lock:
            record = self._records.get(target_project_id)
            if record is None:
                raise ProjectLifecycleError("project is not registered")
            if not mutation:
                return True
            if record.status == "PAUSED":
                raise ProjectLifecycleError("project mutations are paused")
            if record.status == "DRAINING" and not drain_completion:
                raise ProjectLifecycleError("project is draining; new mutations are denied")
            return True
