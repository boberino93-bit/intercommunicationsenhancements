from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TaskIntakeRoutingTests(unittest.TestCase):
    def test_task_classification_precedes_mutation(self):
        bootstrap = json.loads((ROOT / "BOOTSTRAP_ORDER.json").read_text(encoding="utf-8"))
        steps = bootstrap["steps"]
        ids = [step["id"] for step in steps]
        classify = ids.index("classify_task_and_bind_work_context")
        execute = ids.index("execute_task_with_per_mutation_scope_validation")
        self.assertLess(classify, execute)
        self.assertFalse(steps[classify]["mutation_allowed"])
        self.assertTrue(steps[execute]["mutation_allowed"])
        self.assertEqual(steps[classify]["path"], "protocols/task_intake_and_delegation.md")

    def test_new_protocol_and_schemas_are_dependency_closed(self):
        deps = json.loads((ROOT / "packaging/agent_package_dependencies.json").read_text(encoding="utf-8"))
        shared = deps["shared_patterns"]
        self.assertIn("protocols/*.md", shared)
        self.assertIn("schemas/*.json", shared)
        self.assertTrue((ROOT / "protocols/task_intake_and_delegation.md").is_file())
        self.assertTrue((ROOT / "schemas/task_intake.schema.json").is_file())
        self.assertTrue((ROOT / "schemas/delegation_contract.schema.json").is_file())

    def test_task_intake_schema_exposes_safe_modes_and_swarm_decision(self):
        schema = json.loads((ROOT / "schemas/task_intake.schema.json").read_text(encoding="utf-8"))
        modes = schema["properties"]["mode"]["enum"]
        self.assertIn("NEW_PROJECT_BOOTSTRAP", modes)
        self.assertIn("AMBIGUOUS_PROJECT", modes)
        assessment = schema["properties"]["research_assessment"]["properties"]
        self.assertIn("proposed_research_agents", assessment)
        self.assertIn("proposed_manager_agents", assessment)
        self.assertIn("dependency_density", assessment)
        self.assertIn("independent_verification_required", assessment)

    def test_delegation_contract_contains_required_scope_controls(self):
        schema = json.loads((ROOT / "schemas/delegation_contract.schema.json").read_text(encoding="utf-8"))
        required = set(schema["required"])
        for field in (
            "objective",
            "in_scope_resources",
            "out_of_scope_boundaries",
            "allowed_tools",
            "capability_ceiling",
            "write_boundaries",
            "source_of_truth_refs",
            "evidence_requirements",
            "output_contract",
            "completion_condition",
            "failure_condition",
        ):
            self.assertIn(field, required)

    def test_primary_bootstrap_blocks_cross_project_state_leakage(self):
        text = (ROOT / "bootstrap/PRIMARY.md").read_text(encoding="utf-8")
        self.assertIn("Do not place project-specific identity", text)
        self.assertIn("delegation_contract", text)
        self.assertIn("only the bound ACTIVE Primary", text)


if __name__ == "__main__":
    unittest.main()
