from datetime import datetime, timedelta, timezone
import unittest

from org_agent_mesh.evidence_lifecycle import EvidenceReceipt
from org_agent_mesh.two_receipt_gate import (
    GateReceipt,
    TwoReceiptGate,
    TwoReceiptGateError,
    consume_gate_receipts,
)


class TwoReceiptGateTests(unittest.TestCase):
    def make_gate(self):
        now = datetime.now(timezone.utc)
        first = EvidenceReceipt(
            receipt_id="A",
            subject_id="owner",
            transaction_id="CASE",
            verifier_ref="verifier:a",
            issued_at=now - timedelta(seconds=1),
            expires_at=now + timedelta(minutes=5),
        )
        second = EvidenceReceipt(
            receipt_id="B",
            subject_id="owner",
            transaction_id="CASE",
            verifier_ref="verifier:b",
            issued_at=now - timedelta(seconds=1),
            expires_at=now + timedelta(minutes=5),
        )
        gate = TwoReceiptGate(
            first=GateReceipt(first, "PATH_A", "global"),
            second=GateReceipt(second, "PATH_B", "global"),
            expected_pre_state="pre",
            backup_ref="backup/ref",
            propagation_ref="propagation/ref",
        )
        return gate, now

    def test_valid_gate(self):
        gate, now = self.make_gate()
        gate.validate(
            subject_id="owner",
            transaction_id="CASE",
            now=now,
            base_checks_ok=True,
            warning_acknowledged=True,
        )

    def test_distinct_paths_required(self):
        gate, now = self.make_gate()
        duplicate_path = TwoReceiptGate(
            first=gate.first,
            second=GateReceipt(gate.second.receipt, "PATH_A", "global"),
            expected_pre_state=gate.expected_pre_state,
            backup_ref=gate.backup_ref,
            propagation_ref=gate.propagation_ref,
        )
        with self.assertRaisesRegex(TwoReceiptGateError, "DISTINCT_PATHS_REQUIRED"):
            duplicate_path.validate(
                subject_id="owner",
                transaction_id="CASE",
                now=now,
                base_checks_ok=True,
                warning_acknowledged=True,
            )

    def test_replay_is_denied(self):
        gate, now = self.make_gate()
        consumed = consume_gate_receipts(gate, frozenset())
        with self.assertRaises(TwoReceiptGateError):
            gate.validate(
                subject_id="owner",
                transaction_id="CASE",
                now=now,
                base_checks_ok=True,
                warning_acknowledged=True,
                consumed_receipt_ids=consumed,
            )

    def test_post_change_verification_required(self):
        gate, _ = self.make_gate()
        with self.assertRaisesRegex(TwoReceiptGateError, "POST_CHANGE_VERIFICATION_REQUIRED"):
            gate.validate_post_change(
                expected_post_state="post",
                actual_post_state="post",
                verification_ref="",
                verified=False,
            )

    def test_post_change_state_must_match(self):
        gate, _ = self.make_gate()
        with self.assertRaisesRegex(TwoReceiptGateError, "POST_CHANGE_STATE_MISMATCH"):
            gate.validate_post_change(
                expected_post_state="post",
                actual_post_state="other",
                verification_ref="verification:1",
                verified=True,
            )


if __name__ == "__main__":
    unittest.main()
