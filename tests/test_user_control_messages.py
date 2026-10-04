from pathlib import Path
import copy
import json
import unittest

from org_agent_mesh.user_control import (
    UserControlContractError,
    validate_global_entrypoint_control_policy,
    validate_local_control_message_contract,
    validate_registry_control_message_contract,
)

ROOT = Path(__file__).resolve().parents[1]


class UserControlMessageContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((ROOT / "PROJECT_ROLE_ROUTING_REGISTRY.json").read_text(encoding="utf-8"))
        cls.bootstrap = json.loads((ROOT / "AGENT_BOOTSTRAP.json").read_text(encoding="utf-8"))
        cls.entrypoint = json.loads((ROOT / "GLOBAL_AGENT_ENTRYPOINT.json").read_text(encoding="utf-8"))

    def test_protocol_declares_control_message_not_cancellation_and_auto_resume(self):
        text = (ROOT / "protocols" / "user_control_messages.md").read_text(encoding="utf-8")
        self.assertIn("A USER CONTROL MESSAGE IS NOT A CANCELLATION", text)
        self.assertIn("answer the control message immediately", text)
        self.assertIn("resume the interrupted work automatically", text)
        self.assertIn("A control-message response is not task completion", text)

    def test_live_bootstrap_requires_preserve_and_resume(self):
        control = self.bootstrap["user_control_messages"]
        self.assertFalse(control["status_request_is_cancellation"])
        self.assertTrue(control["immediate_status_response"])
        self.assertTrue(control["preserve_active_assignment"])
        self.assertTrue(control["automatic_resume_after_control_message"])
        self.assertEqual(control["routine_continue_reprompt"], "DENY")
        self.assertTrue(self.bootstrap["rules"]["user_control_message_is_not_cancellation"])
        self.assertTrue(self.bootstrap["rules"]["respond_to_control_message_before_resuming"])
        self.assertTrue(self.bootstrap["rules"]["resume_interrupted_assignment_automatically"])

    def test_new_project_template_inherits_same_contract(self):
        template = json.loads((ROOT / "templates" / "new-project" / "AGENT_BOOTSTRAP.template.json").read_text(encoding="utf-8"))
        control = template["user_control_messages"]
        self.assertFalse(control["status_request_is_cancellation"])
        self.assertTrue(control["immediate_status_response"])
        self.assertTrue(control["preserve_active_assignment"])
        self.assertTrue(control["automatic_resume_after_control_message"])
        self.assertEqual(control["protocol_path"], "protocols/user_control_messages.md")

    def test_global_machine_entrypoint_requires_control_message_resume(self):
        self.assertEqual(self.entrypoint["rendezvous"]["user_control_message_protocol"], "protocols/user_control_messages.md")
        control = self.entrypoint["control_message_policy"]
        self.assertFalse(control["status_progress_or_explanation_request_is_task_completion"])
        self.assertTrue(control["respond_before_resuming"])
        self.assertTrue(control["preserve_active_assignment"])
        self.assertTrue(control["automatic_resume"])
        self.assertFalse(control["require_continue_reprompt"])
        self.assertIn("when_user_control_message_arrives_respond_then_resume_active_assignment", self.entrypoint["sequence"])

    def test_runtime_validators_accept_current_contracts(self):
        validate_registry_control_message_contract(self.registry)
        validate_local_control_message_contract(self.bootstrap, registry=self.registry)
        validate_global_entrypoint_control_policy(self.entrypoint)

    def test_registry_cannot_disable_automatic_resume(self):
        registry = copy.deepcopy(self.registry)
        registry["user_control_messages"]["automatic_resume_after_control_message"] = False
        with self.assertRaisesRegex(UserControlContractError, "registry_automatic_resume_disabled"):
            validate_registry_control_message_contract(registry)

    def test_registry_cannot_treat_status_as_cancellation(self):
        registry = copy.deepcopy(self.registry)
        registry["user_control_messages"]["status_request_is_cancellation"] = True
        with self.assertRaisesRegex(UserControlContractError, "registry_status_request_treated_as_cancellation"):
            validate_registry_control_message_contract(registry)

    def test_local_contract_cannot_disable_immediate_status_response(self):
        bootstrap = copy.deepcopy(self.bootstrap)
        bootstrap["user_control_messages"]["immediate_status_response"] = False
        with self.assertRaisesRegex(UserControlContractError, "local_immediate_status_response_disabled"):
            validate_local_control_message_contract(bootstrap, registry=self.registry)

    def test_local_contract_requires_explicit_stop_override(self):
        bootstrap = copy.deepcopy(self.bootstrap)
        bootstrap["user_control_messages"]["explicit_stop_cancel_pause_or_redirect_overrides_resume"] = False
        with self.assertRaisesRegex(UserControlContractError, "local_explicit_stop_override_disabled"):
            validate_local_control_message_contract(bootstrap, registry=self.registry)

    def test_global_entrypoint_cannot_require_continue_reprompt(self):
        entrypoint = copy.deepcopy(self.entrypoint)
        entrypoint["control_message_policy"]["require_continue_reprompt"] = True
        with self.assertRaisesRegex(UserControlContractError, "unsafe_global_control_policy_require_continue_reprompt"):
            validate_global_entrypoint_control_policy(entrypoint)

    def test_autonomous_continuation_and_universal_entrypoint_reference_protocol(self):
        continuation = (ROOT / "protocols" / "autonomous_continuation.md").read_text(encoding="utf-8")
        entrypoint = (ROOT / "UNIVERSAL_AGENT_ENTRYPOINT.md").read_text(encoding="utf-8")
        self.assertIn("protocols/user_control_messages.md", continuation)
        self.assertIn("protocols/user_control_messages.md", entrypoint)
        self.assertIn("resume the exact interrupted work automatically", entrypoint)

    def test_role_packages_include_control_message_protocol_and_validator(self):
        deps = json.loads((ROOT / "packaging" / "agent_package_dependencies.json").read_text(encoding="utf-8"))
        self.assertIn("protocols/*.md", deps["shared_patterns"])
        self.assertIn("org_agent_mesh/*.py", deps["shared_patterns"])
        self.assertTrue((ROOT / "protocols" / "user_control_messages.md").is_file())
        self.assertTrue((ROOT / "org_agent_mesh" / "user_control.py").is_file())


if __name__ == "__main__":
    unittest.main()
