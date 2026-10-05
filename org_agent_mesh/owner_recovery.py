from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Mapping

from .durable_record_guard import validate_durable_record
from .evidence_lifecycle import EvidenceReceipt, validate_evidence_receipt


class OwnerRecoveryError(ValueError):
    pass


@dataclass(frozen=True)
class RecoveryFactorEvidence:
    factor_type: str
    evidence_id: str
    independence_domain: str
    verified: bool
    owner_id: str = ""
    request_id: str = ""
    verifier_ref: str = ""
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    consumed: bool = False
    metadata: Mapping[str, Any] | None = None

    def lifecycle_receipt(self) -> EvidenceReceipt:
        if self.issued_at is None or self.expires_at is None:
            raise OwnerRecoveryError("RECOVERY_EVIDENCE_FRESHNESS_REQUIRED")
        return EvidenceReceipt(
            receipt_id=self.evidence_id,
            subject_id=self.owner_id,
            transaction_id=self.request_id,
            verifier_ref=self.verifier_ref,
            issued_at=self.issued_at,
            expires_at=self.expires_at,
            verified=self.verified,
            consumed=self.consumed,
        )


@dataclass(frozen=True)
class RecoveryReplayLedger:
    consumed_evidence_ids: frozenset[str] = frozenset()
    consumed_request_ids: frozenset[str] = frozenset()

    def consume(self, decision: "OwnerRecoveryDecision") -> "RecoveryReplayLedger":
        if decision.request_id in self.consumed_request_ids:
            raise OwnerRecoveryError("RECOVERY_REQUEST_REPLAY_DENIED")
        evidence_ids = [item.evidence_id for item in decision.factors if item.verified]
        if any(item in self.consumed_evidence_ids for item in evidence_ids):
            raise OwnerRecoveryError("RECOVERY_EVIDENCE_REPLAY_DENIED")
        return RecoveryReplayLedger(
            consumed_evidence_ids=frozenset(set(self.consumed_evidence_ids) | set(evidence_ids)),
            consumed_request_ids=frozenset(set(self.consumed_request_ids) | {decision.request_id}),
        )


@dataclass(frozen=True)
class OwnerRecoveryDecision:
    request_id: str
    owner_id: str
    target_scope: str
    factors: tuple[RecoveryFactorEvidence, ...]

    def validate(self, policy: Mapping[str, Any], *, now: datetime, ledger: RecoveryReplayLedger | None = None) -> str:
        if not self.request_id or not self.owner_id or not self.target_scope:
            raise OwnerRecoveryError("RECOVERY_REQUEST_INCOMPLETE")
        ledger = ledger or RecoveryReplayLedger()
        if self.request_id in ledger.consumed_request_ids:
            raise OwnerRecoveryError("RECOVERY_REQUEST_REPLAY_DENIED")
        verified = [item for item in self.factors if item.verified]
        if len({item.evidence_id for item in verified}) != len(verified):
            raise OwnerRecoveryError("RECOVERY_EVIDENCE_IDS_MUST_BE_UNIQUE")
        prohibited_fields = set(policy.get("durable_prohibited_fields", []))
        for item in verified:
            try:
                validate_evidence_receipt(
                    item.lifecycle_receipt(),
                    expected_subject_id=self.owner_id,
                    expected_transaction_id=self.request_id,
                    now=now,
                    consumed_receipt_ids=ledger.consumed_evidence_ids,
                )
            except ValueError as exc:
                raise OwnerRecoveryError(str(exc)) from exc
            if item.metadata is not None and prohibited_fields:
                try:
                    validate_durable_record(item.metadata, prohibited_fields=prohibited_fields, context="recovery_evidence")
                except ValueError as exc:
                    raise OwnerRecoveryError(str(exc)) from exc
        minimum = int(policy.get("minimum_factor_quorum", 2))
        if len(verified) < minimum:
            raise OwnerRecoveryError("RECOVERY_FACTOR_QUORUM_NOT_MET")
        domains = {item.independence_domain for item in verified if item.independence_domain}
        if len(domains) < minimum:
            raise OwnerRecoveryError("RECOVERY_INDEPENDENCE_QUORUM_NOT_MET")
        strong = set(policy.get("strong_factors", []))
        if policy.get("strong_factor_required_when_available", True):
            if not any(item.factor_type in strong for item in verified):
                raise OwnerRecoveryError("STRONG_RECOVERY_FACTOR_REQUIRED")
        if not policy.get("same_device_dual_totp_counts_as_independent", False):
            totp_domains = [item.independence_domain for item in verified if item.factor_type == "AUTHENTICATOR_TOTP"]
            if len(totp_domains) >= 2 and len(set(totp_domains)) != len(totp_domains):
                raise OwnerRecoveryError("SAME_DEVICE_TOTP_NOT_INDEPENDENT")
        return str(policy.get("recovery_outcome", "ROTATE_CREDENTIAL_AND_RETURN_TO_NORMAL_AUTHORIZATION"))


def verified_factor_types(factors: Iterable[RecoveryFactorEvidence]) -> frozenset[str]:
    return frozenset(item.factor_type for item in factors if item.verified)
