from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SchedulerEvidenceBranchTests(unittest.TestCase):
    def load(self, path):
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    def test_mutation_journal_runtime_writes_leave_main(self):
        policy = self.load("governance/SCHEDULER_MUTATION_JOURNAL_POLICY.json")
        self.assertEqual(policy["storage_branch"], "scheduler-evidence")
        storage = policy["storage_contract"]
        self.assertEqual(storage["canonical_policy_source_branch"], "main")
        self.assertEqual(storage["runtime_evidence_storage_branch"], "scheduler-evidence")
        self.assertTrue(storage["runtime_writes_to_main_prohibited_after_cutover"])
        self.assertTrue(storage["claim_creation_must_fail_if_path_exists"])
        self.assertTrue(storage["force_push_prohibited"])
        cutover = policy["cutover"]
        self.assertEqual(cutover["cutover_through_sequence"], 6)
        self.assertEqual(
            cutover["cutover_terminal_event_hash"],
            "fe719093f320feec38352fb49de18d3b9ebc7bed9c6e6bfa52b9f2b0b93cded6",
        )
        self.assertTrue(cutover["sequences_7_and_later_must_exist_only_on_scheduler_evidence_runtime_path"])

    def test_degraded_frontend_receipts_write_to_evidence_branch(self):
        policy = self.load("governance/SCHEDULER_FRONTEND_RECEIPT_POLICY.json")
        transport = policy["transport"]
        self.assertEqual(transport["github_storage_branch"], "scheduler-evidence")
        self.assertTrue(transport["runtime_github_write_to_main_prohibited"])
        self.assertTrue(transport["backend_scan_must_read_scheduler_evidence_branch"])
        self.assertEqual(transport["github_operation"], "CREATE_NEW_FILE_ONLY")
        self.assertTrue(policy["authority"]["evidence_branch_write_authority_is_not_main_branch_write_authority"])

    def test_bootstrap_separates_policy_and_evidence_authority(self):
        bootstrap = self.load("bootstrap/INTERNAL_SCHEDULER_SERVICE.json")
        self.assertEqual(bootstrap["runtime_evidence_branch"], "scheduler-evidence")
        invariants = bootstrap["invariants"]
        self.assertTrue(invariants["canonical_policy_and_code_source_branch_is_main"])
        self.assertTrue(invariants["runtime_scheduler_evidence_writes_to_main_prohibited"])
        self.assertTrue(invariants["evidence_branch_write_authority_is_not_main_write_authority"])
        self.assertTrue(invariants["frontend_receipt_backend_ingestion_reads_runtime_evidence_branch"])
        self.assertTrue(invariants["scheduler_mutation_journal_live_source_is_scheduler_evidence_branch"])

    def test_independent_scheduler_fetches_and_uses_evidence_branch(self):
        workflow = (ROOT / ".github" / "workflows" / "internal-spawn-scheduler.yml").read_text(encoding="utf-8")
        self.assertIn("git fetch origin scheduler-evidence --depth=1", workflow)
        self.assertIn("scheduler-evidence-snapshot/governance/scheduler-mutation-journal-v3", workflow)
        self.assertIn("scheduler-evidence-snapshot/agentbus-backup/coordination-messages", workflow)
        self.assertNotIn("--receipt-dir agentbus-backup/coordination-messages", workflow)

    def test_main_ruleset_requires_no_scheduler_bypass(self):
        doc = (ROOT / "docs" / "GITHUB_MAIN_RULESET_REQUIRED.md").read_text(encoding="utf-8")
        self.assertIn("scheduler-evidence", doc)
        self.assertIn("Do not permit status-check bypass", doc)
        self.assertIn("runtime evidence", doc.lower())


if __name__ == "__main__":
    unittest.main()
