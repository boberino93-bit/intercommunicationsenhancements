from pathlib import Path
import json
import unittest

from org_agent_mesh.swarm_memory_policy import (
    CANONICAL_ARTIFACTORY_BOARD,
    CANONICAL_GITHUB_REPOSITORY,
    ExternalPersistenceConflict,
    ExternalPersistenceUnavailable,
    MemoryPolicyViolation,
    PersistenceReceipt,
    assert_collective_persistence_source,
    assert_local_state_non_authoritative,
    classify_persistence_source,
    resolve_authoritative_collective_state,
    validate_external_receipts,
)


ROOT = Path(__file__).resolve().parents[1]


class SwarmMemoryPolicyTests(unittest.TestCase):
    def test_native_chatgpt_memory_aliases_are_hard_denied(self):
        for source in (
            "native_chatgpt_memory",
            "chatgpt_memory",
            "saved_memory",
            "memory_recall",
            "chatgpt_memory_recall",
            "host_memory",
        ):
            with self.subTest(source=source):
                self.assertEqual(
                    classify_persistence_source(source),
                    "NATIVE_CHATGPT_MEMORY_DENIED",
                )
                with self.assertRaises(MemoryPolicyViolation):
                    assert_collective_persistence_source(source)

    def test_registered_external_sources_are_accepted(self):
        self.assertEqual(
            assert_collective_persistence_source("artifactory"),
            "ARTIFACTORY_CANONICAL",
        )
        self.assertEqual(
            assert_collective_persistence_source("github"),
            "GITHUB_EXTERNAL_BACKUP",
        )
        self.assertEqual(
            classify_persistence_source(CANONICAL_ARTIFACTORY_BOARD),
            "ARTIFACTORY_CANONICAL",
        )
        self.assertEqual(
            classify_persistence_source(CANONICAL_GITHUB_REPOSITORY),
            "GITHUB_EXTERNAL_BACKUP",
        )

    def test_local_runtime_state_cannot_be_claimed_as_collective_authority(self):
        for source in ("sqlite", "local_filesystem", "process_memory"):
            with self.subTest(source=source):
                with self.assertRaises(MemoryPolicyViolation):
                    assert_collective_persistence_source(source)
        assert_local_state_non_authoritative(claimed_collective_authority=False)
        with self.assertRaises(MemoryPolicyViolation):
            assert_local_state_non_authoritative(claimed_collective_authority=True)

    def test_propagation_requires_verified_artifactory_and_github_receipts(self):
        artifactory = PersistenceReceipt(
            backend="artifactory",
            reference=CANONICAL_ARTIFACTORY_BOARD + "/directive.json",
            readback_verified=True,
        )
        github = PersistenceReceipt(
            backend="github",
            reference="commit:abc123",
            readback_verified=True,
        )
        self.assertEqual(
            len(validate_external_receipts([artifactory, github])),
            2,
        )
        with self.assertRaises(MemoryPolicyViolation):
            validate_external_receipts([artifactory])
        with self.assertRaises(MemoryPolicyViolation):
            validate_external_receipts([
                artifactory,
                PersistenceReceipt("github", "commit:abc123", False),
            ])

    def test_native_memory_is_not_an_availability_fallback(self):
        with self.assertRaises(ExternalPersistenceUnavailable):
            resolve_authoritative_collective_state(
                artifactory_available=False,
                github_available=True,
                github_state={"state": "backup"},
            )
        with self.assertRaises(MemoryPolicyViolation):
            resolve_authoritative_collective_state(
                artifactory_state={"state": "external"},
                native_memory_state={"state": "native"},
            )

    def test_external_conflict_fails_closed(self):
        with self.assertRaises(ExternalPersistenceConflict):
            resolve_authoritative_collective_state(
                artifactory_state={"version": 2},
                github_state={"version": 1},
            )
        expected = {"version": 2}
        self.assertEqual(
            resolve_authoritative_collective_state(
                artifactory_state=expected,
                github_state=expected,
            ),
            expected,
        )

    def test_p1_policy_is_active_and_exact(self):
        policy = json.loads(
            (ROOT / "governance/SWARM_MEMORY_PERSISTENCE_POLICY.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(policy["policy_id"], "IEP-MEM-001")
        self.assertEqual(policy["priority"], "P1")
        self.assertEqual(policy["status"], "ACTIVE")
        native = policy["native_chatgpt_memory"]
        self.assertEqual(native["protocol_access"], "MUST_NOT_CALL")
        self.assertEqual(native["recall_ingestion"], "DENY")
        self.assertEqual(native["fallback"], "DENY")
        self.assertEqual(native["collective_state_source"], "DENY")
        self.assertEqual(
            policy["canonical_persistence"]["artifactory"]["message_board"],
            CANONICAL_ARTIFACTORY_BOARD,
        )
        self.assertEqual(
            policy["canonical_persistence"]["github"]["repository"],
            CANONICAL_GITHUB_REPOSITORY,
        )

    def test_startup_and_package_surfaces_carry_p1_contract(self):
        context = (ROOT / "AGENT_CONTEXT_REFERENCE.md").read_text(encoding="utf-8")
        self.assertIn("P1 external-only swarm memory", context)
        self.assertIn("MUST_NOT_CALL_NATIVE_CHATGPT_MEMORY", context)
        self.assertIn("DO_NOT_FALL_BACK_TO_NATIVE_MEMORY", context)

        dependencies = json.loads(
            (ROOT / "packaging/agent_package_dependencies.json").read_text(
                encoding="utf-8"
            )
        )
        patterns = set(dependencies["shared_patterns"])
        self.assertIn("protocols/*.md", patterns)
        self.assertIn("governance/*.json", patterns)
        self.assertIn("org_agent_mesh/*.py", patterns)
        self.assertIn("AGENT_CONTEXT_REFERENCE.md", patterns)

        build_tool = (ROOT / "tools/build_agent_packages.py").read_text(encoding="utf-8")
        self.assertIn("_validate_swarm_memory_policy", build_tool)
        self.assertIn("SWARM_MEMORY_PERSISTENCE_POLICY.json", build_tool)

    def test_no_unapproved_runtime_native_memory_identifiers(self):
        forbidden = (
            "chatgpt_memory",
            "saved_memory",
            "saved_memories",
            "memory_recall",
            "native_memory",
        )
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

    def test_no_unapproved_protocol_native_memory_fallback_language(self):
        forbidden = (
            "chatgpt_memory",
            "saved_memory",
            "saved_memories",
            "memory_recall",
            "native_memory",
        )
        allowed_protocols = {"external_swarm_memory.md", "layered_context_resolution.md"}
        violations = []
        for path in sorted((ROOT / "protocols").glob("*.md")):
            if path.name in allowed_protocols:
                continue
            text = path.read_text(encoding="utf-8").lower()
            for token in forbidden:
                if token in text:
                    violations.append(f"{path.relative_to(ROOT)}:{token}")
        self.assertEqual(violations, [], "unexpected native-memory protocol references: " + ", ".join(violations))


if __name__ == "__main__":
    unittest.main()
