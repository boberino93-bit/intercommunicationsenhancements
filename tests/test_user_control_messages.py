from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class UserControlMessageContractTests(unittest.TestCase):
    def test_protocol_declares_control_message_not_cancellation_and_auto_resume(self):
        text = (ROOT / "protocols" / "user_control_messages.md").read_text(encoding="utf-8")
        self.assertIn("A USER CONTROL MESSAGE IS NOT A CANCELLATION", text)
        self.assertIn("answer the control message immediately", text)
        self.assertIn("resume the interrupted work automatically", text)
        self.assertIn("A control-message response is not task completion", text)

    def test_live_bootstrap_requires_preserve_and_resume(self):
        bootstrap = json.loads((ROOT / "AGENT_BOOTSTRAP.json").read_text(encoding="utf-8"))
        control = bootstrap["user_control_messages"]
        self.assertFalse(control["status_request_is_cancellation"])
        self.assertTrue(control["immediate_status_response"])
        self.assertTrue(control["preserve_active_assignment"])
        self.assertTrue(control["automatic_resume_after_control_message"])
        self.assertEqual(control["routine_continue_reprompt"], "DENY")
        self.assertTrue(bootstrap["rules"]["user_control_message_is_not_cancellation"])
        self.assertTrue(bootstrap["rules"]["respond_to_control_message_before_resuming"])
        self.assertTrue(bootstrap["rules"]["resume_interrupted_assignment_automatically"])

    def test_new_project_template_inherits_same_contract(self):
        template = json.loads((ROOT / "templates" / "new-project" / "AGENT_BOOTSTRAP.template.json").read_text(encoding="utf-8"))
        control = template["user_control_messages"]
        self.assertFalse(control["status_request_is_cancellation"])
        self.assertTrue(control["immediate_status_response"])
        self.assertTrue(control["preserve_active_assignment"])
        self.assertTrue(control["automatic_resume_after_control_message"])
        self.assertEqual(control["protocol_path"], "protocols/user_control_messages.md")

    def test_global_machine_entrypoint_requires_control_message_resume(self):
        entrypoint = json.loads((ROOT / "GLOBAL_AGENT_ENTRYPOINT.json").read_text(encoding="utf-8"))
        self.assertEqual(entrypoint["rendezvous"]["user_control_message_protocol"], "protocols/user_control_messages.md")
        control = entrypoint["control_message_policy"]
        self.assertFalse(control["status_progress_or_explanation_request_is_task_completion"])
        self.assertTrue(control["respond_before_resuming"])
        self.assertTrue(control["preserve_active_assignment"])
        self.assertTrue(control["automatic_resume"])
        self.assertFalse(control["require_continue_reprompt"])
        self.assertIn("when_user_control_message_arrives_respond_then_resume_active_assignment", entrypoint["sequence"])

    def test_autonomous_continuation_and_universal_entrypoint_reference_protocol(self):
        continuation = (ROOT / "protocols" / "autonomous_continuation.md").read_text(encoding="utf-8")
        entrypoint = (ROOT / "UNIVERSAL_AGENT_ENTRYPOINT.md").read_text(encoding="utf-8")
        self.assertIn("protocols/user_control_messages.md", continuation)
        self.assertIn("protocols/user_control_messages.md", entrypoint)
        self.assertIn("resume the exact interrupted work automatically", entrypoint)

    def test_role_packages_include_control_message_protocol_by_shared_pattern(self):
        deps = json.loads((ROOT / "packaging" / "agent_package_dependencies.json").read_text(encoding="utf-8"))
        self.assertIn("protocols/*.md", deps["shared_patterns"])
        self.assertTrue((ROOT / "protocols" / "user_control_messages.md").is_file())


if __name__ == "__main__":
    unittest.main()
