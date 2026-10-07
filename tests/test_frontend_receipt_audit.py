from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from org_agent_mesh.frontend_execution_receipts import make_frontend_execution_receipt
from org_agent_mesh.frontend_receipt_audit import audit_receipt_directory


UTC = timezone.utc
PROJECT_ID = "intercommunicationsenhancements"
REPOSITORY = "boberino93-bit/intercommunicationsenhancements"
PUBLISHER_ID = "6ac63d38cc688191b9de4213ca40f951"


class FrontendReceiptAuditTests(unittest.TestCase):
    def setUp(self):
        self.bindings = {
            "bindings": [
                {
                    "binding_id": "bounded-capacity-hourly-frontend",
                    "backend_job_id": "global-bounded-capacity-hourly",
                    "frontend_automation_id": PUBLISHER_ID,
                }
            ]
        }
        self.scheduled = datetime(2026, 10, 7, 14, 12, tzinfo=UTC)
        self.receipt = make_frontend_execution_receipt(
            occurrence_id="global-bounded-capacity-hourly:20261007T1412Z",
            job_id="global-bounded-capacity-hourly",
            binding_id="bounded-capacity-hourly-frontend",
            frontend_automation_id=PUBLISHER_ID,
            scheduled_for=self.scheduled,
            observed_run_at=datetime(2026, 10, 7, 14, 16, 11, tzinfo=UTC),
            observed_at=datetime(2026, 10, 7, 14, 20, tzinfo=UTC),
        )

    def message(self, receipt=None, **overrides):
        value = {
            "schema": "org-agent-mesh/scheduler-frontend-receipt-message/v1",
            "message_type": "SCHEDULER_FRONTEND_EXECUTION_RECEIPT",
            "project_id": PROJECT_ID,
            "repository": REPOSITORY,
            "publisher_frontend_automation_id": PUBLISHER_ID,
            "authority_conveyed": False,
            "mutation_authority_conveyed": False,
            "receipt": (receipt or self.receipt).as_dict(),
        }
        value.update(overrides)
        return value

    def write(self, directory, name, value):
        path = Path(directory) / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def audit(self, directory):
        return audit_receipt_directory(
            bindings=self.bindings,
            receipt_dir=Path(directory),
            expected_project_id=PROJECT_ID,
            expected_repository=REPOSITORY,
            expected_publisher_frontend_automation_id=PUBLISHER_ID,
        )

    def test_valid_append_only_message_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "scheduler-frontend-receipt__one.json", self.message())
            audit = self.audit(tmp)
        self.assertEqual(audit["accepted_receipt_count"], 1)
        self.assertEqual(audit["rejected_receipt_count"], 0)
        self.assertEqual(
            audit["latest_verified_by_job"]["global-bounded-capacity-hourly"]["occurrence_id"],
            self.receipt.occurrence_id,
        )
        self.assertFalse(audit["authority_conveyed"])

    def test_wrong_publisher_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write(
                tmp,
                "scheduler-frontend-receipt__wrong-publisher.json",
                self.message(publisher_frontend_automation_id="different-automation"),
            )
            audit = self.audit(tmp)
        self.assertEqual(audit["accepted_receipt_count"], 0)
        self.assertEqual(audit["rejected_receipt_count"], 1)

    def test_wrong_project_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write(
                tmp,
                "scheduler-frontend-receipt__wrong-project.json",
                self.message(project_id="foreign-project"),
            )
            audit = self.audit(tmp)
        self.assertEqual(audit["accepted_receipt_count"], 0)
        self.assertEqual(audit["rejected_receipt_count"], 1)

    def test_binding_identity_mismatch_is_rejected(self):
        altered = self.receipt.as_dict()
        altered["frontend_automation_id"] = "dead-or-replaced-task"
        with tempfile.TemporaryDirectory() as tmp:
            self.write(
                tmp,
                "scheduler-frontend-receipt__bad-binding.json",
                self.message(receipt=type(self.receipt)(**altered)),
            )
            audit = self.audit(tmp)
        self.assertEqual(audit["accepted_receipt_count"], 0)
        self.assertEqual(audit["rejected_receipt_count"], 1)

    def test_occurrence_id_must_match_scheduled_time(self):
        altered = self.receipt.as_dict()
        altered["occurrence_id"] = "global-bounded-capacity-hourly:20261007T1512Z"
        with tempfile.TemporaryDirectory() as tmp:
            self.write(
                tmp,
                "scheduler-frontend-receipt__bad-occurrence.json",
                self.message(receipt=type(self.receipt)(**altered)),
            )
            audit = self.audit(tmp)
        self.assertEqual(audit["accepted_receipt_count"], 0)
        self.assertEqual(audit["rejected_receipt_count"], 1)

    def test_non_receipt_coordination_messages_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "ordinary-message.json", {"message": "not a scheduler receipt"})
            audit = self.audit(tmp)
        self.assertEqual(audit["accepted_receipt_count"], 0)
        self.assertEqual(audit["rejected_receipt_count"], 0)

    def test_exact_duplicate_receipt_is_idempotently_collapsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "scheduler-frontend-receipt__one.json", self.message())
            self.write(tmp, "scheduler-frontend-receipt__two.json", self.message())
            audit = self.audit(tmp)
        self.assertEqual(audit["accepted_receipt_count"], 1)
        self.assertEqual(audit["rejected_receipt_count"], 0)


if __name__ == "__main__":
    unittest.main()
