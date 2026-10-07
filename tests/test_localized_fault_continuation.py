from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LocalizedFaultContinuationTests(unittest.TestCase):
    def test_machine_bootstrap_requires_localized_continue(self):
        bootstrap = json.loads((ROOT / "AGENT_BOOTSTRAP.json").read_text())
        ac = bootstrap["autonomous_continuation"]
        self.assertTrue(ac["localized_fail_closed"])
        self.assertTrue(ac["continue_unaffected_safe_work"])
        self.assertEqual(ac["blocked_branch_policy"], "PERSIST_BLOCKER_AND_CONTINUE_OTHER_SAFE_WORK")
        self.assertEqual(bootstrap["rules"]["fail_closed_scope"], "AFFECTED_MUTATION_OR_BRANCH_ONLY")
        self.assertTrue(bootstrap["rules"]["continue_unaffected_safe_work"])

    def test_existing_hard_gates_already_require_safe_continuation(self):
        mutation = (ROOT / "protocols/mutation_authorization.md").read_text()
        autonomous = (ROOT / "protocols/autonomous_continuation.md").read_text()
        completion = (ROOT / "protocols/completion_integrity.md").read_text()
        self.assertIn("continue useful read-only inspection", mutation)
        self.assertIn("A blocker affects the smallest unsafe scope possible", autonomous)
        self.assertIn("continue every unrelated safe branch", autonomous)
        self.assertIn("INCOMPLETE_BLOCKED", completion)

    def test_delivery_policy_turns_stop_regression_into_failure(self):
        policy = json.loads((ROOT / "governance/DELIVERY_INTELLIGENCE_PREFLIGHT_POLICY.json").read_text())
        lfc = policy["localized_fault_continuation"]
        self.assertEqual(lfc["invariant"], "LOCALIZED_MUTATION_FAULT_IS_NOT_GLOBAL_STOP")
        self.assertIn("CONTINUE_UNAFFECTED_SAFE_WORK_AUTOMATICALLY", lfc["on_authorization_or_execution_fault"])
        self.assertEqual(lfc["required_status_when_applicable"], "MUTATION_LANE_BLOCKED_CONTINUING_SAFE_WORK")

    def test_roles_cannot_treat_fail_closed_as_global_idle(self):
        for path in (
            "bootstrap/RESEARCH.md",
            "bootstrap/MANAGER.md",
            "bootstrap/PRIMARY.md",
            "research_swarm/prompts/master.md",
        ):
            text = (ROOT / path).read_text().lower()
            self.assertIn("continue", text, path)
            self.assertIn("safe", text, path)
            self.assertTrue("quarantine" in text or "smallest unsafe scope" in text, path)


if __name__ == "__main__":
    unittest.main()
