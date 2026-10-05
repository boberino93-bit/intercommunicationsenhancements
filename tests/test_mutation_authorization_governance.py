import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str):
    return json.loads((ROOT / path).read_text())


class MutationAuthorizationGovernanceTests(unittest.TestCase):
    def test_mutation_policy_is_hard_gate(self):
        policy = load_json("governance/MUTATION_AUTHORIZATION_POLICY.json")
        self.assertEqual(policy["status"], "ACTIVE_HARD_GATE")
        self.assertEqual(policy["invariant"], "INTENT_IS_NOT_AUTHORIZATION")
        self.assertTrue(policy["authorization_record_required_before_each_mutation"])
        self.assertEqual(policy["interactive_explicit_test"]["material_ambiguity_result"], "AUTHORIZATION_UNRESOLVED")
        self.assertEqual(policy["interactive_explicit_test"]["unresolved_write_behavior"], "DENY")
        self.assertFalse(policy["role_is_mutation_authority"])
        self.assertFalse(policy["claim_or_lease_is_mutation_authority"])
        self.assertFalse(policy["scheduled_work"]["schedule_fire_is_authorization"])

    def test_inferred_intent_and_capability_questions_are_not_authority(self):
        policy = load_json("governance/MUTATION_AUTHORIZATION_POLICY.json")
        invalid = set(policy["invalid_authorization_sources"])
        for source in (
            "INFERRED_INTENT",
            "CAPABILITY_QUESTION",
            "DESIGN_DISCUSSION",
            "ENTHUSIASM_OR_PRAISE",
            "ROLE_OR_SENIORITY",
            "REPOSITORY_PERMISSION",
            "PRIOR_UNRELATED_AUTHORIZATION",
        ):
            self.assertIn(source, invalid)

    def test_valid_authorization_sources_are_bounded(self):
        policy = load_json("governance/MUTATION_AUTHORIZATION_POLICY.json")
        self.assertEqual(
            set(policy["valid_authorization_sources"]),
            {
                "CURRENT_HUMAN_EXPLICIT",
                "ACTIVE_HUMAN_APPROVED_TASK_CONTRACT",
                "DELEGATED_WITHIN_APPROVED_SCOPE",
            },
        )
        self.assertFalse(policy["delegation"]["may_expand_human_approved_mutation_envelope"])

    def test_roleless_admission_does_not_self_promote_primary(self):
        policy = load_json("governance/ROLELESS_AGENT_ADMISSION_POLICY.json")
        role = policy["role_selection"]
        self.assertTrue(role["demand_driven"])
        self.assertFalse(role["fixed_global_ratios"])
        self.assertFalse(role["primary_self_promotion"])
        self.assertFalse(role["master_self_selection"])
        self.assertFalse(policy["role_plus_claim_grants_mutation_authority"])
        self.assertFalse(policy["minimal_human_launch"]["generic_start_instruction_alone_authorizes_external_mutation"])

    def test_global_entrypoint_routes_generic_agent_to_roleless_admission(self):
        entry = load_json("GLOBAL_AGENT_ENTRYPOINT.json")
        self.assertEqual(entry["version"], "1.6.0")
        self.assertEqual(entry["mutation_authorization_policy"]["invariant"], "INTENT_IS_NOT_AUTHORIZATION")
        self.assertFalse(entry["mutation_authorization_policy"]["capability_question_is_authorization"])
        self.assertEqual(
            entry["role_policy"]["human_launched_generic_project_agent_without_role"],
            "ROLELESS_DEMAND_DRIVEN_ADMISSION",
        )
        self.assertEqual(entry["role_policy"]["generic_agent_primary_self_promotion"], "DENY")
        self.assertIn("proposed_external_side_effect_has_valid_mutation_authorization_source", entry["mutation_gate"])

    def test_local_bootstrap_separates_role_claim_and_mutation_authority(self):
        bootstrap = load_json("AGENT_BOOTSTRAP.json")
        self.assertTrue(bootstrap["mutation_authorization"]["required_before_every_external_mutation"])
        self.assertEqual(bootstrap["mutation_authorization"]["invariant"], "INTENT_IS_NOT_AUTHORIZATION")
        self.assertFalse(bootstrap["roleless_agent_admission"]["primary_self_promotion"])
        self.assertFalse(bootstrap["roleless_agent_admission"]["role_or_claim_grants_mutation_authority"])
        self.assertFalse(bootstrap["rules"]["generic_human_launch_without_role_defaults_to_primary"])
        self.assertTrue(bootstrap["rules"]["ambiguous_mutation_authorization_fails_closed"])

    def test_bootstrap_order_has_authorization_gate_before_mutation(self):
        order = load_json("BOOTSTRAP_ORDER.json")
        self.assertEqual(order["schema"], "org-agent-mesh/bootstrap-order/v5")
        steps = {step["id"]: step for step in order["steps"]}
        auth_step = steps["evaluate_current_mutation_authorization_envelope"]
        self.assertFalse(auth_step["mutation_allowed"])
        self.assertTrue(auth_step["result_required_before_any_external_side_effect"])
        execute = steps["execute_task_with_autonomous_continuation_and_per_mutation_scope_validation"]
        self.assertIn("mutation_authorization_validation_before_each_external_side_effect", execute["additional_guards"])
        self.assertIn("stronger_exact_action_authorization_when_applicable", execute["additional_guards"])

    def test_supervisory_policy_cannot_turn_role_into_write_authority(self):
        policy = load_json("governance/SWARM_SUPERVISION_POLICY.json")
        self.assertFalse(policy["mutation_authorization"]["supervisory_role_grants_mutation_authority"])
        self.assertFalse(policy["mutation_authorization"]["claim_or_lease_grants_mutation_authority"])
        self.assertFalse(policy["roleless_agent_admission"]["generic_agent_defaults_to_primary"])
        self.assertFalse(policy["roleless_agent_admission"]["primary_self_promotion"])
        self.assertTrue(policy["runtime"]["authorization_check_before_each_external_side_effect"])

    def test_protocol_contains_near_miss_regression_examples(self):
        text = (ROOT / "protocols" / "mutation_authorization.md").read_text()
        self.assertIn("Can you harden this?", text)
        self.assertIn("do **not** by themselves authorize mutation", text)
        self.assertIn("Implement this fix and commit it.", text)


if __name__ == "__main__":
    unittest.main()
