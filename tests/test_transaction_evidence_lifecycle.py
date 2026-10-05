from datetime import datetime, timedelta, timezone
import unittest

from org_agent_mesh.durable_record_guard import DurableRecordGuardError, validate_durable_record
from org_agent_mesh.evidence_lifecycle import (
    EvidenceLifecycleError,
    EvidenceReceipt,
    consume_evidence_receipt,
    validate_evidence_receipt,
)


class TransactionEvidenceLifecycleTests(unittest.TestCase):
    def make_receipt(self, **overrides):
        now = datetime.now(timezone.utc)
        data = {
            "receipt_id": "R-1",
            "subject_id": "owner",
            "transaction_id": "TX-1",
            "verifier_ref": "external-verifier:1",
            "issued_at": now - timedelta(seconds=1),
            "expires_at": now + timedelta(minutes=5),
            "verified": True,
            "consumed": False,
        }
        data.update(overrides)
        return EvidenceReceipt(**data), now

    def test_fresh_bound_receipt_is_valid(self):
        receipt, now = self.make_receipt()
        validate_evidence_receipt(
            receipt,
            expected_subject_id="owner",
            expected_transaction_id="TX-1",
            now=now,
        )

    def test_expired_receipt_is_denied(self):
        now = datetime.now(timezone.utc)
        receipt, _ = self.make_receipt(
            issued_at=now - timedelta(minutes=10),
            expires_at=now - timedelta(minutes=1),
        )
        with self.assertRaisesRegex(EvidenceLifecycleError, "EVIDENCE_EXPIRED"):
            validate_evidence_receipt(
                receipt,
                expected_subject_id="owner",
                expected_transaction_id="TX-1",
                now=now,
            )

    def test_replayed_receipt_is_denied(self):
        receipt, now = self.make_receipt()
        consumed = consume_evidence_receipt(receipt.receipt_id, frozenset())
        with self.assertRaisesRegex(EvidenceLifecycleError, "EVIDENCE_REPLAY_DENIED"):
            validate_evidence_receipt(
                receipt,
                expected_subject_id="owner",
                expected_transaction_id="TX-1",
                now=now,
                consumed_receipt_ids=consumed,
            )

    def test_wrong_transaction_is_denied(self):
        receipt, now = self.make_receipt()
        with self.assertRaisesRegex(EvidenceLifecycleError, "EVIDENCE_TRANSACTION_MISMATCH"):
            validate_evidence_receipt(
                receipt,
                expected_subject_id="owner",
                expected_transaction_id="TX-2",
                now=now,
            )

    def test_nested_prohibited_durable_field_is_denied(self):
        with self.assertRaises(DurableRecordGuardError):
            validate_durable_record(
                {"outer": {"ephemeral_value": "present"}},
                prohibited_fields={"ephemeral_value"},
                context="test",
            )

    def test_prohibited_label_with_live_value_is_denied(self):
        with self.assertRaises(DurableRecordGuardError):
            validate_durable_record(
                {"body": "Sensitive-Label: live-value"},
                prohibited_fields=set(),
                prohibited_labels={"Sensitive-Label"},
                context="test",
            )

    def test_redacted_label_is_allowed(self):
        validate_durable_record(
            {"body": "Sensitive-Label: removed"},
            prohibited_fields=set(),
            prohibited_labels={"Sensitive-Label"},
            context="test",
        )


if __name__ == "__main__":
    unittest.main()
