import unittest

from org_agent_mesh.scheduler_work_gate import (
    WorkConsequence,
    evaluate_scheduler_work_gate,
)


class SchedulerWorkGateTests(unittest.TestCase):
    def test_healthy_lane_still_passes_only_to_normal_authority_gates(self):
        decision = evaluate_scheduler_work_gate(
            lane_health_state="HEALTHY",
            consequence=WorkConsequence.PROTECTED_MUTATION,
        )
        self.assertTrue(decision.allowed)
        self.assertIn("NORMAL_AUTHORITY_STILL_REQUIRED", decision.reason)

    def test_recovering_lane_may_continue_read_only_work(self):
        decision = evaluate_scheduler_work_gate(
            lane_health_state="RECOVERING",
            consequence=WorkConsequence.READ_ONLY,
        )
        self.assertTrue(decision.allowed)

    def test_degraded_lane_may_preserve_append_only_observability(self):
        decision = evaluate_scheduler_work_gate(
            lane_health_state="DEGRADED_MISSING_EXECUTION_EVIDENCE",
            consequence=WorkConsequence.APPEND_ONLY_OBSERVABILITY,
        )
        self.assertTrue(decision.allowed)

    def test_nonhealthy_lane_cannot_make_consequential_mutation(self):
        for state in ["RECOVERING", "DEGRADED_MISSING_EXECUTION_EVIDENCE", "UNQUALIFIED"]:
            with self.subTest(state=state):
                decision = evaluate_scheduler_work_gate(
                    lane_health_state=state,
                    consequence=WorkConsequence.PROTECTED_MUTATION,
                )
                self.assertFalse(decision.allowed)

    def test_unknown_health_state_fails_closed(self):
        decision = evaluate_scheduler_work_gate(
            lane_health_state="MAYBE_FINE",
            consequence=WorkConsequence.READ_ONLY,
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "UNKNOWN_SCHEDULER_HEALTH_STATE_FAILS_CLOSED")


if __name__ == "__main__":
    unittest.main()
