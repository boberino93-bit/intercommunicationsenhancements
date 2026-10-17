from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
V26_SHA = "122e73dc7ba01384d799fc508c337081948ae1714f869a318d2ab96cd142d778"
V26_PREFIX = [
    "load_v26_canonical_bootstrap_adapter",
    "enter_unbound_read_only_and_initialize_validate_vmbus",
    "require_vmbus_ready",
    "load_principal_context_layers_build_indexes_and_require_principal_context_ready",
    "bind_host_chat_project_context_after_v26_readiness",
]


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class V26CanonicalAlignmentTests(unittest.TestCase):
    def test_root_and_generation_manifests_are_v26(self):
        root = load_json("PROJECT_MANIFEST.json")
        generation = load_json("PROJECT_MANIFEST_V26.json")
        adapter = load_json("bootstrap/V26_BOOTSTRAP_ADAPTER.json")
        self.assertEqual(root["canonical_bootstrap_generation"], "V26")
        self.assertEqual(root["canonical_generation_manifest"], "PROJECT_MANIFEST_V26.json")
        self.assertEqual(root["canonical_bootstrap_adapter"], "bootstrap/V26_BOOTSTRAP_ADAPTER.json")
        self.assertEqual(root["canonical_artifact_sha256"], V26_SHA)
        self.assertEqual(generation["version"], "V26")
        self.assertEqual(generation["status"], "CANONICAL_ACTIVE")
        self.assertTrue(generation["canonical_promotion"])
        self.assertFalse(generation["activation"]["v25_r11_active"])
        self.assertEqual(generation["artifact"]["sha256"], V26_SHA)
        self.assertEqual(adapter["version"], "V26")
        self.assertEqual(adapter["status"], "CANONICAL_ACTIVE_ON_MAIN")
        self.assertEqual(adapter["canonical_bootstrap_generation"], "V26")

    def test_v26_readiness_precedes_project_binding(self):
        order = load_json("BOOTSTRAP_ORDER.json")
        self.assertEqual(order["canonical_bootstrap_generation"], "V26")
        ids = [step["id"] for step in order["steps"]]
        self.assertEqual(ids[:len(V26_PREFIX)], V26_PREFIX)
        self.assertLess(ids.index("require_vmbus_ready"), ids.index("bind_host_chat_project_context_after_v26_readiness"))
        self.assertLess(ids.index("load_principal_context_layers_build_indexes_and_require_principal_context_ready"), ids.index("bind_host_chat_project_context_after_v26_readiness"))
        self.assertLess(ids.index("bind_host_chat_project_context_after_v26_readiness"), ids.index("classify_task_and_bind_work_context"))

    def test_local_bootstrap_is_v26_not_v25(self):
        local = load_json("AGENT_BOOTSTRAP.json")
        self.assertEqual(local["canonical_bootstrap_generation"], "V26")
        self.assertEqual(local["canonical_artifact_sha256"], V26_SHA)
        pre = local["v26_prebind_contract"]
        self.assertTrue(pre["vmbus_ready_before_project_bind"])
        self.assertTrue(pre["principal_context_ready_before_project_bind"])
        self.assertTrue(pre["principal_context_ready_before_task_interpretation"])
        self.assertFalse(pre["v25_r11_active"])
        self.assertEqual(pre["v25_r11_role"], "HISTORICAL_LINEAGE_ONLY")
        self.assertFalse(pre["cv_support_federated"])
        self.assertEqual(local["forum"]["surface"], "CHATGPT_LIBRARY_AGENTBUS")
        self.assertFalse(local["forum"]["legacy_authority_alias_is_jfrog"])

    def test_project_binding_surfaces_are_post_v26_readiness(self):
        policy = load_json("governance/PROJECT_CONTEXT_BINDING_POLICY.json")
        registry = load_json("governance/PROJECT_CONTEXT_BINDING_REGISTRY.json")
        self.assertEqual(policy["canonical_bootstrap_generation"], "V26")
        self.assertTrue(policy["v26_prebind_readiness"]["required"])
        self.assertEqual(policy["v26_prebind_readiness"]["required_barriers"], ["VMBUS_READY", "PRINCIPAL_CONTEXT_READY"])
        self.assertEqual(policy["host_project_context"]["binding_mode"], "HARD_BIND_AFTER_V26_READINESS_BEFORE_TASK_INTERPRETATION")
        self.assertEqual(registry["canonical_bootstrap_generation"], "V26")
        self.assertTrue(registry["semantics"]["v26_prebind_readiness_required"])
        self.assertEqual(registry["semantics"]["host_chat_project_when_available"], "HARD_BIND_AFTER_V26_READINESS_BEFORE_TASK_INTERPRETATION")
        self.assertFalse(registry["semantics"]["cv_support_federated"])
        self.assertIn("CV_SUPPORT", registry["explicit_non_federated_projects"])

        protocol = (ROOT / "protocols" / "project_context_binding.md").read_text(encoding="utf-8")
        self.assertIn("Canonical bootstrap generation: **V26**", protocol)
        self.assertLess(protocol.index("Mandatory V26 pre-bind boundary"), protocol.index("Project-bound startup order"))
        self.assertIn("VMBUS_READY", protocol)
        self.assertIn("PRINCIPAL_CONTEXT_READY", protocol)

    def test_universal_entrypoints_are_v26_first(self):
        machine = load_json("GLOBAL_AGENT_ENTRYPOINT.json")
        self.assertEqual(machine["canonical_bootstrap_generation"], "V26")
        self.assertTrue(machine["v26_prebind_contract"]["require_vmbus_ready_before_project_resolution"])
        self.assertTrue(machine["v26_prebind_contract"]["require_principal_context_ready_before_project_resolution"])
        self.assertEqual(machine["v26_prebind_contract"]["v25_r11_role"], "HISTORICAL_LINEAGE_ONLY")
        self.assertFalse(machine["v26_prebind_contract"]["cv_support_federated"])
        self.assertTrue(machine["swarm_synchronization_policy"]["critical_path_focus_required"])
        self.assertTrue(any("swarm_synchronization" in step for step in machine["sequence"]))

        human = (ROOT / "UNIVERSAL_AGENT_ENTRYPOINT.md").read_text(encoding="utf-8")
        self.assertIn("Canonical bootstrap generation: **V26**", human)
        self.assertLess(human.index("Mandatory V26 pre-bind readiness"), human.index("Existing-project discovery"))
        self.assertIn("V25 R11 and earlier generations are preserved historical lineage only", human)

    def test_separation_invariants_and_cv_support_exception(self):
        adapter = load_json("bootstrap/V26_BOOTSTRAP_ADAPTER.json")
        hard = set(adapter["hard_invariants"])
        for invariant in (
            "SHARED_INTERCOMMUNICATION_PROTOCOL != SHARED_PROJECT_STATE",
            "COMMON_BOOTSTRAP_INTERFACE != COMMON_PROJECT_AUTHORITY",
            "PROJECT_A_VMBUS != PROJECT_B_VMBUS",
            "CROSS_PROJECT_DISCOVERY != CROSS_PROJECT_DATA_ACCESS",
            "CV_SUPPORT != FEDERATED_PROJECT",
            "INTERCOMMUNICATION_ENHANCEMENTS = ONLY_SHARED_COORDINATION_PROJECT",
        ):
            self.assertIn(invariant, hard)
        generation = load_json("PROJECT_MANIFEST_V26.json")
        self.assertFalse(generation["project_sharing_boundary"]["cv_support_federated"])
        self.assertFalse(generation["project_sharing_boundary"]["shared_protocol_implies_shared_project_state"])
        self.assertFalse(generation["project_sharing_boundary"]["shared_protocol_implies_shared_project_authority"])

    def test_packages_require_v26_manifest_and_adapter(self):
        deps = load_json("packaging/agent_package_dependencies.json")
        required = set(deps["required_v26_components"])
        self.assertEqual(deps["canonical_bootstrap_generation"], "V26")
        self.assertIn("PROJECT_MANIFEST_V26.json", required)
        self.assertIn("bootstrap/V26_BOOTSTRAP_ADAPTER.json", required)
        patterns = set(deps["shared_patterns"])
        self.assertTrue(required.issubset(patterns))

    def test_role_bootstraps_are_v26_first(self):
        for role in ("PRIMARY", "MANAGER", "RESEARCH"):
            text = (ROOT / "bootstrap" / f"{role}.md").read_text(encoding="utf-8")
            with self.subTest(role=role):
                self.assertIn("Canonical bootstrap generation: **V26**", text)
                self.assertLess(text.index("Mandatory V26 pre-bind gate"), text.index("Mandatory project-context gate"))
                self.assertIn("VMBUS_READY", text)
                self.assertIn("PRINCIPAL_CONTEXT_READY", text)

    def test_active_docs_identify_v26_and_semver_axis_stays_separate(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        self.assertIn("Canonical bootstrap generation: V26", re.sub(r"[*`]", "", readme))
        self.assertIn("V26 canonical bootstrap precedence", start)
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(version, "1.6.0-alpha.1")

    def test_master_handoff_is_generation_26(self):
        handoff = load_json("MASTER_HANDOFF.json")
        self.assertEqual(handoff["generation"], 26)
        self.assertEqual(handoff["canonical_bootstrap_generation"], "V26")
        self.assertFalse(handoff["project_separation"]["cv_support_federated"])
        self.assertEqual(handoff["source_state"]["alignment_case"], "AUTH-20261016-V26-CANONICAL-ALIGNMENT-02")
        self.assertEqual(handoff["source_state"]["independent_proof_issue"], 199)


if __name__ == "__main__":
    unittest.main()
