import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str):
    return json.loads((ROOT / path).read_text())


class MutationAuthorizationGovernanceTests(unittest.TestCase):
    def test_mutation_policy_is_hard_gate_and_single_use(self):
        policy = load_json("governance/MUTATION_AUTHORIZATION_POLICY.json")
        self.assertEqual(policy["status"], "ACTIVE_HARD_GATE")
        self.assertEqual(policy["invariant"], "INTENT_IS_NOT_AUTHORIZATION")
        self.assertTrue(policy["principal_claim_required"])
        self.assertTrue(policy["authorization_record_required_before_each_mutation_case"])
        self.assertTrue(policy["authorization_case"]["single_use"])
        self.assertFalse(policy["authorization_case"]["session_persistence"])
        self.assertFalse(policy["authorization_case"]["conversation_persistence"])
        self.assertFalse(policy["role_is_mutation_authority"])
        self.assertFalse(policy["claim_or_lease_is_mutation_authority"])
        self.assertFalse(policy["authentication_is_mutation_authority"])
        self.assertFalse(policy["scheduled_work"]["schedule_fire_is_authorization"])

    def test_prior_permission_and_task_contract_are_not_authority(self):
        policy = load_json("governance/MUTATION_AUTHORIZATION_POLICY.json")
        invalid = set(policy["invalid_authorization_sources"])
        for source in (
            "INFERRED_INTENT",
            "CAPABILITY_QUESTION",
            "DESIGN_DISCUSSION",
            "ENTHUSIASM_OR_PRAISE",
            "ROLE_OR_SENIORITY",
            "REPOSITORY_PERMISSION",
            "PRIOR_AUTHORIZATION",
            "PRIOR_AUTHENTICATION",
            "ACTIVE_TASK_CONTRACT_ALONE",
            "SCHEDULE_FIRE",
            "PARENT_AGENT_DELEGATION_ALONE",
            "SESSION_CONTEXT",
            "CONVERSATION_CONTINUITY",
        ):
            self.assertIn(source, invalid)

    def test_only_current_single_use_human_case_is_standalone_authority(self):
        policy = load_json("governance/MUTATION_AUTHORIZATION_POLICY.json")
        self.assertEqual(policy["valid_authorization_sources"], ["CURRENT_HUMAN_SINGLE_USE_AUTHORIZATION_CASE"])
        self.assertFalse(policy["delegation"]["may_create_new_human_authorization"])
        self.assertFalse(policy["delegation"]["may_expand_case_scope"])
        self.assertTrue(policy["scheduled_work"]["each_distinct_mutation_case_requires_fresh_human_authorization"])

    def test_roleless_admission_does_not_self_promote_primary(self):
        policy = load_json("governance/ROLELESS_AGENT_ADMISSION_POLICY.json")
        role = policy["role_selection"]
        self.assertTrue(role["demand_driven"])
        self.assertFalse(role["fixed_global_ratios"])
        self.assertFalse(role["primary_self_promotion"])
        self.assertFalse(role["master_self_selection"])
        self.assertFalse(policy["role_plus_claim_grants_mutation_authority"])

    def test_global_entrypoint_routes_generic_agent_to_roleless_admission(self):
        entry = load_json("GLOBAL_AGENT_ENTRYPOINT.json")
        self.assertEqual(entry["mutation_authorization_policy"]["invariant"], "INTENT_IS_NOT_AUTHORIZATION")
        self.assertEqual(
            entry["role_policy"]["human_launched_generic_project_agent_without_role"],
            "ROLELESS_DEMAND_DRIVEN_ADMISSION",
        )
        self.assertEqual(entry["role_policy"]["generic_agent_primary_self_promotion"], "DENY")

    def test_local_bootstrap_separates_role_claim_and_mutation_authority(self):
        bootstrap = load_json("AGENT_BOOTSTRAP.json")
        self.assertTrue(bootstrap["mutation_authorization"]["required_before_every_external_mutation"])
        self.assertEqual(bootstrap["mutation_authorization"]["invariant"], "INTENT_IS_NOT_AUTHORIZATION")
        self.assertFalse(bootstrap["roleless_agent_admission"]["primary_self_promotion"])
        self.assertFalse(bootstrap["roleless_agent_admission"]["role_or_claim_grants_mutation_authority"])

    def test_bootstrap_order_has_authorization_gate_before_mutation(self):
        order = load_json("BOOTSTRAP_ORDER.json")
        steps = {step["id"]: step for step in order["steps"]}
        auth_step = steps["evaluate_current_mutation_authorization_envelope"]
        self.assertFalse(auth_step["mutation_allowed"])
        self.assertTrue(auth_step["result_required_before_any_external_side_effect"])

    def test_protocol_forbids_ambient_authorization(self):
        text = (ROOT / "protocols" / "mutation_authorization.md").read_text()
        self.assertIn("There is no session-wide", text)
        self.assertIn("even one issued seconds earlier", text)
        self.assertIn("Every distinct mutation case requires its own case ID", text)


if __name__ == "__main__":
    unittest.main()
