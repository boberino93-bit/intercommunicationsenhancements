from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text())


class ForensicReadOnlyPolicyTests(unittest.TestCase):
    def test_policy_is_perpetual_fail_closed_and_non_mutating(self):
        policy = load("governance/FORENSIC_READ_ONLY_POLICY.json")
        self.assertEqual(policy["policy_id"], "IE-FORENSICS-READ-ONLY-PERPETUAL")
        self.assertEqual(policy["status"], "ACTIVE_HARD_GATE")
        self.assertEqual(policy["duration"], "PERPETUAL")
        self.assertEqual(policy["default_mode"], "READ_ONLY_FAIL_CLOSED")
        self.assertFalse(policy["authority"]["forensic_investigation_grants_mutation_authority"])
        self.assertFalse(policy["authority"]["tool_write_capability_is_authority"])
        self.assertFalse(policy["authority"]["consensus_is_authorization"])
        self.assertFalse(policy["authority"]["native_model_memory_is_authoritative_governance"])
        self.assertTrue(policy["authority"]["durable_project_state_required_for_governance"])
        self.assertIn("REMEDIATION", policy["prohibited_operations"])
        self.assertIn("COMMIT", policy["prohibited_operations"])
        self.assertIn("RERUN_SWARM_OR_REPRODUCE_INCIDENT_WHERE_PROJECT_STATE_MAY_CHANGE", policy["prohibited_operations"])

    def test_unknown_tool_semantics_fail_closed(self):
        policy = load("governance/FORENSIC_READ_ONLY_POLICY.json")
        gate = policy["tool_dispatch"]
        self.assertTrue(gate["read_only_determination_required_before_every_invocation"])
        self.assertEqual(gate["unknown_mutation_semantics"], "DENY_AND_RECORD_LIMITATION")
        self.assertEqual(gate["ambiguous_mutation_semantics"], "DENY_AND_RECORD_LIMITATION")
        self.assertEqual(gate["suspected_side_effect"], "DENY_AND_RECORD_LIMITATION")
        self.assertFalse(gate["fallback_to_alternative_mutating_tool"])

    def test_forensics_and_remediation_are_separate_modes(self):
        policy = load("governance/FORENSIC_READ_ONLY_POLICY.json")
        separation = policy["remediation_separation"]
        self.assertFalse(separation["forensic_mode_may_apply_remediation"])
        self.assertTrue(separation["forensic_findings_may_recommend_remediation"])
        self.assertTrue(separation["remediation_requires_distinct_operational_mode"])
        self.assertTrue(separation["remediation_requires_separate_explicit_authority"])
        self.assertFalse(separation["implicit_mode_switch"])
        self.assertTrue(separation["finding_active_security_issue_does_not_self_authorize_containment"])

    def test_children_inherit_read_only_and_memory_is_non_authoritative(self):
        policy = load("governance/FORENSIC_READ_ONLY_POLICY.json")
        delegation = policy["delegation"]
        self.assertTrue(delegation["children_inherit_read_only"])
        self.assertFalse(delegation["delegation_may_expand_mutation_authority"])
        self.assertFalse(delegation["parent_may_grant_forensic_child_mutation_authority"])

        memory = policy["persistence_and_memory"]
        self.assertTrue(memory["conversation_memory_is_convenience_only"])
        self.assertFalse(memory["conversation_memory_may_override_policy"])
        self.assertFalse(memory["conversation_memory_may_substitute_for_policy"])

    def test_existing_bootstrap_requires_forensic_protocol(self):
        bootstrap = load("AGENT_BOOTSTRAP.json")
        forensic = bootstrap["forensic_orchestration_validation"]
        self.assertTrue(forensic["required_on_startup"])
        self.assertEqual(forensic["protocol_path"], "protocols/forensic_orchestration_validation.md")

        protocol = (ROOT / "protocols/forensic_orchestration_validation.md").read_text()
        self.assertIn("protocols/forensic_read_only.md", protocol)
        self.assertIn("governance/FORENSIC_READ_ONLY_POLICY.json", protocol)
        self.assertIn("FORENSIC_INVESTIGATION and REMEDIATION are separate operational modes", protocol)
        self.assertIn("Model-native, conversational, or temporary memory is non-authoritative convenience only", protocol)

        read_only_protocol = (ROOT / "protocols/forensic_read_only.md").read_text()
        self.assertIn("Default outcome: READ ONLY", read_only_protocol)
        self.assertIn("Forensics observes. Forensics preserves. Forensics explains.", read_only_protocol)


if __name__ == "__main__":
    unittest.main()
