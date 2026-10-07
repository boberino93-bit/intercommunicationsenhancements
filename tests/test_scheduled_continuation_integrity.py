from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ScheduledContinuationIntegrityTests(unittest.TestCase):
    def load(self, path):
        return json.loads((ROOT / path).read_text())

    def test_scheduler_bootstrap_loads_continuation_contracts(self):
        bootstrap = self.load("bootstrap/INTERNAL_SCHEDULER_SERVICE.json")
        self.assertIn("protocols/autonomous_continuation.md", bootstrap["load_with"])
        self.assertIn("protocols/scheduled_continuation_integrity.md", bootstrap["load_with"])
        self.assertTrue(bootstrap["invariants"]["scheduled_worker_continuation_integrity_required"])
        self.assertTrue(bootstrap["invariants"]["blocked_mutation_blocks_only_affected_branch"])
        self.assertTrue(bootstrap["invariants"]["blocker_finalization_requires_no_remaining_safe_work"])
        self.assertTrue(bootstrap["invariants"]["continuation_integrity_does_not_expand_authority_or_scope"])

    def test_policy_requires_safe_work_exhaustion_before_blocker_finalization(self):
        policy = self.load("governance/INTERNAL_SPAWN_SCHEDULER_POLICY.json")
        integrity = policy["continuation_integrity"]
        self.assertTrue(integrity["required_for_scheduled_workers"])
        self.assertTrue(integrity["blocked_action_blocks_only_affected_branch"])
        self.assertTrue(integrity["must_exhaust_useful_safe_in_scope_work_before_blocker_finalization"])
        self.assertTrue(integrity["authorization_blocked_mutation_must_not_end_read_only_safe_work"])
        self.assertTrue(integrity["remaining_safe_work_must_be_false_for_blocker_terminal_outcome"])
        self.assertTrue(integrity["human_decision_required_only_when_no_useful_safe_work_remains"])

    def test_continuation_does_not_create_authority_or_new_scope(self):
        policy = self.load("governance/INTERNAL_SPAWN_SCHEDULER_POLICY.json")
        integrity = policy["continuation_integrity"]
        self.assertTrue(integrity["continuation_may_not_cross_project_or_claim_new_work_unit"])
        self.assertTrue(integrity["continuation_does_not_grant_mutation_authority"])
        self.assertTrue(integrity["hold_pause_stop_override_continuation"])
        self.assertTrue(integrity["handoff_transfers_context_not_authority"])

    def test_blocked_capability_preserves_useful_progress_semantics(self):
        policy = self.load("governance/INTERNAL_SPAWN_SCHEDULER_POLICY.json")
        integrity = policy["continuation_integrity"]
        self.assertTrue(integrity["capability_blocked_only_after_permitted_fallbacks_and_safe_work_exhausted"])
        self.assertTrue(integrity["checkpoint_io_blocked_does_not_erase_completed_useful_work"])
        self.assertTrue(integrity["work_advanced_may_coexist_with_secondary_blocker"])
        self.assertEqual(
            policy["failure_semantics"]["premature_blocker_finalization"],
            "CONTINUATION_INTEGRITY_VIOLATION",
        )

    def test_unfinished_work_survives_invocation_boundary(self):
        policy = self.load("governance/INTERNAL_SPAWN_SCHEDULER_POLICY.json")
        integrity = policy["continuation_integrity"]
        self.assertTrue(integrity["unfinished_safe_work_survives_invocation_boundary"])
        self.assertTrue(integrity["unfinished_work_must_not_be_marked_completed"])
        self.assertTrue(
            integrity[
                "successor_must_scan_valid_unresolved_continuation_handoffs_before_lower_priority_fresh_work"
            ]
        )
        self.assertTrue(integrity["successor_resume_requires_project_role_claim_fence_and_control_revalidation"])
        self.assertTrue(integrity["higher_priority_p0_p3_work_may_preempt_continuation"])
        self.assertTrue(integrity["live_owner_prevents_duplicate_continuation"])
        self.assertEqual(
            policy["failure_semantics"]["unfinished_work_abandoned_at_invocation_boundary"],
            "CONTINUATION_HANDOFF_MISSING",
        )

    def test_finalization_observability_records_remaining_safe_work_and_handoff(self):
        policy = self.load("governance/INTERNAL_SPAWN_SCHEDULER_POLICY.json")
        obs = policy["observability"]
        self.assertTrue(obs["record_blocked_actions"])
        self.assertTrue(obs["record_safe_fallbacks_considered"])
        self.assertTrue(obs["record_safe_fallbacks_completed"])
        self.assertTrue(obs["record_remaining_safe_work_at_finalization"])
        self.assertTrue(obs["record_continuation_handoff_required"])
        self.assertTrue(obs["record_continuation_handoff_ref"])
        self.assertTrue(obs["record_successor_acceptance_when_resumed"])
        self.assertTrue(obs["record_remaining_human_gate"])

    def test_protocol_explicitly_prohibits_premature_halt_and_abandonment(self):
        text = (ROOT / "protocols/scheduled_continuation_integrity.md").read_text()
        self.assertIn("A local blocker blocks the affected action or branch only.", text)
        self.assertIn("A blocker-based terminal outcome requires `remaining_safe_work = false`.", text)
        self.assertIn("Inter-occurrence continuation", text)
        self.assertIn("MUST inspect unresolved valid continuation handoffs", text)
        self.assertIn("must not be falsely recorded as completed", text)
        self.assertIn("Continuation integrity never authorizes", text)
        self.assertIn("does **not** grant mutation authority", text)


if __name__ == "__main__":
    unittest.main()
