from pathlib import Path
import json
import unittest

from org_agent_mesh.swarm_memory_policy import (
    CANONICAL_AGENTBUS_BOARD,
    CANONICAL_ARTIFACTORY_BOARD,
    CANONICAL_GITHUB_REPOSITORY,
    ExternalPersistenceConflict,
    ExternalPersistenceUnavailable,
    MemoryPolicyViolation,
    PersistenceReceipt,
    assert_collective_persistence_source,
    assert_local_state_non_authoritative,
    classify_persistence_source,
    records_equivalent,
    resolve_authoritative_collective_state,
    validate_external_receipts,
)

ROOT = Path(__file__).resolve().parents[1]


class SwarmMemoryPolicyTests(unittest.TestCase):
    def test_native_chatgpt_memory_aliases_are_hard_denied(self):
        for source in ("native_chatgpt_memory", "chatgpt_memory", "saved_memory", "memory_recall", "chatgpt_memory_recall", "host_memory"):
            with self.subTest(source=source):
                self.assertEqual(classify_persistence_source(source), "NATIVE_CHATGPT_MEMORY_DENIED")
                with self.assertRaises(MemoryPolicyViolation):
                    assert_collective_persistence_source(source)

    def test_registered_external_sources_are_accepted(self):
        for source in ("agentbus", "artifactory", "internal_artifactory", CANONICAL_AGENTBUS_BOARD, CANONICAL_ARTIFACTORY_BOARD):
            with self.subTest(source=source):
                self.assertEqual(assert_collective_persistence_source(source), "AGENTBUS_CANONICAL")
        self.assertEqual(assert_collective_persistence_source("github"), "GITHUB_EXTERNAL_BACKUP")
        self.assertEqual(classify_persistence_source(CANONICAL_GITHUB_REPOSITORY), "GITHUB_EXTERNAL_BACKUP")
        self.assertEqual(CANONICAL_ARTIFACTORY_BOARD, CANONICAL_AGENTBUS_BOARD)

    def test_local_runtime_state_cannot_be_claimed_as_collective_authority(self):
        for source in ("sqlite", "local_filesystem", "process_memory"):
            with self.subTest(source=source):
                with self.assertRaises(MemoryPolicyViolation):
                    assert_collective_persistence_source(source)
        assert_local_state_non_authoritative(claimed_collective_authority=False)
        with self.assertRaises(MemoryPolicyViolation):
            assert_local_state_non_authoritative(claimed_collective_authority=True)

    def test_propagation_requires_verified_agentbus_and_github_receipts(self):
        agentbus = PersistenceReceipt("agentbus", CANONICAL_AGENTBUS_BOARD + "/directive.json", True)
        github = PersistenceReceipt("github", "commit:abc123", True)
        self.assertEqual(len(validate_external_receipts([agentbus, github])), 2)
        with self.assertRaises(MemoryPolicyViolation):
            validate_external_receipts([agentbus])
        with self.assertRaises(MemoryPolicyViolation):
            validate_external_receipts([agentbus, PersistenceReceipt("github", "commit:abc123", False)])

    def test_native_memory_is_not_an_availability_fallback(self):
        with self.assertRaises(ExternalPersistenceUnavailable):
            resolve_authoritative_collective_state(agentbus_available=False, github_available=True, github_state={"state": "backup"})
        self.assertEqual(
            resolve_authoritative_collective_state(agentbus_available=False, github_available=True, github_state={"state": "backup"}, require_agentbus_for_this_branch=False),
            {"state": "backup"},
        )
        with self.assertRaises(MemoryPolicyViolation):
            resolve_authoritative_collective_state(agentbus_state={"state": "external"}, native_memory_state={"state": "native"})

    def test_record_level_equivalence_not_whole_store_equality(self):
        a = {"logical_record_id": "r1", "payload_sha256": "abc", "agentbus_only": 1}
        b = {"logical_record_id": "r1", "payload_sha256": "abc", "github_only": 2}
        self.assertTrue(records_equivalent(a, b))
        self.assertEqual(resolve_authoritative_collective_state(agentbus_state=a, github_state=b), a)

        conflict = {"logical_record_id": "r1", "payload_sha256": "def"}
        self.assertFalse(records_equivalent(a, conflict))
        with self.assertRaises(ExternalPersistenceConflict):
            resolve_authoritative_collective_state(agentbus_state=a, github_state=conflict)

        unrelated = {"logical_record_id": "r2", "payload_sha256": "def"}
        self.assertIsNone(records_equivalent(a, unrelated))
        self.assertEqual(resolve_authoritative_collective_state(agentbus_state=a, github_state=unrelated), a)

    def test_p1_policy_is_active_and_v26_linked(self):
        policy = json.loads((ROOT / "governance/SWARM_MEMORY_PERSISTENCE_POLICY.json").read_text(encoding="utf-8"))
        self.assertEqual(policy["policy_id"], "IEP-MEM-001")
        self.assertEqual(policy["priority"], "P1")
        self.assertEqual(policy["status"], "ACTIVE")
        native = policy["native_chatgpt_memory"]
        self.assertEqual(native["protocol_access"], "MUST_NOT_CALL")
        self.assertEqual(native["fallback"], "DENY")
        self.assertEqual(policy["canonical_persistence"]["agentbus"]["message_board"], CANONICAL_AGENTBUS_BOARD)
        self.assertFalse(policy["canonical_persistence"]["agentbus"]["jfrog_artifactory"])
        self.assertEqual(policy["canonical_persistence"]["github"]["repository"], CANONICAL_GITHUB_REPOSITORY)
        self.assertFalse(policy["reconciliation"]["whole_store_difference_is_record_conflict"])
        self.assertEqual(policy["reconciliation"]["record_equivalence_requires"], ["logical_record_id", "payload_sha256"])

    def test_startup_and_package_surfaces_carry_p1_contract(self):
        context = (ROOT / "AGENT_CONTEXT_REFERENCE.md").read_text(encoding="utf-8")
        self.assertIn("P1 external-only swarm memory", context)
        self.assertIn("MUST_NOT_CALL_NATIVE_CHATGPT_MEMORY", context)
        self.assertIn("DO_NOT_FALL_BACK_TO_NATIVE_MEMORY", context)
        dependencies = json.loads((ROOT / "packaging/agent_package_dependencies.json").read_text(encoding="utf-8"))
        patterns = set(dependencies["shared_patterns"])
        self.assertIn("protocols/*.md", patterns)
        self.assertIn("governance/*.json", patterns)
        self.assertIn("org_agent_mesh/*.py", patterns)
        self.assertIn("AGENT_CONTEXT_REFERENCE.md", patterns)

    def test_no_unapproved_runtime_native_memory_identifiers(self):
        forbidden = ("chatgpt_memory", "saved_memory", "saved_memories", "memory_recall", "native_memory")
        allowed_runtime = {"swarm_memory_policy.py"}
        violations = []
        for path in sorted((ROOT / "org_agent_mesh").glob("*.py")):
            if path.name in allowed_runtime:
                continue
            text = path.read_text(encoding="utf-8").lower()
            for token in forbidden:
                if token in text:
                    violations.append(f"{path.relative_to(ROOT)}:{token}")
        self.assertEqual(violations, [], "unexpected native-memory runtime references: " + ", ".join(violations))


if __name__ == "__main__":
    unittest.main()
