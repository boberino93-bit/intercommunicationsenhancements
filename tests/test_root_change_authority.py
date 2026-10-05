import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "governance" / "ROOT_CHANGE_AUTHORITY.json"
CODEOWNERS = ROOT / ".github" / "CODEOWNERS"
GUARD = ROOT / ".github" / "workflows" / "root-authority-guard.yml"


class RootChangeAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads(AUTHORITY.read_text(encoding="utf-8"))

    def test_exactly_one_human_root_change_principal(self):
        principals = self.policy["human_root_change_principals"]
        self.assertTrue(self.policy["sole_human_change_authority"])
        self.assertEqual(len(principals), 1)
        self.assertEqual(principals[0]["name"], "Robert Leonard")
        self.assertEqual(principals[0]["github_login"], "boberino93-bit")

    def test_root_authority_cannot_be_created_by_agents_or_learning(self):
        invariants = self.policy["invariants"]
        self.assertFalse(invariants["agent_may_mint_root_authority"])
        self.assertFalse(invariants["learning_may_modify_root_authority"])
        self.assertFalse(invariants["confidence_or_consensus_may_create_authority"])
        self.assertTrue(invariants["root_change_requires_authenticated_human_principal"])

    def test_delegation_is_disabled(self):
        delegation = self.policy["delegation"]
        self.assertFalse(delegation["allowed"])
        self.assertFalse(delegation["automatic_delegation"])
        self.assertFalse(delegation["agent_delegation"])

    def test_repository_surfaces_bind_to_same_github_principal(self):
        codeowners = CODEOWNERS.read_text(encoding="utf-8")
        guard = GUARD.read_text(encoding="utf-8")
        self.assertIn("* @boberino93-bit", codeowners)
        self.assertIn("AUTHORIZED_ACTOR: boberino93-bit", guard)
        self.assertEqual(self.policy["repository_enforcement"]["authorized_github_actor"], "boberino93-bit")

    def test_github_preventive_enforcement_is_not_overclaimed(self):
        repo = self.policy["repository_enforcement"]
        self.assertTrue(repo["preventive_branch_rule_required"])
        self.assertFalse(repo["preventive_branch_rule_verified"])


if __name__ == "__main__":
    unittest.main()
