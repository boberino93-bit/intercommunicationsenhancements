from datetime import datetime, timezone
import unittest

from org_agent_mesh.scheduler_occurrence_guard import (
    OccurrenceClaimError,
    claim_from_dict,
    decide_occurrence_ownership,
    make_occurrence_claim,
    occurrence_claim_path,
)

UTC = timezone.utc


class SchedulerOccurrenceGuardTests(unittest.TestCase):
    def claim(self, *, receipt_id="receipt-a", claimed_minute=13):
        return make_occurrence_claim(
            occurrence_id="global-bounded-capacity-hourly:20261007T2212Z",
            job_id="global-bounded-capacity-hourly",
            binding_id="bounded-capacity-hourly-frontend",
            frontend_automation_id="bridge-id",
            receipt_id=receipt_id,
            scheduled_for=datetime(2026, 10, 7, 22, 12, tzinfo=UTC),
            claimed_at=datetime(2026, 10, 7, 22, claimed_minute, tzinfo=UTC),
        )

    def test_claim_path_is_deterministic_for_backend_occurrence(self):
        first = occurrence_claim_path("job-a:20261007T2212Z")
        second = occurrence_claim_path("job-a:20261007T2212Z")
        other = occurrence_claim_path("job-a:20261007T2312Z")
        self.assertEqual(first, second)
        self.assertNotEqual(first, other)
        self.assertTrue(first.startswith("scheduler-occurrence-claims/"))

    def test_no_existing_claim_requires_atomic_create_before_work(self):
        proposed = self.claim()
        decision = decide_occurrence_ownership(proposed_claim=proposed, existing_claim=None)
        self.assertFalse(decision.may_enter_project_work)
        self.assertEqual(decision.disposition, "CLAIM_CREATE_REQUIRED")

    def test_exact_readback_allows_occurrence_owner_to_continue(self):
        proposed = self.claim()
        existing = claim_from_dict(proposed.as_dict())
        decision = decide_occurrence_ownership(proposed_claim=proposed, existing_claim=existing)
        self.assertTrue(decision.may_enter_project_work)
        self.assertEqual(decision.disposition, "CLAIM_OWNED_BY_THIS_INVOCATION")

    def test_second_execution_receipt_for_same_occurrence_is_duplicate_noop(self):
        first = self.claim(receipt_id="receipt-a")
        second = self.claim(receipt_id="receipt-b", claimed_minute=14)
        decision = decide_occurrence_ownership(proposed_claim=second, existing_claim=first)
        self.assertFalse(decision.may_enter_project_work)
        self.assertEqual(decision.disposition, "DUPLICATE_OCCURRENCE_NOOP")

    def test_claim_identity_must_match_job_and_schedule(self):
        with self.assertRaises(OccurrenceClaimError):
            make_occurrence_claim(
                occurrence_id="wrong:20261007T2212Z",
                job_id="global-bounded-capacity-hourly",
                binding_id="bounded-capacity-hourly-frontend",
                frontend_automation_id="bridge-id",
                receipt_id="receipt-a",
                scheduled_for=datetime(2026, 10, 7, 22, 12, tzinfo=UTC),
                claimed_at=datetime(2026, 10, 7, 22, 13, tzinfo=UTC),
            )

    def test_claim_later_than_receipt_window_fails_closed(self):
        with self.assertRaises(OccurrenceClaimError):
            self.claim(receipt_id="late", claimed_minute=43)

    def test_claim_tampering_is_detected(self):
        value = self.claim().as_dict()
        value["receipt_id"] = "tampered"
        with self.assertRaises(OccurrenceClaimError):
            claim_from_dict(value)


if __name__ == "__main__":
    unittest.main()
