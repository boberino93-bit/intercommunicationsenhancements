from datetime import datetime
from pathlib import Path
import json
import unittest

from org_agent_mesh.scheduler_mutation_ledger import parse_jsonl, validate_ledger

ROOT = Path(__file__).resolve().parents[1]


class SchedulerHardeningContractTests(unittest.TestCase):
    def load(self, path):
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    def test_health_deadline_covers_receipt_acceptance_and_persistence(self):
        health = self.load("governance/SCHEDULER_HEALTH_POLICY.json")
        receipts = self.load("governance/SCHEDULER_FRONTEND_RECEIPT_POLICY.json")
        self.assertEqual(
            health["receipt_acceptance_window_minutes"],
            receipts["verification"]["default_maximum_start_delay_minutes"],
        )
        self.assertGreaterEqual(
            health["health_evidence_deadline_minutes"],
            health["receipt_acceptance_window_minutes"] + health["receipt_persistence_grace_minutes"],
        )

    def test_repair_grant_is_time_bounded_budgeted_and_human_renewed(self):
        grant = self.load("governance/SCHEDULER_ACTIVATION_GRANT_2026-10-07.json")
        issued = datetime.fromisoformat(grant["issued_at"].replace("Z", "+00:00"))
        expires = datetime.fromisoformat(grant["expires_at"].replace("Z", "+00:00"))
        self.assertLess(issued, expires)
        self.assertLessEqual((expires - issued).total_seconds(), 24 * 60 * 60)
        budget = grant["repair_budget"]
        self.assertGreater(budget["window_minutes"], 0)
        self.assertGreater(budget["max_repairs_per_target_in_window"], 0)
        self.assertGreater(budget["max_total_repairs_in_window"], 0)
        self.assertEqual(budget["on_exhaustion"], "QUARANTINE_REPAIR_AND_REQUIRE_HUMAN")
        self.assertFalse(grant["renewal"]["automatic_extension_allowed"])
        self.assertTrue(grant["renewal"]["explicit_current_human_authorization_required"])

    def test_bootstrap_requires_all_hardening_runtimes(self):
        bootstrap = self.load("bootstrap/INTERNAL_SCHEDULER_SERVICE.json")
        self.assertEqual(bootstrap["repair_guard_runtime"], "org_agent_mesh.scheduler_repair_guard")
        self.assertEqual(bootstrap["scheduler_work_gate_runtime"], "org_agent_mesh.scheduler_work_gate")
        self.assertEqual(bootstrap["scheduler_mutation_ledger_runtime"], "org_agent_mesh.scheduler_mutation_ledger")
        self.assertTrue(bootstrap["invariants"]["nonhealthy_lane_consequential_mutation_prohibited"])
        self.assertTrue(bootstrap["invariants"]["repair_budget_exhaustion_requires_quarantine"])
        self.assertTrue(bootstrap["invariants"]["scheduler_mutation_ledger_hash_chain_required"])

    def test_canonical_mutation_ledger_validates_end_to_end(self):
        path = ROOT / "governance" / "SCHEDULER_MUTATION_LEDGER_V2_2026-10-07.jsonl"
        result = validate_ledger(parse_jsonl(path.read_text(encoding="utf-8")))
        self.assertTrue(result.valid)
        self.assertGreaterEqual(result.event_count, 2)


if __name__ == "__main__":
    unittest.main()
