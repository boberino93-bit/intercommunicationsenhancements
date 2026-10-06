import json
from pathlib import Path
import unittest

from org_agent_mesh.project_context_binding import (
    ProjectContextBindingError,
    bind_host_project_context,
    parse_project_launch_context,
    render_project_launch_context,
    require_project_context_ready,
    resolve_host_project_id,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "governance" / "PROJECT_CONTEXT_BINDING_REGISTRY.json").read_text())


class ProjectContextBindingTests(unittest.TestCase):
    def test_current_project_display_name_resolves(self):
        self.assertEqual(
            resolve_host_project_id(REGISTRY, "Intercommunication enhancements"),
            "intercommunicationsenhancements",
        )

    def test_display_name_resolves(self):
        self.assertEqual(resolve_host_project_id(REGISTRY, "Duo Screen"), "duo-open")

    def test_xrp_mapping_exists_and_uses_internal_forum(self):
        binding = bind_host_project_context(REGISTRY, host_project_context="Xrp analysis")
        self.assertEqual(binding.project_id, "xrp-thesis")
        self.assertEqual(binding.forum_authority, "INTERNAL_ARTIFACTORY")
        self.assertEqual(binding.forum_namespace, "/XRPTHESIS-AgentBus/messages")

    def test_conflicting_explicit_project_is_denied(self):
        with self.assertRaises(ProjectContextBindingError):
            bind_host_project_context(
                REGISTRY,
                host_project_context="Duo Screen",
                explicit_project_id="benefitflow",
            )

    def test_launch_context_round_trip(self):
        binding = bind_host_project_context(REGISTRY, host_project_context="Duo Screen")
        rendered = render_project_launch_context(binding)
        parsed = parse_project_launch_context(
            "Start work\n" + rendered + "\nThen continue",
            REGISTRY,
        )
        self.assertEqual(parsed, binding)

    def test_tampered_launch_context_is_denied(self):
        binding = bind_host_project_context(REGISTRY, host_project_context="Duo Screen")
        rendered = render_project_launch_context(binding).replace(
            "boberino93-bit/duo-open",
            "boberino93-bit/benefitflow",
        )
        with self.assertRaises(ProjectContextBindingError):
            parse_project_launch_context(rendered, REGISTRY)

    def test_ready_barrier_requires_local_context(self):
        binding = bind_host_project_context(REGISTRY, host_project_context="Duo Screen")
        with self.assertRaises(ProjectContextBindingError):
            require_project_context_ready(
                binding=binding,
                local_bootstrap_loaded=True,
                context_reference_loaded=False,
                identity_lock_checked=True,
                handoff_loaded=True,
                coordination_route_loaded=True,
            )
        self.assertTrue(
            require_project_context_ready(
                binding=binding,
                local_bootstrap_loaded=True,
                context_reference_loaded=True,
                identity_lock_checked=True,
                handoff_loaded=True,
                coordination_route_loaded=True,
            )
        )

    def test_all_deployable_role_bootstraps_gate_host_project_before_bootstrap_order(self):
        for role in ("PRIMARY", "MANAGER", "RESEARCH"):
            text = (ROOT / "bootstrap" / f"{role}.md").read_text()
            with self.subTest(role=role):
                self.assertIn("Mandatory project-context gate", text)
                self.assertIn("protocols/project_context_binding.md", text)
                self.assertIn("org_agent_mesh.project_context_binding", text)
                gate_pos = text.index("Mandatory project-context gate")
                order_pos = text.index("execute `BOOTSTRAP_ORDER.json`")
                self.assertLess(gate_pos, order_pos)
                self.assertIn(
                    "Only when no host project context can be verified may startup enter `UNIVERSAL_AGENT_ENTRYPOINT.md`",
                    text,
                )
                self.assertIn(
                    "before role admission, task interpretation, handoff execution, or mutation evaluation",
                    text,
                )

    def test_machine_bootstrap_makes_project_context_step_zero_and_guards_execution(self):
        bootstrap = json.loads((ROOT / "BOOTSTRAP_ORDER.json").read_text())
        self.assertEqual(bootstrap["schema"], "org-agent-mesh/bootstrap-order/v7")
        contract = bootstrap["project_context_binding_contract"]
        self.assertTrue(
            contract["required_before_every_other_bootstrap_step_when_host_context_available"]
        )
        self.assertFalse(contract["task_text_may_override_host_context"])
        self.assertTrue(
            contract[
                "ready_barrier_required_before_role_admission_task_interpretation_handoff_execution_or_mutation_evaluation"
            ]
        )

        steps = {step["id"]: step for step in bootstrap["steps"]}
        gate = steps["bind_host_chat_project_context_before_all_other_bootstrap"]
        self.assertEqual(gate["order"], 0)
        self.assertEqual(gate["task_text_override"], "DENY")
        self.assertEqual(
            gate["unbound_fallback"],
            "ONLY_IF_HOST_CONTEXT_UNAVAILABLE_OR_UNVERIFIABLE",
        )
        self.assertFalse(gate["mutation_allowed"])

        self.assertTrue(
            steps["classify_task_and_bind_work_context"]["project_context_ready_required"]
        )
        self.assertTrue(
            steps["evaluate_current_mutation_authorization_envelope"][
                "project_context_ready_required"
            ]
        )
        for step_id in (
            "bind_global_run_role_instance_and_ready_barrier_if_swarm",
            "execute_task_with_autonomous_continuation_and_per_mutation_scope_validation",
            "persist_learning_checkpoint_and_handoff",
            "checkpoint_master_handoff_after_material_transition_or_before_yield",
        ):
            self.assertIn("project_context_ready", steps[step_id]["additional_guards"])


if __name__ == "__main__":
    unittest.main()
