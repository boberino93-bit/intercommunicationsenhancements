import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InternalSchedulerBootstrapContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bootstrap = json.loads((ROOT / "AGENT_BOOTSTRAP.json").read_text())
        cls.entrypoint = json.loads((ROOT / "INTERNAL_SCHEDULER_ENTRYPOINT.json").read_text())
        cls.protocol = (ROOT / "protocols" / "bootstrap_internal_scheduler.md").read_text()

    def test_bootstrap_requires_internal_scheduler_service(self):
        service = self.bootstrap["internal_scheduler_service"]
        self.assertTrue(service["required_on_startup"])
        self.assertTrue(service["restore_durable_state_before_tick"])
        self.assertTrue(service["bootstrap_tick_required"])
        self.assertEqual(
            service["runtime"],
            "org_agent_mesh.internal_scheduler.BootstrapInternalScheduler",
        )

    def test_spawn_ticket_never_claims_session_started(self):
        service = self.bootstrap["internal_scheduler_service"]
        self.assertFalse(service["spawn_ticket_is_session_started"])
        self.assertTrue(service["host_spawn_adapter_required_for_real_execution"])
        self.assertEqual(service["host_adapter_absent_state"], "HOST_SPAWN_ADAPTER_REQUIRED")
        self.assertFalse(service["schedule_fire_is_authority"])
        self.assertFalse(service["ticket_is_authority"])

    def test_primary_and_full_swarm_boundaries_remain_intact(self):
        service = self.bootstrap["internal_scheduler_service"]
        self.assertEqual(service["primary_creation"], "PROHIBITED")
        self.assertEqual(service["full_swarm_creation"], "HUMAN_ONLY")
        self.assertEqual(service["autonomous_disabled_to_enabled_transition"], "DENY")

    def test_entrypoint_matches_bootstrap_contract(self):
        self.assertEqual(
            self.entrypoint["service"]["runtime"],
            self.bootstrap["internal_scheduler_service"]["runtime"],
        )
        self.assertFalse(self.entrypoint["spawn_semantics"]["spawn_ticket_is_session_started"])
        self.assertTrue(
            self.entrypoint["spawn_semantics"]["host_spawn_adapter_required_for_real_execution"]
        )

    def test_protocol_states_truth_boundary(self):
        self.assertIn("SPAWN_TICKET_ISSUED", self.protocol)
        self.assertIn("SESSION_STARTED", self.protocol)
        self.assertIn("HOST_SPAWN_ADAPTER_REQUIRED", self.protocol)
        self.assertIn("PRIMARY", self.protocol)
        self.assertIn("COALESCE_TO_LATEST", self.protocol)


if __name__ == "__main__":
    unittest.main()
