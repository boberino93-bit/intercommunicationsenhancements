"""v1.8 Reliability Kernel reference implementation.

This module is intentionally narrow: it projects existing authority into a
verifiable execution certificate, enforces selected machine invariants, bounds
aggregate admission, supports safe-minimal fail-closed behavior, and produces
proof-carrying handoffs. It never creates project authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import hmac
import json
import re
from threading import RLock
from typing import Iterable, Mapping

from .project_scope import (
    ProjectBinding,
    ProjectScopeError,
    require_project_id,
    require_repository_identity,
    require_resource_id,
)


class ReliabilityKernelError(RuntimeError):
    pass


class PolicyCompilationError(ReliabilityKernelError):
    pass


class CertificateVerificationError(ReliabilityKernelError):
    pass


class InvariantViolation(ReliabilityKernelError):
    pass


class AdmissionDenied(ReliabilityKernelError):
    pass


class AuthorizationError(ReliabilityKernelError):
    pass


class HandoffVerificationError(ReliabilityKernelError):
    pass


class CompatibilityError(ReliabilityKernelError):
    pass


class ReasonCode(str, Enum):
    AUTHORITY_ESCALATION = "RK_AUTHORITY_ESCALATION"
    PROJECT_MISMATCH = "RK_PROJECT_MISMATCH"
    REPOSITORY_MISMATCH = "RK_REPOSITORY_MISMATCH"
    CERTIFICATE_INVALID = "RK_CERTIFICATE_INVALID"
    CERTIFICATE_EXPIRED = "RK_CERTIFICATE_EXPIRED"
    CERTIFICATE_REPLAY = "RK_CERTIFICATE_REPLAY"
    OWNERSHIP_STALE = "RK_OWNERSHIP_STALE"
    PROTECTED_AUTH_REQUIRED = "RK_PROTECTED_AUTH_REQUIRED"
    AUTHORIZATION_REPLAY = "RK_AUTHORIZATION_REPLAY"
    ADMISSION_CAPACITY = "RK_ADMISSION_CAPACITY"
    RESOURCE_BUDGET_EXHAUSTED = "RK_RESOURCE_BUDGET_EXHAUSTED"
    SAFE_MINIMAL_DENY = "RK_SAFE_MINIMAL_DENY"
    SCHEMA_INCOMPATIBLE = "RK_SCHEMA_INCOMPATIBLE"
    HANDOFF_INVALID = "RK_HANDOFF_INVALID"
    HANDOFF_STALE = "RK_HANDOFF_STALE"
    CONTROL_LOOP_COOLDOWN = "RK_CONTROL_LOOP_COOLDOWN"


class KernelMode(str, Enum):
    NORMAL = "NORMAL"
    DEGRADED = "DEGRADED"
    SAFE_MINIMAL = "SAFE_MINIMAL"


SAFE_MINIMAL_EFFECTS = frozenset({
    "READ_ONLY",
    "DIAGNOSTIC",
    "EVIDENCE_PERSIST",
    "CHECKPOINT_PERSIST",
    "RECOVERY",
})

# Existing capabilities remain authoritative. This table only maps an effect to
# the capability that must already be present before that effect can be projected.
EFFECT_CAPABILITY = {
    "READ_SOURCE": "READ_SOURCE",
    "READ_ARTIFACTS": "READ_ARTIFACTS",
    "WRITE_SOURCE": "WRITE_SOURCE",
    "WRITE_ARTIFACTS": "WRITE_ARTIFACTS",
    "WRITE_ACCEPTED_STATE": "WRITE_ACCEPTED_STATE",
    "PUBLISH_MESSAGE": "PUBLISH_MESSAGE",
    "MODIFY_EXTERNAL_SYSTEM": "MODIFY_EXTERNAL_SYSTEM",
    "DELETE_DATA": "DELETE_DATA",
    "APPROVE_RELEASE": "APPROVE_RELEASE",
    "PUBLISH_DEPLOYMENT_PACKAGE": "PUBLISH_DEPLOYMENT_PACKAGE",
    "POLICY_CHANGE": "AUTHORIZE_POLICY_CHANGE",
    "FINANCIAL_ACTION": "AUTHORIZE_FINANCIAL_ACTION",
}

PROTECTED_EFFECTS = frozenset({
    "PRODUCTION_DEPLOYMENT",
    "POLICY_CHANGE",
    "FINANCIAL_ACTION",
    "BREAK_GLASS",
})

_RESOURCE_ID_SAFE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._:-]{0,254}[A-Za-z0-9])?$")


def _aware_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timezone-aware datetime required")
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return _aware_utc(value).isoformat().replace("+00:00", "Z")


def _parse_iso(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("UTC timestamp string required")
    return _aware_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))


def _rid(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not _RESOURCE_ID_SAFE.fullmatch(value):
        raise ValueError(f"{field_name} must be a canonical identifier")
    return value


def _canonical(value) -> bytes:
    def normalize(v):
        if isinstance(v, Enum):
            return v.value
        if hasattr(v, "__dataclass_fields__"):
            return {k: normalize(x) for k, x in asdict(v).items()}
        if isinstance(v, Mapping):
            return {str(k): normalize(v[k]) for k in sorted(v)}
        if isinstance(v, (tuple, list, set, frozenset)):
            return [normalize(x) for x in v]
        return v

    return json.dumps(normalize(value), sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_digest(value) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _sign(payload, key: bytes) -> str:
    if not isinstance(key, (bytes, bytearray)) or len(key) < 16:
        raise ValueError("signing key must be at least 16 bytes")
    return hmac.new(bytes(key), _canonical(payload), hashlib.sha256).hexdigest()


def _verify_signature(payload, signature: str, key: bytes) -> bool:
    return hmac.compare_digest(_sign(payload, key), signature)


@dataclass(frozen=True)
class EffectivePolicySlice:
    policy_version: str
    project_id: str
    repository_identity: str
    work_instance_id: str
    agent_instance_id: str
    authority_capabilities: tuple[str, ...]
    allowed_effect_classes: tuple[str, ...]
    execution_profile: str
    ownership_epoch: int
    schema_versions: tuple[tuple[str, str], ...] = ()
    protected_authorization_ids: tuple[str, ...] = ()

    def __post_init__(self):
        require_project_id(self.project_id)
        require_repository_identity(self.repository_identity)
        _rid(self.work_instance_id, "work_instance_id")
        if not isinstance(self.agent_instance_id, str) or not self.agent_instance_id.strip():
            raise ValueError("agent_instance_id is required")
        if not isinstance(self.policy_version, str) or not self.policy_version.strip():
            raise ValueError("policy_version is required")
        if not isinstance(self.execution_profile, str) or not self.execution_profile.strip():
            raise ValueError("execution_profile is required")
        if not isinstance(self.ownership_epoch, int) or self.ownership_epoch < 0:
            raise ValueError("ownership_epoch must be a non-negative integer")
        object.__setattr__(self, "authority_capabilities", tuple(sorted(set(self.authority_capabilities))))
        object.__setattr__(self, "allowed_effect_classes", tuple(sorted(set(self.allowed_effect_classes))))
        object.__setattr__(self, "schema_versions", tuple(sorted((str(k), str(v)) for k, v in self.schema_versions)))
        object.__setattr__(self, "protected_authorization_ids", tuple(sorted(set(self.protected_authorization_ids))))


@dataclass(frozen=True)
class PolicyCertificate:
    certificate_id: str
    policy_slice: EffectivePolicySlice
    issued_at_utc: str
    expires_at_utc: str
    nonce: str
    issuer: str
    payload_digest: str
    signature: str

    def unsigned_payload(self):
        return {
            "certificate_id": self.certificate_id,
            "policy_slice": asdict(self.policy_slice),
            "issued_at_utc": self.issued_at_utc,
            "expires_at_utc": self.expires_at_utc,
            "nonce": self.nonce,
            "issuer": self.issuer,
            "payload_digest": self.payload_digest,
        }


@dataclass(frozen=True)
class HumanAuthorization:
    authorization_id: str
    project_id: str
    artifact_hash: str
    requested_action: str
    environment: str
    issued_at_utc: str
    expires_at_utc: str
    nonce: str
    issuer: str
    signature: str

    def unsigned_payload(self):
        return {
            "authorization_id": self.authorization_id,
            "project_id": self.project_id,
            "artifact_hash": self.artifact_hash,
            "requested_action": self.requested_action,
            "environment": self.environment,
            "issued_at_utc": self.issued_at_utc,
            "expires_at_utc": self.expires_at_utc,
            "nonce": self.nonce,
            "issuer": self.issuer,
        }


class AuthorizationLedger:
    """Reference anti-replay ledger for externally issued human authorizations."""

    def __init__(self):
        self._consumed: set[str] = set()
        self._lock = RLock()

    def verify(
        self,
        authorization: HumanAuthorization,
        *,
        verification_key: bytes,
        now: datetime,
        project_id: str,
        requested_action: str,
        artifact_hash: str,
        consume: bool = False,
    ) -> bool:
        now = _aware_utc(now)
        require_project_id(project_id)
        if authorization.project_id != project_id:
            raise AuthorizationError(ReasonCode.PROJECT_MISMATCH.value)
        if authorization.requested_action != requested_action:
            raise AuthorizationError(ReasonCode.PROTECTED_AUTH_REQUIRED.value)
        if authorization.artifact_hash != artifact_hash:
            raise AuthorizationError(ReasonCode.PROTECTED_AUTH_REQUIRED.value)
        if authorization.issuer != "HUMAN_ROOT_AUTHORITY_VERIFIER":
            raise AuthorizationError(ReasonCode.PROTECTED_AUTH_REQUIRED.value)
        if not _verify_signature(authorization.unsigned_payload(), authorization.signature, verification_key):
            raise AuthorizationError(ReasonCode.CERTIFICATE_INVALID.value)
        if now < _parse_iso(authorization.issued_at_utc) or now >= _parse_iso(authorization.expires_at_utc):
            raise AuthorizationError(ReasonCode.CERTIFICATE_EXPIRED.value)
        with self._lock:
            if authorization.authorization_id in self._consumed:
                raise AuthorizationError(ReasonCode.AUTHORIZATION_REPLAY.value)
            if consume:
                self._consumed.add(authorization.authorization_id)
        return True


class PolicyCompiler:
    """Projects existing binding authority into a narrower effective policy slice."""

    def __init__(self, *, policy_version: str = "v1.8-reference"):
        self.policy_version = policy_version

    def compile_slice(
        self,
        binding: ProjectBinding,
        *,
        work_instance_id: str,
        requested_capabilities: Iterable[str],
        requested_effect_classes: Iterable[str],
        execution_profile: str,
        ownership_epoch: int,
        schema_versions: Mapping[str, str] | None = None,
        protected_authorization_ids: Iterable[str] = (),
    ) -> EffectivePolicySlice:
        if not isinstance(binding, ProjectBinding):
            raise TypeError("binding must be ProjectBinding")
        requested_caps = set(requested_capabilities)
        granted_caps = set(binding.capabilities)
        if not requested_caps.issubset(granted_caps):
            raise PolicyCompilationError(ReasonCode.AUTHORITY_ESCALATION.value)

        effects = set(requested_effect_classes)
        for effect in effects:
            capability = EFFECT_CAPABILITY.get(effect)
            if capability is not None and capability not in requested_caps:
                raise PolicyCompilationError(
                    f"effect {effect} requires pre-existing capability {capability}"
                )
            if effect == "PRODUCTION_DEPLOYMENT":
                # No current baseline capability grants deployment itself. A later
                # deployment mechanism must explicitly add and verify such authority.
                raise PolicyCompilationError(ReasonCode.PROTECTED_AUTH_REQUIRED.value)
            if effect == "BREAK_GLASS":
                raise PolicyCompilationError(ReasonCode.PROTECTED_AUTH_REQUIRED.value)

        return EffectivePolicySlice(
            policy_version=self.policy_version,
            project_id=binding.project_id,
            repository_identity=binding.repository_identity,
            work_instance_id=_rid(work_instance_id, "work_instance_id"),
            agent_instance_id=binding.agent_instance_id,
            authority_capabilities=tuple(requested_caps),
            allowed_effect_classes=tuple(effects),
            execution_profile=execution_profile,
            ownership_epoch=ownership_epoch,
            schema_versions=tuple((schema_versions or {}).items()),
            protected_authorization_ids=tuple(protected_authorization_ids),
        )

    def issue_certificate(
        self,
        policy_slice: EffectivePolicySlice,
        *,
        issued_at: datetime,
        expires_at: datetime,
        nonce: str,
        signing_key: bytes,
        issuer: str = "RELIABILITY_KERNEL_POLICY_COMPILER",
    ) -> PolicyCertificate:
        issued = _aware_utc(issued_at)
        expires = _aware_utc(expires_at)
        if expires <= issued:
            raise ValueError("certificate expiry must be after issue time")
        nonce = _rid(nonce, "nonce")
        payload_digest = canonical_digest(policy_slice)
        certificate_id = f"pc-{payload_digest[:16]}-{nonce}"
        unsigned = {
            "certificate_id": certificate_id,
            "policy_slice": asdict(policy_slice),
            "issued_at_utc": _iso(issued),
            "expires_at_utc": _iso(expires),
            "nonce": nonce,
            "issuer": issuer,
            "payload_digest": payload_digest,
        }
        return PolicyCertificate(
            certificate_id=certificate_id,
            policy_slice=policy_slice,
            issued_at_utc=unsigned["issued_at_utc"],
            expires_at_utc=unsigned["expires_at_utc"],
            nonce=nonce,
            issuer=issuer,
            payload_digest=payload_digest,
            signature=_sign(unsigned, signing_key),
        )


class CertificateVerifier:
    def __init__(self):
        self._consumed: set[str] = set()
        self._lock = RLock()

    def verify(
        self,
        certificate: PolicyCertificate,
        *,
        verification_key: bytes,
        now: datetime,
        binding: ProjectBinding,
        work_instance_id: str,
        ownership_epoch: int,
        required_effect: str | None = None,
        consume: bool = False,
    ) -> bool:
        now = _aware_utc(now)
        if not _verify_signature(certificate.unsigned_payload(), certificate.signature, verification_key):
            raise CertificateVerificationError(ReasonCode.CERTIFICATE_INVALID.value)
        if certificate.payload_digest != canonical_digest(certificate.policy_slice):
            raise CertificateVerificationError(ReasonCode.CERTIFICATE_INVALID.value)
        if now < _parse_iso(certificate.issued_at_utc) or now >= _parse_iso(certificate.expires_at_utc):
            raise CertificateVerificationError(ReasonCode.CERTIFICATE_EXPIRED.value)
        ps = certificate.policy_slice
        if ps.project_id != binding.project_id:
            raise CertificateVerificationError(ReasonCode.PROJECT_MISMATCH.value)
        if ps.repository_identity != binding.repository_identity:
            raise CertificateVerificationError(ReasonCode.REPOSITORY_MISMATCH.value)
        if ps.agent_instance_id != binding.agent_instance_id:
            raise CertificateVerificationError(ReasonCode.CERTIFICATE_INVALID.value)
        if ps.work_instance_id != _rid(work_instance_id, "work_instance_id"):
            raise CertificateVerificationError(ReasonCode.CERTIFICATE_INVALID.value)
        if ps.ownership_epoch != ownership_epoch:
            raise CertificateVerificationError(ReasonCode.OWNERSHIP_STALE.value)
        if not set(ps.authority_capabilities).issubset(set(binding.capabilities)):
            raise CertificateVerificationError(ReasonCode.AUTHORITY_ESCALATION.value)
        if required_effect is not None and required_effect not in ps.allowed_effect_classes:
            raise CertificateVerificationError(ReasonCode.CERTIFICATE_INVALID.value)
        with self._lock:
            if certificate.certificate_id in self._consumed:
                raise CertificateVerificationError(ReasonCode.CERTIFICATE_REPLAY.value)
            if consume:
                self._consumed.add(certificate.certificate_id)
        return True


@dataclass(frozen=True)
class InvariantCheckResult:
    invariant_id: str
    passed: bool
    reason_code: str | None = None
    detail: str | None = None


class InvariantRegistry:
    """Small machine-enforceable invariant registry; callers may extend it."""

    def __init__(self):
        self._checks = {}
        self.register("authority_subset", self._authority_subset)
        self.register("repository_matches_binding", self._repository_matches)
        self.register("project_matches_binding", self._project_matches)

    def register(self, invariant_id: str, fn):
        invariant_id = require_resource_id(invariant_id, field="invariant_id")
        if invariant_id in self._checks:
            raise ValueError("invariant already registered")
        self._checks[invariant_id] = fn

    def evaluate(self, invariant_id: str, **context) -> InvariantCheckResult:
        if invariant_id not in self._checks:
            raise KeyError(invariant_id)
        return self._checks[invariant_id](**context)

    @staticmethod
    def _authority_subset(*, policy_slice: EffectivePolicySlice, binding: ProjectBinding):
        passed = set(policy_slice.authority_capabilities).issubset(set(binding.capabilities))
        return InvariantCheckResult(
            "authority_subset",
            passed,
            None if passed else ReasonCode.AUTHORITY_ESCALATION.value,
        )

    @staticmethod
    def _repository_matches(*, policy_slice: EffectivePolicySlice, binding: ProjectBinding):
        passed = policy_slice.repository_identity == binding.repository_identity
        return InvariantCheckResult(
            "repository_matches_binding",
            passed,
            None if passed else ReasonCode.REPOSITORY_MISMATCH.value,
        )

    @staticmethod
    def _project_matches(*, policy_slice: EffectivePolicySlice, binding: ProjectBinding):
        passed = policy_slice.project_id == binding.project_id
        return InvariantCheckResult(
            "project_matches_binding",
            passed,
            None if passed else ReasonCode.PROJECT_MISMATCH.value,
        )

    def require(self, invariant_id: str, **context) -> bool:
        result = self.evaluate(invariant_id, **context)
        if not result.passed:
            raise InvariantViolation(result.reason_code or invariant_id)
        return True


@dataclass(frozen=True)
class ResourcePolicy:
    max_concurrent: int = 4
    max_weight: int = 8

    def __post_init__(self):
        if self.max_concurrent <= 0 or self.max_weight <= 0:
            raise ValueError("resource limits must be positive")


@dataclass(frozen=True)
class ResourceReservation:
    reservation_id: str
    work_instance_id: str
    weight: int
    priority: int


class ResourceGovernor:
    """Bounded admission with priority-aware queued work and deterministic release."""

    def __init__(self, policy: ResourcePolicy | None = None):
        self.policy = policy or ResourcePolicy()
        self._active: dict[str, ResourceReservation] = {}
        self._lock = RLock()

    @property
    def active_count(self):
        return len(self._active)

    @property
    def active_weight(self):
        return sum(x.weight for x in self._active.values())

    def reserve(self, *, reservation_id: str, work_instance_id: str, weight: int = 1, priority: int = 100):
        reservation_id = _rid(reservation_id, "reservation_id")
        work_instance_id = _rid(work_instance_id, "work_instance_id")
        if weight <= 0 or priority < 0:
            raise ValueError("weight must be positive and priority non-negative")
        with self._lock:
            if reservation_id in self._active:
                return self._active[reservation_id]
            if self.active_count >= self.policy.max_concurrent:
                raise AdmissionDenied(ReasonCode.ADMISSION_CAPACITY.value)
            if self.active_weight + weight > self.policy.max_weight:
                raise AdmissionDenied(ReasonCode.RESOURCE_BUDGET_EXHAUSTED.value)
            record = ResourceReservation(reservation_id, work_instance_id, weight, priority)
            self._active[reservation_id] = record
            return record

    def release(self, reservation_id: str) -> bool:
        with self._lock:
            return self._active.pop(reservation_id, None) is not None


@dataclass
class KernelState:
    mode: KernelMode = KernelMode.NORMAL
    reason_code: str | None = None

    def enter_degraded(self, reason_code: str):
        self.mode = KernelMode.DEGRADED
        self.reason_code = reason_code

    def enter_safe_minimal(self, reason_code: str):
        self.mode = KernelMode.SAFE_MINIMAL
        self.reason_code = reason_code

    def recover_normal(self):
        self.mode = KernelMode.NORMAL
        self.reason_code = None

    def assert_effect_allowed(self, effect_class: str) -> bool:
        if self.mode == KernelMode.SAFE_MINIMAL and effect_class not in SAFE_MINIMAL_EFFECTS:
            raise InvariantViolation(ReasonCode.SAFE_MINIMAL_DENY.value)
        return True


@dataclass(frozen=True)
class ProofCarryingHandoff:
    handoff_id: str
    project_id: str
    repository_identity: str
    work_instance_id: str
    sender_agent_instance_id: str
    receiver_agent_instance_id: str
    sender_capabilities: tuple[str, ...]
    receiver_capabilities: tuple[str, ...]
    ownership_epoch: int
    checkpoint_digest: str
    policy_certificate_id: str
    issued_at_utc: str
    expires_at_utc: str
    nonce: str
    signature: str

    def unsigned_payload(self):
        data = asdict(self)
        data.pop("signature")
        return data


def issue_handoff(
    *,
    project_id: str,
    repository_identity: str,
    work_instance_id: str,
    sender_agent_instance_id: str,
    receiver_agent_instance_id: str,
    sender_capabilities: Iterable[str],
    receiver_capabilities: Iterable[str],
    ownership_epoch: int,
    checkpoint_digest: str,
    policy_certificate_id: str,
    issued_at: datetime,
    expires_at: datetime,
    nonce: str,
    signing_key: bytes,
) -> ProofCarryingHandoff:
    require_project_id(project_id)
    require_repository_identity(repository_identity)
    sender = tuple(sorted(set(sender_capabilities)))
    receiver = tuple(sorted(set(receiver_capabilities)))
    if not set(receiver).issubset(set(sender)):
        raise HandoffVerificationError(ReasonCode.AUTHORITY_ESCALATION.value)
    issued = _aware_utc(issued_at)
    expires = _aware_utc(expires_at)
    if expires <= issued:
        raise ValueError("handoff expiry must be after issue time")
    base = {
        "handoff_id": _rid(f"handoff-{nonce}", "handoff_id"),
        "project_id": project_id,
        "repository_identity": repository_identity,
        "work_instance_id": _rid(work_instance_id, "work_instance_id"),
        "sender_agent_instance_id": sender_agent_instance_id,
        "receiver_agent_instance_id": receiver_agent_instance_id,
        "sender_capabilities": sender,
        "receiver_capabilities": receiver,
        "ownership_epoch": ownership_epoch,
        "checkpoint_digest": checkpoint_digest,
        "policy_certificate_id": policy_certificate_id,
        "issued_at_utc": _iso(issued),
        "expires_at_utc": _iso(expires),
        "nonce": _rid(nonce, "nonce"),
    }
    return ProofCarryingHandoff(signature=_sign(base, signing_key), **base)


def verify_handoff(
    handoff: ProofCarryingHandoff,
    *,
    verification_key: bytes,
    now: datetime,
    project_id: str,
    repository_identity: str,
    current_ownership_epoch: int,
) -> bool:
    now = _aware_utc(now)
    if not _verify_signature(handoff.unsigned_payload(), handoff.signature, verification_key):
        raise HandoffVerificationError(ReasonCode.HANDOFF_INVALID.value)
    if handoff.project_id != project_id:
        raise HandoffVerificationError(ReasonCode.PROJECT_MISMATCH.value)
    if handoff.repository_identity != repository_identity:
        raise HandoffVerificationError(ReasonCode.REPOSITORY_MISMATCH.value)
    if now >= _parse_iso(handoff.expires_at_utc):
        raise HandoffVerificationError(ReasonCode.HANDOFF_STALE.value)
    if handoff.ownership_epoch != current_ownership_epoch:
        raise HandoffVerificationError(ReasonCode.OWNERSHIP_STALE.value)
    if not set(handoff.receiver_capabilities).issubset(set(handoff.sender_capabilities)):
        raise HandoffVerificationError(ReasonCode.AUTHORITY_ESCALATION.value)
    return True


@dataclass(frozen=True)
class SchemaProtocolVersion:
    schema_id: str
    version: str
    minimum_reader: str
    minimum_writer: str
    compatibility_class: str = "BACKWARD_COMPATIBLE"
    unknown_field_behavior: str = "IGNORE_OPTIONAL_FAIL_UNKNOWN_REQUIRED"


class SchemaEvolutionRegistry:
    def __init__(self):
        self._versions: dict[tuple[str, str], SchemaProtocolVersion] = {}

    @staticmethod
    def _version_tuple(value: str):
        try:
            return tuple(int(x) for x in value.split("."))
        except Exception as exc:
            raise CompatibilityError("versions must be numeric dot-separated values") from exc

    def register(self, record: SchemaProtocolVersion):
        key = (record.schema_id, record.version)
        if key in self._versions:
            raise CompatibilityError("schema version already registered")
        self._versions[key] = record

    def require_writer_compatible(self, schema_id: str, version: str, writer_version: str, active_reader_versions: Iterable[str]):
        record = self._versions.get((schema_id, version))
        if record is None:
            raise CompatibilityError(ReasonCode.SCHEMA_INCOMPATIBLE.value)
        if self._version_tuple(writer_version) < self._version_tuple(record.minimum_writer):
            raise CompatibilityError(ReasonCode.SCHEMA_INCOMPATIBLE.value)
        minimum_reader = self._version_tuple(record.minimum_reader)
        if any(self._version_tuple(v) < minimum_reader for v in active_reader_versions):
            raise CompatibilityError(ReasonCode.SCHEMA_INCOMPATIBLE.value)
        return True


@dataclass
class HysteresisGate:
    enter_threshold: float
    exit_threshold: float
    cooldown_seconds: int = 0
    active: bool = False
    last_changed_at: datetime | None = None

    def __post_init__(self):
        if self.exit_threshold > self.enter_threshold:
            raise ValueError("exit_threshold must be <= enter_threshold")
        if self.cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be non-negative")

    def update(self, value: float, now: datetime) -> bool:
        now = _aware_utc(now)
        if self.last_changed_at is not None:
            elapsed = (now - self.last_changed_at).total_seconds()
            if elapsed < self.cooldown_seconds:
                return self.active
        if not self.active and value >= self.enter_threshold:
            self.active = True
            self.last_changed_at = now
        elif self.active and value <= self.exit_threshold:
            self.active = False
            self.last_changed_at = now
        return self.active
