from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SwarmSynchronizationPolicyTests(unittest.TestCase):
    def test_bootstrap_requires_canonical_sync_contract(self):
        data = json.loads((ROOT / "AGENT_BOOTSTRAP.json").read_text())
        sync = data["swarm_synchronization"]
        self.assertEqual(sync["policy_id"], "IEP-SYNC-001")
        self.assertEqual(sync["protocol_path"], "protocols/swarm_synchronization.md")
        self.assertTrue(sync["required_on_startup"])
        self.assertTrue(sync["required_before_claim_or_retask"])
        self.assertTrue(sync["required_before_protected_mutation"])
        self.assertTrue(sync["heartbeat_is_sensor_only"])
        self.assertEqual(sync["ownership_authority"], "CLAIMS_LEASES_FENCING")
        self.assertTrue(data["rules"]["swarm_synchronization_required"])
        self.assertTrue(data["rules"]["heartbeat_is_sensor_not_ownership_authority"])

    def test_global_entrypoint_loads_sync_overlay(self):
        data = json.loads((ROOT / "GLOBAL_AGENT_ENTRYPOINT.json").read_text())
        self.assertEqual(
            data["rendezvous"]["swarm_synchronization_protocol"],
            "protocols/swarm_synchronization.md",
        )
        sync = data["swarm_synchronization_policy"]
        self.assertEqual(sync["policy_id"], "IEP-SYNC-001")
        self.assertTrue(sync["required_after_project_resolution"])
        self.assertTrue(sync["critical_path_focus_required"])
        self.assertTrue(sync["does_not_create_authority"])
        self.assertTrue(any("swarm_synchronization" in step for step in data["sequence"]))

    def test_stronger_existing_controls_remain(self):
        bootstrap = json.loads((ROOT / "AGENT_BOOTSTRAP.json").read_text())
        entry = json.loads((ROOT / "GLOBAL_AGENT_ENTRYPOINT.json").read_text())
        self.assertTrue(bootstrap["mutation_authorization"]["required_before_every_external_mutation"])
        self.assertTrue(bootstrap["authority_authentication"]["high_consequence_independent_external_proof_required"])
        self.assertTrue(bootstrap["scheduled_launch_contract"]["each_distinct_scheduled_mutation_case_requires_fresh_human_authorization"])
        self.assertTrue(bootstrap["governed_proposal_artifacts"]["primary_execution_required_for_protected_or_global_mutations"])
        self.assertTrue(bootstrap["forensic_orchestration_validation"]["architecture_itself_is_testable"])
        self.assertFalse(entry["scheduled_task_activation_policy"]["agents_may_enable"])
        self.assertEqual(entry["mutation_authorization_policy"]["invariant"], "INTENT_IS_NOT_AUTHORIZATION")

    def test_protocol_preserves_authority_separation_and_focus(self):
        text = (ROOT / "protocols" / "swarm_synchronization.md").read_text()
        for expected in (
            "heartbeat",
            "claims",
            "leases",
            "fencing",
            "critical path",
            "drift",
            "WIP",
            "does not create authority",
        ):
            self.assertIn(expected.lower(), text.lower())


if __name__ == "__main__":
    unittest.main()
