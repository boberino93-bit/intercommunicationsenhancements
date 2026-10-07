from datetime import datetime, timedelta, timezone
import unittest

from org_agent_mesh.frontend_execution_receipts import (
    FrontendExecutionReceipt,
    FrontendExecutionReceiptError,
    make_frontend_execution_receipt,
    verify_frontend_execution_receipt,
)


UTC = timezone.utc


class FrontendExecutionReceiptTests(unittest.TestCase):
    def make(self):
        scheduled = datetime(2026, 10, 7, 14, 12, tzinfo=UTC)
        observed_run = datetime(2026, 10, 7, 14, 16, 11, tzinfo=UTC)
        observed_at = datetime(2026, 10, 7, 14, 20, tzinfo=UTC)
        receipt = make_frontend_execution_receipt(
            occurrence_id="global-bounded-capacity-hourly:20261007T1412Z",
            job_id="global-bounded-capacity-hourly",
            binding_id="bounded-capacity-hourly-frontend",
            frontend_automation_id="6ac63d38cc688191b9de4213ca40f951",
            scheduled_for=scheduled,
            observed_run_at=observed_run,
            observed_at=observed_at,
        )
        return scheduled, receipt

    def test_exact_identity_bound_receipt_verifies(self):
        scheduled, receipt = self.make()
        self.assertTrue(
            verify_frontend_execution_receipt(
                receipt,
                occurrence_id="global-bounded-capacity-hourly:20261007T1412Z",
                job_id="global-bounded-capacity-hourly",
                binding_id="bounded-capacity-hourly-frontend",
                frontend_automation_id="6ac63d38cc688191b9de4213ca40f951",
                scheduled_for=scheduled,
            )
        )

    def test_title_or_wrong_task_identity_cannot_verify(self):
        scheduled, receipt = self.make()
        self.assertFalse(
            verify_frontend_execution_receipt(
                receipt,
                occurrence_id="global-bounded-capacity-hourly:20261007T1412Z",
                job_id="global-bounded-capacity-hourly",
                binding_id="bounded-capacity-hourly-frontend",
                frontend_automation_id="different-task-id",
                scheduled_for=scheduled,
            )
        )

    def test_wrong_occurrence_cannot_verify(self):
        scheduled, receipt = self.make()
        self.assertFalse(
            verify_frontend_execution_receipt(
                receipt,
                occurrence_id="global-bounded-capacity-hourly:20261007T1512Z",
                job_id="global-bounded-capacity-hourly",
                binding_id="bounded-capacity-hourly-frontend",
                frontend_automation_id="6ac63d38cc688191b9de4213ca40f951",
                scheduled_for=scheduled,
            )
        )

    def test_receipt_cannot_convey_authority(self):
        scheduled, receipt = self.make()
        forged = FrontendExecutionReceipt(
            **{**receipt.as_dict(), "authority_conveyed": True}
        )
        self.assertFalse(
            verify_frontend_execution_receipt(
                forged,
                occurrence_id=receipt.occurrence_id,
                job_id=receipt.job_id,
                binding_id=receipt.binding_id,
                frontend_automation_id=receipt.frontend_automation_id,
                scheduled_for=scheduled,
            )
        )

    def test_excessively_late_run_does_not_verify_occurrence(self):
        scheduled, receipt = self.make()
        late = FrontendExecutionReceipt(
            **{
                **receipt.as_dict(),
                "observed_run_at": "2026-10-07T15:00:00Z",
                "observed_at": "2026-10-07T15:01:00Z",
            }
        )
        self.assertFalse(
            verify_frontend_execution_receipt(
                late,
                occurrence_id=receipt.occurrence_id,
                job_id=receipt.job_id,
                binding_id=receipt.binding_id,
                frontend_automation_id=receipt.frontend_automation_id,
                scheduled_for=scheduled,
                maximum_start_delay=timedelta(minutes=30),
            )
        )

    def test_make_rejects_run_before_schedule(self):
        with self.assertRaises(FrontendExecutionReceiptError):
            make_frontend_execution_receipt(
                occurrence_id="o",
                job_id="j",
                binding_id="b",
                frontend_automation_id="a",
                scheduled_for=datetime(2026, 10, 7, 14, 12, tzinfo=UTC),
                observed_run_at=datetime(2026, 10, 7, 14, 11, tzinfo=UTC),
                observed_at=datetime(2026, 10, 7, 14, 20, tzinfo=UTC),
            )


if __name__ == "__main__":
    unittest.main()
