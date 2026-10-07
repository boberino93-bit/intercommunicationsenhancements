from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SchedulerHealthPolicyTests(unittest.TestCase):
    def test_health_policy_fails_closed_on_missing_evidence_and_common_mode(self):
        policy = json.loads((ROOT / "governance" / "SCHEDULER_HEALTH_POLICY.json").read_text())
        self.assertEqual(policy["required_consecutive_verified_occurrences"], 3)
        self.assertEqual(policy["receipt_acceptance_window_minutes"], 30)
        self.assertEqual(policy["receipt_persistence_grace_minutes"], 5)
        self.assertGreaterEqual(
            policy["health_evidence_deadline_minutes"],
            policy["receipt_acceptance_window_minutes"] + policy["receipt_persistence_grace_minutes"],
        )
        self.assertTrue(policy["rules"]["missing_overdue_receipt_is_degraded"])
        self.assertTrue(policy["rules"]["zero_receipts_is_not_success"])
        self.assertTrue(policy["rules"]["single_successful_occurrence_is_not_sustained_health"])
        self.assertTrue(policy["rules"]["absence_before_health_evidence_deadline_is_not_missing_execution_failure"])
        self.assertTrue(policy["common_mode_boundary"]["chatgpt_bridge_and_slot1_share_provider_failure_domain"])
        self.assertTrue(policy["common_mode_boundary"]["secondary_chatgpt_task_is_not_independent_provider_failover"])
        self.assertTrue(policy["common_mode_boundary"]["absence_of_out_of_band_actuator_must_be_reported_as_capability_blocked_not_healthy"])

    def test_nonhealthy_lanes_cannot_do_consequential_mutation(self):
        policy = json.loads((ROOT / "governance" / "SCHEDULER_HEALTH_POLICY.json").read_text())
        work = policy["work_admission"]
        self.assertIn("PROTECTED_MUTATION", work["HEALTHY"])
        for state in ["RECOVERING", "DEGRADED_MISSING_EXECUTION_EVIDENCE", "UNQUALIFIED"]:
            self.assertNotIn("REVERSIBLE_MUTATION", work[state])
            self.assertNotIn("PROTECTED_MUTATION", work[state])
            self.assertIn("READ_ONLY", work[state])
            self.assertIn("APPEND_ONLY_OBSERVABILITY", work[state])
        self.assertTrue(work["health_gate_is_additional_restriction_not_authority"])

    def test_mutation_ledger_is_hash_chained(self):
        policy = json.loads((ROOT / "governance" / "SCHEDULER_MUTATION_LEDGER_POLICY.json").read_text())
        self.assertEqual(policy["hash_algorithm"], "SHA-256")
        self.assertTrue(policy["requirements"]["append_only"])
        self.assertTrue(policy["requirements"]["strict_sequence"])
        self.assertTrue(policy["requirements"]["previous_event_hash_required"])
        self.assertTrue(policy["requirements"]["event_hash_required"])
        self.assertTrue(policy["requirements"]["silent_rewrite_or_reordering_is_invalid"])


if __name__ == "__main__":
    unittest.main()
