from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Callable, Mapping

from .reliability_v18_core import digest, ensure_aware, iso, parse_iso, verify_signature


class ConsequenceGatewayError(RuntimeError):
    pass


class EffectState(str, Enum):
    CONFIRMED = "CONFIRMED"
    NO_EFFECT = "NO_EFFECT"
    FAILED = "FAILED"
    UNKNOWN_EFFECT = "UNKNOWN_EFFECT"


class ProvenanceClass(str, Enum):
    AUTHORITY_BEARING = "AUTHORITY_BEARING"
    OBSERVATION_ONLY = "OBSERVATION_ONLY"


@dataclass(frozen=True)
class ProvenanceRecord:
    source_type: str
    source_ref: str
    classification: ProvenanceClass
    content_digest: str

    @property
    def grants_authority(self) -> bool:
        return self.classification == ProvenanceClass.AUTHORITY_BEARING


@dataclass(frozen=True)
class PreparedAction:
    action_id: str
    project_id: str
    work_id: str
    preparer_instance_id: str
    effect_class: str
    target: str
    parameters_digest: str
    policy_digest: str
    capability_digest: str
    precondition_digest: str
    ownership_epoch: int
    fence_token: str
    prepared_at_utc: str
    expires_at_utc: str
    action_digest: str

    @classmethod
    def create(
        cls, *,
        action_id: str,
        project_id: str,
        work_id: str,
        preparer_instance_id: str,
        effect_class: str,
        target: str,
        parameters: Mapping,
        policy_digest: str,
        capability_digest: str,
        precondition_digest: str,
        ownership_epoch: int,
        fence_token: str,
        prepared_at: datetime,
        expires_at: datetime,
    ) -> "PreparedAction":
        prepared_at = ensure_aware(prepared_at)
        expires_at = ensure_aware(expires_at)
        if expires_at <= prepared_at:
            raise ConsequenceGatewayError("prepared action expiry must be after preparation")
        if not all((action_id, project_id, work_id, preparer_instance_id, effect_class, target, fence_token)):
            raise ConsequenceGatewayError("prepared action identity field missing")
        unsigned = {
            "action_id": action_id,
            "project_id": project_id,
            "work_id": work_id,
            "preparer_instance_id": preparer_instance_id,
            "effect_class": effect_class,
            "target": target,
            "parameters_digest": digest(parameters),
            "policy_digest": policy_digest,
            "capability_digest": capability_digest,
            "precondition_digest": precondition_digest,
            "ownership_epoch": ownership_epoch,
            "fence_token": fence_token,
            "prepared_at_utc": iso(prepared_at),
            "expires_at_utc": iso(expires_at),
        }
        return cls(**unsigned, action_digest=digest(unsigned))

    def verify_self_digest(self) -> bool:
        unsigned = asdict(self)
        supplied = unsigned.pop("action_digest")
        return supplied == digest(unsigned)


@dataclass(frozen=True)
class CommitAuthorizationGrant:
    grant_id: str
    issuer_id: str
    issuer_instance_id: str
    project_id: str
    agent_instance_id: str
    action_digest: str
    allowed_operation: str
    allowed_target: str
    effect_class: str
    ownership_epoch: int
    fence_token: str
    policy_digest: str
    capability_digest: str
    precondition_digest: str
    issued_at_utc: str
    expires_at_utc: str
    max_uses: int
    nonce: str
    use_policy: str
    signature: str

    def unsigned(self) -> dict:
        raw = asdict(self)
        raw.pop("signature")
        return raw


@dataclass(frozen=True)
class CurrentCommitState:
    project_id: str
    actor_instance_id: str
    ownership_epoch: int
    fence_token: str
    policy_digest: str
    capability_digest: str
    precondition_digest: str
    health_allows_effect: bool
    session_active: bool = True
    task_authorized: bool = True
    required_capability_present: bool = True
    lease_valid: bool = True
    project_quarantined: bool = False
    cross_project_exchange_validated: bool = True


