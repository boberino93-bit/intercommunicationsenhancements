from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text())


class GovernedProposalArtifactsTests(unittest.TestCase):
    def test_bootstrap_loads_governed_proposal_artifacts(self):
        bootstrap = load("AGENT_BOOTSTRAP.json")
        contract = bootstrap["governed_proposal_artifacts"]
        self.assertEqual(contract["protocol_path"], "protocols/governed_proposal_artifacts.md")
        self.assertEqual(contract["canonical_candidate_surface"], "swarm-governance/recommendations/")
        self.assertTrue(contract["substantial_executable_prompts_are_durable_project_artifacts"])
        self.assertTrue(contract["primary_discovers_pending_artifacts_on_bootstrap"])
        self.assertTrue(contract["primary_execution_required_for_protected_or_global_mutations"])
        self.assertEqual(contract["universal_swarm_change_project"], "intercommunicationsenhancements")
        self.assertFalse(contract["storage_is_acceptance"])
        self.assertFalse(contract["retrieval_is_authorization"])

    def test_bootstrap_loads_forensic_validation(self):
        bootstrap = load("AGENT_BOOTSTRAP.json")
        contract = bootstrap["forensic_orchestration_validation"]
        self.assertEqual(contract["protocol_path"], "protocols/forensic_orchestration_validation.md")
        self.assertTrue(contract["required_on_startup"])
        self.assertTrue(contract["architecture_itself_is_testable"])
        self.assertTrue(contract["smallest_effective_swarm"])
        self.assertTrue(contract["contradiction_is_system_resource"])
        self.assertTrue(contract["limitations_must_remain_visible"])
        self.assertTrue(contract["scheduled_task_exists_is_not_execution_evidence"])

    def test_existing_authorization_hard_gates_are_preserved(self):
        bootstrap = load("AGENT_BOOTSTRAP.json")
        self.assertEqual(bootstrap["mutation_authorization"]["invariant"], "INTENT_IS_NOT_AUTHORIZATION")
        self.assertTrue(bootstrap["mutation_authorization"]["single_use_case_required"])
        self.assertTrue(bootstrap["authority_authentication"]["high_consequence_independent_external_proof_required"])
        self.assertFalse(bootstrap["authority_authentication"]["agent_may_answer_its_own_challenge"])
        self.assertTrue(bootstrap["rules"]["mutation_authorization_required_before_every_external_side_effect"])
        self.assertTrue(bootstrap["rules"]["role_selection_does_not_grant_mutation_authority"])

    def test_canonical_protocols_are_active(self):
        forensic = (ROOT / "protocols/forensic_orchestration_validation.md").read_text()
        routing = (ROOT / "protocols/governed_proposal_artifacts.md").read_text()
        self.assertIn("status: ACTIVE_CANONICAL", forensic)
        self.assertIn("More agents do not equal more truth", forensic)
        self.assertIn("A scheduled task existing is not evidence that it executed", forensic)
        self.assertIn("status: ACTIVE_CANONICAL", routing)
        self.assertIn("Storage is not acceptance", routing)
        self.assertIn("Retrieval is not authorization", routing)


if __name__ == "__main__":
    unittest.main()
