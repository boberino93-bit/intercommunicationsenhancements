from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SchedulerHealthPolicyTests(unittest.TestCase):
    def test_health_policy_fails_closed_on_missing_evidence_and_common_mode(self):
        policy = json.loads((ROOT / "governance" / "SCHEDULER_HEALTH_POLICY.json").read_text())
        self.assertEqual(policy["required_consecutive_verified_occurrences"], 3)
        self.assertTrue(policy["rules"]["missing_overdue_receipt_is_degraded"])
        self.assertTrue(policy["rules"]["zero_receipts_is_not_success"])
        self.assertTrue(policy["rules"]["single_successful_occurrence_is_not_sustained_health"])
        self.assertTrue(policy["common_mode_boundary"]["chatgpt_bridge_and_slot1_share_provider_failure_domain"])
        self.assertTrue(policy["common_mode_boundary"]["secondary_chatgpt_task_is_not_independent_provider_failover"])
        self.assertTrue(policy["common_mode_boundary"]["absence_of_out_of_band_actuator_must_be_reported_as_capability_blocked_not_healthy"])


if __name__ == "__main__":
    unittest.main()