class CommitGrantVerifier:
    """Verifies externally issued exact-action grants. It cannot mint grants."""

    def __init__(self, trusted_issuers: Mapping[str, bytes]):
        self._keys = {k: bytes(v) for k, v in trusted_issuers.items()}
        self._uses: dict[str, int] = {}
        self._revoked: set[str] = set()
        self._cancelled_actions: set[str] = set()

    def revoke(self, grant_id: str) -> None:
        self._revoked.add(grant_id)

    def cancel_action(self, action_id: str) -> None:
        self._cancelled_actions.add(action_id)

    def verify_and_consume(
        self, *,
        prepared: PreparedAction,
        grant: CommitAuthorizationGrant,
        current: CurrentCommitState,
        now: datetime,
    ) -> None:
        now = ensure_aware(now)
        if not prepared.verify_self_digest():
            raise ConsequenceGatewayError("prepared action digest invalid")
        if prepared.action_id in self._cancelled_actions:
            raise ConsequenceGatewayError("prepared action cancelled")
        if now < parse_iso(prepared.prepared_at_utc) or now >= parse_iso(prepared.expires_at_utc):
            raise ConsequenceGatewayError("prepared action expired")
        key = self._keys.get(grant.issuer_id)
        if key is None or not verify_signature(grant.unsigned(), grant.signature, key):
            raise ConsequenceGatewayError("grant signature/issuer invalid")
        if grant.issuer_instance_id == prepared.preparer_instance_id:
            raise ConsequenceGatewayError("preparer cannot authorize its own consequential action")
        if grant.grant_id in self._revoked:
            raise ConsequenceGatewayError("grant revoked")
        if grant.max_uses < 1 or self._uses.get(grant.grant_id, 0) >= grant.max_uses:
            raise ConsequenceGatewayError("grant replay/use limit exceeded")
        if now < parse_iso(grant.issued_at_utc) or now >= parse_iso(grant.expires_at_utc):
            raise ConsequenceGatewayError("grant expired")
        exact = (
            grant.project_id == prepared.project_id == current.project_id
            and grant.agent_instance_id == prepared.preparer_instance_id == current.actor_instance_id
            and grant.action_digest == prepared.action_digest
            and grant.allowed_operation == prepared.effect_class
            and grant.allowed_target == prepared.target
            and grant.effect_class == prepared.effect_class
            and grant.ownership_epoch == prepared.ownership_epoch == current.ownership_epoch
            and grant.fence_token == prepared.fence_token == current.fence_token
            and grant.policy_digest == prepared.policy_digest == current.policy_digest
            and grant.capability_digest == prepared.capability_digest == current.capability_digest
            and grant.precondition_digest == prepared.precondition_digest == current.precondition_digest
        )
        if not exact:
            raise ConsequenceGatewayError("exact-action/current-state binding mismatch")
        if not current.session_active:
            raise ConsequenceGatewayError("agent session is not active")
        if not current.task_authorized:
            raise ConsequenceGatewayError("task is no longer authorized")
        if not current.required_capability_present:
            raise ConsequenceGatewayError("required capability is no longer present")
        if not current.lease_valid:
            raise ConsequenceGatewayError("lease is stale or invalid")
        if current.project_quarantined:
            raise ConsequenceGatewayError("project is quarantined")
        if prepared.effect_class.startswith("CROSS_PROJECT") and not current.cross_project_exchange_validated:
            raise ConsequenceGatewayError("cross-project exchange is not validated")
        if not current.health_allows_effect:
            raise ConsequenceGatewayError("current health blocks consequential effect")
        self._uses[grant.grant_id] = self._uses.get(grant.grant_id, 0) + 1


@dataclass(frozen=True)
class EffectOutcome:
    state: EffectState
    target_evidence_digest: str | None = None
    detail: str = ""


@dataclass(frozen=True)
class ConsequenceReceipt:
    attempt_id: str
    action_digest: str
    grant_id: str
    intended_effect: str
    attempted_effect: bool
    effect_state: str
    target_evidence_digest: str | None
    verified_at_utc: str
    retry_allowed: bool
    next_action: str
    authority: bool = False


class ConsequenceGateway:
    """Single prepare->authorize->commit boundary for protected effects."""

    def __init__(self, verifier: CommitGrantVerifier):
        self.verifier = verifier

    def commit(
        self, *,
        attempt_id: str,
        prepared: PreparedAction,
        grant: CommitAuthorizationGrant,
        current: CurrentCommitState,
        now: datetime,
        executor: Callable[[PreparedAction], EffectOutcome],
    ) -> ConsequenceReceipt:
        now = ensure_aware(now)
        self.verifier.verify_and_consume(prepared=prepared, grant=grant, current=current, now=now)
        try:
            outcome = executor(prepared)
        except Exception as exc:
            # The call may have crossed an external effect boundary before failing.
            outcome = EffectOutcome(EffectState.UNKNOWN_EFFECT, None, f"executor exception: {type(exc).__name__}")
        if not isinstance(outcome, EffectOutcome):
            raise ConsequenceGatewayError("executor must return EffectOutcome")
        if outcome.state == EffectState.UNKNOWN_EFFECT:
            retry_allowed = False
            next_action = "VERIFY_OR_RECOVERY"
        elif outcome.state == EffectState.CONFIRMED:
            retry_allowed = False
            next_action = "COMPLETE"
        elif outcome.state == EffectState.NO_EFFECT:
            retry_allowed = True
            next_action = "REPREPARE_AND_REAUTHORIZE"
        else:
            retry_allowed = False
            next_action = "DIAGNOSE"
        return ConsequenceReceipt(
            attempt_id=attempt_id,
            action_digest=prepared.action_digest,
            grant_id=grant.grant_id,
            intended_effect=f"{prepared.effect_class}:{prepared.target}",
            attempted_effect=True,
            effect_state=outcome.state.value,
            target_evidence_digest=outcome.target_evidence_digest,
            verified_at_utc=iso(now),
            retry_allowed=retry_allowed,
            next_action=next_action,
        )


class DataClass(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    SENSITIVE = "SENSITIVE"
    RESTRICTED = "RESTRICTED"


@dataclass(frozen=True)
class EgressReceipt:
    project_id: str
    work_id: str
    destination: str
    data_class: str
    sanitized: bool
    content_digest: str
    reason: str
    authority: bool = False


class EgressPolicy:
    def __init__(self, allowed: Mapping[str, set[DataClass]]):
        self.allowed = {target: frozenset(classes) for target, classes in allowed.items()}

    def authorize(self, *, target: str, data_class: DataClass) -> bool:
        if data_class == DataClass.RESTRICTED:
            raise ConsequenceGatewayError("restricted data cannot egress through this gateway")
        if data_class not in self.allowed.get(target, frozenset()):
            raise ConsequenceGatewayError("egress policy denied")
        return True

    def authorize_with_receipt(
        self, *,
        project_id: str,
        work_id: str,
        target: str,
        data_class: DataClass,
        content_digest: str,
        sanitized: bool,
        reason: str,
    ) -> EgressReceipt:
        self.authorize(target=target, data_class=data_class)
        if data_class == DataClass.SENSITIVE and not sanitized:
            raise ConsequenceGatewayError("sensitive egress requires sanitization")
        return EgressReceipt(project_id, work_id, target, data_class.value, sanitized, content_digest, reason)
