from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import AbstractSet

from .evidence_lifecycle import EvidenceReceipt, validate_evidence_receipt


class TwoReceiptGateError(ValueError):
    pass


@dataclass(frozen=True)
class GateReceipt:
    receipt: EvidenceReceipt
    path_id: str
    scope: str


@dataclass(frozen=True)
class TwoReceiptGate:
    first: GateReceipt
    second: GateReceipt
    expected_pre_state: str
    backup_ref: str
    propagation_ref: str

    def validate(
        self,
        *,
        subject_id: str,
        transaction_id: str,
        now: datetime,
        base_checks_ok: bool,
        warning_acknowledged: bool,
        consumed_receipt_ids: AbstractSet[str] = frozenset(),
    ) -> None:
        if not base_checks_ok:
            raise TwoReceiptGateError("BASE_CHECKS_REQUIRED")
        if not warning_acknowledged:
            raise TwoReceiptGateError("WARNING_ACK_REQUIRED")
        for item in (self.first, self.second):
            if not item.path_id or not item.scope:
                raise TwoReceiptGateError("RECEIPT_METADATA_REQUIRED")
            try:
                validate_evidence_receipt(
                    item.receipt,
                    expected_subject_id=subject_id,
                    expected_transaction_id=transaction_id,
                    now=now,
                    consumed_receipt_ids=consumed_receipt_ids,
                )
            except ValueError as exc:
                raise TwoReceiptGateError(str(exc)) from exc
        if self.first.receipt.receipt_id == self.second.receipt.receipt_id:
            raise TwoReceiptGateError("DISTINCT_RECEIPTS_REQUIRED")
        if self.first.path_id == self.second.path_id:
            raise TwoReceiptGateError("DISTINCT_PATHS_REQUIRED")
        if not self.expected_pre_state or not self.backup_ref or not self.propagation_ref:
            raise TwoReceiptGateError("PRE_CHANGE_BINDING_REQUIRED")

    def validate_post_change(
        self,
        *,
        expected_post_state: str,
        actual_post_state: str,
        verification_ref: str,
        verified: bool,
    ) -> None:
        if not verified or not verification_ref:
            raise TwoReceiptGateError("POST_CHANGE_VERIFICATION_REQUIRED")
        if not expected_post_state or actual_post_state != expected_post_state:
            raise TwoReceiptGateError("POST_CHANGE_STATE_MISMATCH")


def consume_gate_receipts(gate: TwoReceiptGate, consumed_receipt_ids: AbstractSet[str]) -> frozenset[str]:
    ids = {gate.first.receipt.receipt_id, gate.second.receipt.receipt_id}
    if "" in ids or any(item in consumed_receipt_ids for item in ids):
        raise TwoReceiptGateError("RECEIPT_REPLAY_DENIED")
    return frozenset(set(consumed_receipt_ids) | ids)
