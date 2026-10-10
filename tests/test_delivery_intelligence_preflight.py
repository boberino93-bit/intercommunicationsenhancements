from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DeliveryIntelligencePreflightTests(unittest.TestCase):
    def test_policy_exists_and_preserves_authority(self):
        policy = json.loads((ROOT / "governance/DELIVERY_INTELLIGENCE_PREFLIGHT_POLICY.json").read_text())
        self.assertEqual(policy["policy_id"], "IEP-DIP-001")
        self.assertFalse(policy["authority"]["authority_conveyed"])
        self.assertFalse(policy["authority"]["may_expand_scope"])
        self.assertFalse(policy["authority"]["may_bypass_authorization"])
        self.assertTrue(policy["context_assimilation"]["required_when_relevant_and_available"])
        self.assertEqual(
            set(policy["required_disciplines"]),
            {"BUSINESS_ANALYSIS", "IMPLEMENTATION_CONSULTING", "PROJECT_MANAGEMENT"},
        )

    def test_protocol_contains_all_delivery_dimensions(self):
        text = (ROOT / "protocols/delivery_intelligence_preflight.md").read_text()
        for required in (
            "Business Analysis",
            "Implementation Consulting",
            "Project Management",
            "CAPABILITY != AUTHORITY",
            "MUTATION_LANE_BLOCKED_CONTINUING_SAFE_WORK",
            "minority findings",
            "acceptance criteria",
            "critical path",
            "reversibility",
        ):
            self.assertIn(required, text)

    def test_all_core_role_bootstraps_load_preflight(self):
        for path in ("bootstrap/RESEARCH.md", "bootstrap/MANAGER.md", "bootstrap/PRIMARY.md"):
            text = (ROOT / path).read_text()
            self.assertIn("protocols/delivery_intelligence_preflight.md", text, path)
            self.assertIn("governance/DELIVERY_INTELLIGENCE_PREFLIGHT_POLICY.json", text, path)
            self.assertIn("grants zero authority", text.lower(), path)

    def test_master_consumes_portfolio_preflight(self):
        text = (ROOT / "research_swarm/prompts/master.md").read_text()
        self.assertIn("Delivery Intelligence Preflight", text)
        self.assertIn("portfolio", text.lower())
        self.assertIn("zero project-local", text)


if __name__ == "__main__":
    unittest.main()
