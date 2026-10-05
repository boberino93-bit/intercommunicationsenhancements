from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ProjectWorkControlTests(unittest.TestCase):
    def test_registry_starts_active_and_is_hold_aware(self):
        control = json.loads((ROOT / "governance" / "PROJECT_WORK_CONTROL.json").read_text())
        self.assertEqual(control["status"], "ACTIVE_CONTROL_PLANE")
        self.assertFalse(control["rules"]["hold_is_cancellation"])
        self.assertFalse(control["rules"]["hold_is_failure"])
        self.assertTrue(control["rules"]["active_agents_checkpoint_then_stop_project_work"])
        self.assertTrue(control["rules"]["scheduled_tasks_must_check_before_project_selection"])
        self.assertTrue(control["rules"]["global_agents_may_continue_other_unheld_projects"])
        self.assertEqual(control["rules"]["expired_manual_hold_state"], "HOLD_EXPIRED_PENDING_HUMAN_RESUME")
        for project in control["projects"].values():
            self.assertEqual(project["state"], "ACTIVE")
            self.assertIsNone(project["active_hold"])

    def test_event_schema_supports_hold_extend_resume(self):
        schema = json.loads((ROOT / "schemas" / "project_work_control_event.schema.json").read_text())
        actions = set(schema["properties"]["action"]["enum"])
        self.assertEqual(actions, {"HOLD", "EXTEND_HOLD", "RESUME"})
        self.assertIn("authentication_ref", schema["required"])
        self.assertIn("authorization_case_id", schema["required"])
        self.assertEqual(schema["properties"]["preserve_partial_state"]["const"], True)

    def test_live_and_future_bootstraps_load_work_control(self):
        live = json.loads((ROOT / "AGENT_BOOTSTRAP.json").read_text())
        template = json.loads((ROOT / "templates" / "new-project" / "AGENT_BOOTSTRAP.template.json").read_text())
        for bootstrap in (live, template):
            work = bootstrap["project_work_control"]
            self.assertTrue(work["required_on_startup"])
            self.assertTrue(work["required_between_bounded_units"])
            self.assertFalse(work["hold_is_cancellation"])
            self.assertTrue(work["hold_blocks_bound_project_work"])
            self.assertTrue(bootstrap["rules"]["resume_interrupted_assignment_automatically"])
            self.assertTrue(bootstrap["rules"]["pending_human_response_blocks_only_dependent_branch"])

    def test_protocol_requires_checkpoint_then_stop(self):
        text = (ROOT / "protocols" / "project_work_holds.md").read_text()
        self.assertIn("HOLD is **not** cancellation", text)
        self.assertIn("checkpoint", text.lower())
        self.assertIn("PROJECT_HOLD_ACTIVE", text)
        self.assertIn("AUTO_AT_EXPIRY", text)

    def test_authorization_package_never_replaces_single_use_gate(self):
        core = json.loads((ROOT / "governance" / "MUTATION_AUTHORIZATION_POLICY.json").read_text())
        package = json.loads((ROOT / "governance" / "AUTHORIZATION_PACKAGE_POLICY.json").read_text())
        self.assertEqual(core["valid_authorization_sources"], ["CURRENT_HUMAN_SINGLE_USE_AUTHORIZATION_CASE"])
        self.assertTrue(core["authorization_case"]["single_use"])
        self.assertTrue(package["package_requirements"]["child_single_use"])
        self.assertEqual(package["forbidden"][0], "OPEN_ENDED_FUTURE_WRITES")
        self.assertIn("ADDING_NEW_CHILDREN_AFTER_HUMAN_APPROVAL", package["forbidden"])


if __name__ == "__main__":
    unittest.main()
