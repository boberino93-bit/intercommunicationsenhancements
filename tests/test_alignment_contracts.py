from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from org_agent_mesh.universal_intake import discover_project


class CrossContractAlignmentTests(unittest.TestCase):
    def test_task_classification_precedes_every_swarm_mutation(self):
        bootstrap = json.loads((ROOT / "BOOTSTRAP_ORDER.json").read_text(encoding="utf-8"))
        steps = bootstrap["steps"]
        classify_index = next(i for i, step in enumerate(steps) if step["id"] == "classify_task_and_bind_work_context")
        for i, step in enumerate(steps):
            if i < classify_index:
                self.assertFalse(step.get("mutation_allowed", False), step["id"])
        ready_index = next(i for i, step in enumerate(steps) if step["id"] == "bind_global_run_role_instance_and_ready_barrier_if_swarm")
        self.assertGreater(ready_index, classify_index)

    def test_master_handoff_is_required_before_mutation(self):
        bootstrap = json.loads((ROOT / "BOOTSTRAP_ORDER.json").read_text(encoding="utf-8"))
        ids = [step["id"] for step in bootstrap["steps"]]
        self.assertLess(ids.index("load_master_handoff"), ids.index("execute_task_with_per_mutation_scope_validation"))
        local = json.loads((ROOT / "AGENT_BOOTSTRAP.json").read_text(encoding="utf-8"))
        self.assertTrue(local["master_handoff"]["required_before_mutation"])
        self.assertTrue(local["rules"]["manual_master_handoff_checkpoint_after_material_transition"])
        self.assertTrue((ROOT / "MASTER_HANDOFF.json").is_file())
        self.assertTrue((ROOT / "protocols" / "agent_state_handoff.md").is_file())
        self.assertTrue((ROOT / "schemas" / "master_handoff.schema.json").is_file())

    def test_authority_roles_are_not_execution_modes(self):
        registry = json.loads((ROOT / "PROJECT_ROLE_ROUTING_REGISTRY.json").read_text(encoding="utf-8"))
        expected_roles, expected_modes = {"primary", "manager", "research"}, {"recovery", "qa", "build"}
        for project in registry["projects"].values():
            self.assertEqual(set(project["roles"]), expected_roles)
            self.assertTrue(expected_modes.issubset(set(project["execution_modes"])))
            self.assertTrue(expected_roles.isdisjoint(set(project["execution_modes"])))
            self.assertEqual(project["master_handoff_path"], "MASTER_HANDOFF.json")
            self.assertIn("MASTER_HANDOFF.json", project["handoff_paths"])

    def test_global_round_member_is_routable(self):
        registry = json.loads((ROOT / "PROJECT_ROLE_ROUTING_REGISTRY.json").read_text(encoding="utf-8"))
        swarm = json.loads((ROOT / "swarm_kernel" / "project.json").read_text(encoding="utf-8"))
        for project_id in swarm["expected_global_round_projects"]:
            self.assertIn(project_id, registry["projects"])

    def test_active_project_context_resolves_this_project_without_history_guessing(self):
        registry = json.loads((ROOT / "PROJECT_ROLE_ROUTING_REGISTRY.json").read_text(encoding="utf-8"))
        discovery = discover_project(registry, task_text="Would you say this project is still in alpha?", active_project_context="intercommunicationsenhancements")
        self.assertEqual(discovery.project_id, "intercommunicationsenhancements")
        self.assertIn("active_project_context", discovery.evidence)

    def test_semantic_package_closure_carries_handoff_and_factory(self):
        deps = json.loads((ROOT / "packaging" / "agent_package_dependencies.json").read_text(encoding="utf-8"))
        patterns = set(deps["shared_patterns"])
        for required in ("MASTER_HANDOFF.json", "NEW_PROJECT_BOOTSTRAP.json", "HARDENING_STATUS.md", "templates/new-project/*.json", "templates/new-project/*.md"):
            self.assertIn(required, patterns)

    def test_new_project_factory_materializes_master_handoff(self):
        kit = json.loads((ROOT / "NEW_PROJECT_BOOTSTRAP.json").read_text(encoding="utf-8"))
        outputs = {entry["output"] for entry in kit["required_documents"]}
        self.assertIn("MASTER_HANDOFF.json", outputs)
        self.assertIn(".interagent/handoffs", kit["required_directories"])


if __name__ == "__main__":
    unittest.main()
