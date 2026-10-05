from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AbstractSet


class EvidenceLifecycleError(ValueError):
    pass


@dataclass(frozen=True)
class EvidenceReceipt:
    receipt_id: str
    subject_id: str
    transaction_id: str
    verifier_ref: str
    issued_at: datetime
    expires_at: datetime
    verified: bool = True
    consumed: bool = False


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise EvidenceLifecycleError("EVIDENCE_TIMEZONE_REQUIRED")
    return value.astimezone(timezone.utc)


def validate_evidence_receipt(
    receipt: EvidenceReceipt,
    *,
    expected_subject_id: str,
    expected_transaction_id: str,
    now: datetime,
    consumed_receipt_ids: AbstractSet[str] = frozenset(),
) -> None:
    if not receipt.receipt_id or not receipt.verifier_ref:
        raise EvidenceLifecycleError("EVIDENCE_REFERENCE_REQUIRED")
    if not receipt.verified:
        raise EvidenceLifecycleError("EVIDENCE_NOT_VERIFIED")
    if receipt.consumed or receipt.receipt_id in consumed_receipt_ids:
        raise EvidenceLifecycleError("EVIDENCE_REPLAY_DENIED")
    if receipt.subject_id != expected_subject_id:
        raise EvidenceLifecycleError("EVIDENCE_SUBJECT_MISMATCH")
    if receipt.transaction_id != expected_transaction_id:
        raise EvidenceLifecycleError("EVIDENCE_TRANSACTION_MISMATCH")
    current = _utc(now)
    issued = _utc(receipt.issued_at)
    expires = _utc(receipt.expires_at)
    if current < issued:
        raise EvidenceLifecycleError("EVIDENCE_NOT_YET_VALID")
    if current > expires:
        raise EvidenceLifecycleError("EVIDENCE_EXPIRED")


def consume_evidence_receipt(receipt_id: str, consumed_receipt_ids: AbstractSet[str]) -> frozenset[str]:
    if not receipt_id:
        raise EvidenceLifecycleError("EVIDENCE_ID_REQUIRED")
    if receipt_id in consumed_receipt_ids:
        raise EvidenceLifecycleError("EVIDENCE_REPLAY_DENIED")
    return frozenset(set(consumed_receipt_ids) | {receipt_id})
