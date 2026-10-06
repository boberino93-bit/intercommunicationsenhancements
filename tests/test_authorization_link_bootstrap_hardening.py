from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]

def load(path):
    return json.loads((ROOT / path).read_text())

class AuthorizationLinkBootstrapHardeningTests(unittest.TestCase):
    def test_canonical_bootstrap_gate_precedes_authorization(self):
        order = load("BOOTSTRAP_ORDER.json")
        self.assertEqual(order["schema"], "org-agent-mesh/bootstrap-order/v7")
        self.assertTrue(order["actionable_link_delivery_contract"]["required_before_authorization_evaluation"])
        steps = {s["id"]: s for s in order["steps"]}
        link = steps["prepare_and_surface_case_specific_authorization_link"]
        auth = steps["evaluate_current_mutation_authorization_envelope"]
        self.assertLess(link["order"], auth["order"])
        self.assertEqual(link["required_state"], "PRE_MUTATION_AUTHORIZATION_REQUIRED")
        self.assertEqual(link["verification_unavailable_behavior"], "SURFACE_SAFE_UNVERIFIED_DIRECT_WITH_DISCLOSURE")
        self.assertEqual(link["secret_or_bearer_material_in_url"], "DENY")
        self.assertFalse(link["link_open_or_render_is_authorization"])

    def test_policy_forbids_secret_urls_but_does_not_suppress_safe_link(self):
        link_policy = load("governance/ACTIONABLE_LINK_DELIVERY_POLICY.json")
        self.assertEqual(link_policy["status"], "ACTIVE_HARD_GATE")
        self.assertFalse(link_policy["security"]["security_tokens_in_url_allowed"])
        self.assertFalse(link_policy["security"]["credentials_in_url_allowed"])
        contract = link_policy["authorization_link_contract"]
        self.assertTrue(contract["required_before_waiting_for_human_authorization"])
        self.assertEqual(contract["unverified_safe_direct_behavior"], "SURFACE_WITH_EXPLICIT_UNVERIFIED_DIRECT_DISCLOSURE")
        self.assertFalse(contract["raw_connector_write_capability_is_authority"])

        mutation = load("governance/MUTATION_AUTHORIZATION_POLICY.json")
        self.assertEqual(mutation["pre_mutation_state"], "PRE_MUTATION_AUTHORIZATION_REQUIRED")
        self.assertTrue(mutation["authorization_case"]["prefilled_actionable_link_required_when_supported"])
        self.assertTrue(mutation["fail_closed"]["verification_unavailable_must_not_suppress_safe_direct_link"])
        self.assertFalse(mutation["raw_connector_write_capability_is_authority"])

    def test_local_and_seeded_bootstraps_inherit_gate(self):
        for path in ("AGENT_BOOTSTRAP.json", "templates/new-project/AGENT_BOOTSTRAP.template.json"):
            data = load(path)
            link = data["actionable_link_delivery"]
            self.assertTrue(link["required_before_waiting_for_human_authorization"])
            self.assertTrue(link["prefilled_case_link_required_when_supported"])
            self.assertFalse(link["secret_tokens_in_url"])
            self.assertFalse(link["raw_connector_write_capability_is_authority"])
            self.assertEqual(link["pre_mutation_state"], "PRE_MUTATION_AUTHORIZATION_REQUIRED")

        seeded_order = load("templates/new-project/BOOTSTRAP_ORDER.template.json")
        self.assertEqual(seeded_order["schema"], "org-agent-mesh/bootstrap-order/v5")
        self.assertIn("case-specific actionable authorization link surfaced when supported", seeded_order["mutation_gate"])
        self.assertIn("raw connector write capability is not authority", seeded_order["mutation_gate"])

    def test_protocols_state_non_suppressive_link_gate(self):
        actionable = (ROOT / "protocols/actionable_link_delivery.md").read_text()
        mutation = (ROOT / "protocols/mutation_authorization.md").read_text()
        self.assertIn("Verification uncertainty alone MUST NOT suppress", actionable)
        self.assertIn("Raw connector/tool write capability is not mutation authority", actionable)
        self.assertIn("PRE_MUTATION_AUTHORIZATION_REQUIRED BEFORE ANY DURABLE WRITE", mutation)
        self.assertIn("Raw connector or tool write capability is not authority", mutation)

if __name__ == "__main__":
    unittest.main()
