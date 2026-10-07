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
BRIDGE_ID = "bridge-id"


class SchedulerDuplicateReceiptTests(unittest.TestCase):
    def setUp(self):
        self.bindings = {
            "bindings": [
                {
                    "binding_id": "bounded-capacity-hourly-frontend",
                    "backend_job_id": "global-bounded-capacity-hourly",
                    "frontend_automation_id": BRIDGE_ID,
                }
            ]
        }
        self.scheduled = datetime(2026, 10, 7, 22, 12, tzinfo=UTC)

    def receipt(self, observed_second):
        return make_frontend_execution_receipt(
            occurrence_id="global-bounded-capacity-hourly:20261007T2212Z",
            job_id="global-bounded-capacity-hourly",
            binding_id="bounded-capacity-hourly-frontend",
            frontend_automation_id=BRIDGE_ID,
            scheduled_for=self.scheduled,
            observed_run_at=datetime(2026, 10, 7, 22, 12, observed_second, tzinfo=UTC),
            observed_at=datetime(2026, 10, 7, 22, 13, tzinfo=UTC),
        )

    def message(self, receipt):
        return {
            "schema": "org-agent-mesh/scheduler-frontend-receipt-message/v1",
            "message_type": "SCHEDULER_FRONTEND_EXECUTION_RECEIPT",
            "project_id": PROJECT_ID,
            "repository": REPOSITORY,
            "publisher_frontend_automation_id": BRIDGE_ID,
            "authority_conveyed": False,
            "mutation_authority_conveyed": False,
            "receipt": receipt.as_dict(),
        }

    def audit(self, values):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for index, value in enumerate(values, start=1):
                (root / f"scheduler-frontend-receipt__{index}.json").write_text(
                    json.dumps(value), encoding="utf-8"
                )
            return audit_receipt_directory(
                bindings=self.bindings,
                receipt_dir=root,
                expected_project_id=PROJECT_ID,
                expected_repository=REPOSITORY,
                expected_publisher_frontend_automation_id=BRIDGE_ID,
            )

    def test_two_distinct_receipts_for_one_occurrence_fail_health_evidence(self):
        first = self.message(self.receipt(5))
        second = self.message(self.receipt(9))
        audit = self.audit([first, second])
        self.assertEqual(audit["duplicate_occurrence_count"], 1)
        self.assertEqual(
            audit["duplicate_occurrence_ids"],
            ["global-bounded-capacity-hourly:20261007T2212Z"],
        )
        self.assertEqual(audit["accepted_receipt_count"], 0)
        self.assertEqual(audit["raw_accepted_receipt_count"], 1)
        self.assertEqual(audit["rejected_receipt_count"], 1)
        self.assertNotIn("global-bounded-capacity-hourly", audit["latest_verified_by_job"])

    def test_exact_duplicate_message_remains_idempotent_not_duplicate_execution(self):
        message = self.message(self.receipt(5))
        audit = self.audit([message, message])
        self.assertEqual(audit["duplicate_occurrence_count"], 0)
        self.assertEqual(audit["accepted_receipt_count"], 1)
        self.assertEqual(audit["rejected_receipt_count"], 0)


if __name__ == "__main__":
    unittest.main()
