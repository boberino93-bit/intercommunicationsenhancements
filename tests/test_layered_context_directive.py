from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LayeredContextDirectiveTests(unittest.TestCase):
    def test_policy_declares_context_pervasive_and_layered(self):
        policy = json.loads(
            (ROOT / "governance/LAYERED_CONTEXT_POLICY.json").read_text(encoding="utf-8")
        )
        self.assertEqual(policy["policy_id"], "IEP-CTX-001")
        self.assertEqual(policy["status"], "ACTIVE")
        self.assertEqual(
            policy["bootstrap_invariant"],
            "CONTEXT_IS_PRESENT_IN_EVERY_OBSERVABLE_INPUT_AND_MAY_EXIST_AT_MULTIPLE_LAYERS",
        )
        rules = policy["rules"]
        self.assertFalse(rules["absence_in_one_layer_proves_global_absence"])
        self.assertTrue(rules["scan_available_authorized_layers_before_declaring_context_missing"])
        self.assertTrue(rules["scan_available_authorized_layers_before_asking_human_to_repeat"])
        self.assertTrue(rules["preserve_layer_provenance"])
        self.assertTrue(rules["preserve_temporal_state"])
        self.assertTrue(rules["preserve_material_contradictions"])
        self.assertTrue(rules["authority_is_separate_from_context_presence"])
        self.assertTrue(rules["do_not_infer_inaccessible_hidden_context"])

    def test_context_reference_embeds_bootstrap_directive(self):
        context = (ROOT / "AGENT_CONTEXT_REFERENCE.md").read_text(encoding="utf-8")
        self.assertIn("Bootstrap directive — layered context", context)
        self.assertIn("CONTEXT_IS_PERVASIVE_LAYERED_AND_PROVENANCE_BOUND", context)
        self.assertIn("Do not equate absence in one layer with global absence", context)
        self.assertIn("context presence", context)
        self.assertIn("evidence quality", context)
        self.assertIn("authority", context)
        self.assertIn("BEFORE / AFTER / CURRENT / BASELINE", context)

    def test_directive_is_packaged_for_all_roles(self):
        directive = json.loads(
            (ROOT / ".interagent/directives/2026-10-07-layered-context-awareness.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(directive["status"], "ACTIVE")
        self.assertEqual(directive["policy_id"], "IEP-CTX-001")
        self.assertEqual(
            directive["bootstrap_marker"],
            "CONTEXT_IS_PERVASIVE_LAYERED_AND_PROVENANCE_BOUND",
        )

        dependencies = json.loads(
            (ROOT / "packaging/agent_package_dependencies.json").read_text(encoding="utf-8")
        )
        patterns = set(dependencies["shared_patterns"])
        self.assertIn("AGENT_CONTEXT_REFERENCE.md", patterns)
        self.assertIn(".interagent/directives/*.json", patterns)
        self.assertIn("governance/*.json", patterns)
        self.assertIn("protocols/*.md", patterns)

    def test_native_memory_boundary_remains_intact(self):
        policy = json.loads(
            (ROOT / "governance/LAYERED_CONTEXT_POLICY.json").read_text(encoding="utf-8")
        )
        boundary = policy["native_chatgpt_memory_boundary"]
        self.assertEqual(boundary["policy_id"], "IEP-MEM-001")
        self.assertFalse(boundary["may_be_swarm_authority"])
        self.assertFalse(boundary["may_be_queried_as_swarm_fallback"])
        self.assertTrue(boundary["host_supplied_ephemeral_context_may_be_observed"])
        self.assertTrue(
            boundary[
                "host_supplied_ephemeral_context_requires_external_verification_for_swarm_authority_claims"
            ]
        )


if __name__ == "__main__":
    unittest.main()
