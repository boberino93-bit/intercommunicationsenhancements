from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SchedulerEcosystemRolloutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.routes = json.loads((ROOT / "PROJECT_ROLE_ROUTING_REGISTRY.json").read_text())
        cls.bindings = json.loads((ROOT / "governance" / "INTERNAL_SPAWN_PROJECT_BINDINGS.json").read_text())
        cls.policy = json.loads((ROOT / "governance" / "INTERNAL_SPAWN_SCHEDULER_POLICY.json").read_text())
        cls.kit = json.loads((ROOT / "NEW_PROJECT_BOOTSTRAP.json").read_text())

    def test_every_registered_project_has_scheduler_binding(self):
        self.assertEqual(set(self.routes["projects"]), set(self.bindings["projects"]))
        for project_id, route in self.routes["projects"].items():
            binding = self.bindings["projects"][project_id]
            self.assertEqual(route["repository"], binding["repository"])
            self.assertEqual(route["repository_id"], binding["repository_id"])
            self.assertEqual(binding["binding_path"], "INTERNAL_SCHEDULER_SERVICE_BINDING.json")

    def test_spawn_scope_is_subordinate_only(self):
        authority = self.policy["delegated_spawn_authority"]
        self.assertEqual(authority["allowed_roles"], ["research", "manager"])
        self.assertFalse(authority["primary_allowed"])
        self.assertFalse(authority["master_allowed"])
        self.assertFalse(authority["full_swarm_auto_start_allowed"])
        self.assertTrue(authority["spawn_authority_is_not_mutation_authority"])

    def test_schedule_task_state_remains_separate_human_gate(self):
        boundary = self.policy["scheduler_state_boundary"]
        self.assertFalse(boundary["may_enable_existing_chatgpt_scheduled_tasks"])
        self.assertFalse(boundary["may_reenable_disabled_chatgpt_scheduled_tasks"])
        self.assertFalse(boundary["may_disable_existing_chatgpt_scheduled_tasks"])
        self.assertFalse(boundary["may_reschedule_existing_chatgpt_scheduled_tasks"])
        self.assertTrue(boundary["disabled_task_remains_human_control_gate"])

    def test_new_project_factory_materializes_scheduler_files(self):
        outputs = {item["output"] for item in self.kit["required_documents"]}
        self.assertIn("INTERNAL_SCHEDULER_SERVICE_BINDING.json", outputs)
        self.assertIn("bootstrap/INTERNAL_SCHEDULER_SERVICE.json", outputs)
        self.assertTrue(self.kit["startup_rules"]["internal_scheduler_service_binding_required"])
        self.assertTrue(self.kit["startup_rules"]["spawn_authority_is_not_mutation_authority"])

    def test_project_discovery_requires_local_scheduler_binding(self):
        text = (ROOT / "bootstrap" / "PROJECT_ROLE_DISCOVERY.md").read_text()
        self.assertIn("INTERNAL_SPAWN_PROJECT_BINDINGS.json", text)
        self.assertIn("INTERNAL_SCHEDULER_SERVICE_BINDING.json", text)
        self.assertIn("SCHEDULER_PROJECT_BINDING_BLOCKED", text)


if __name__ == "__main__":
    unittest.main()
