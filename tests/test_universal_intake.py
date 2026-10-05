import copy
import json
from pathlib import Path
import unittest

from org_agent_mesh.universal_intake import (
    UniversalIntakeError,
    admit_roleless_role,
    complete_project_binding,
    discover_project,
    resolve_unbound_intake,
    validate_global_intake_registry,
)

ROOT = Path(__file__).resolve().parents[1]


class UniversalIntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((ROOT / "PROJECT_ROLE_ROUTING_REGISTRY.json").read_text())

    def test_real_registry_supports_unbound_intake(self):
        validate_global_intake_registry(self.registry)
        config = self.registry["global_intake"]
        self.assertEqual(config["mode"], "READ_ONLY_UNTIL_BOUND")
        self.assertEqual(config["generic_human_task_role_mode"], "ROLELESS_DEMAND_DRIVEN_ADMISSION")
        self.assertEqual(
            config["fallback_resolution"],
            "REGISTERED_FORUM_HANDOFF_EXACT_IDENTIFIER_ONLY",
        )
        self.assertEqual(
            config["unresolved_action"],
            "STOP_AFFECTED_MUTATION_CONTINUE_SAFE_READ_ONLY_DISCOVERY",
        )
        self.assertEqual(config["context_reference_path"], "AGENT_CONTEXT_REFERENCE.md")
        self.assertEqual(config["continuation_protocol_path"], "protocols/autonomous_continuation.md")

    def test_v15_unresolved_policy_cannot_become_mutating(self):
        registry = copy.deepcopy(self.registry)
        registry["global_intake"]["unresolved_action"] = "CONTINUE_MUTATION_WHILE_UNRESOLVED"
        with self.assertRaisesRegex(UniversalIntakeError, "invalid_unresolved_action"):
            validate_global_intake_registry(registry)

    def test_generic_human_task_resolves_project_but_not_role(self):
        result = resolve_unbound_intake(
            self.registry,
            task_text="Please fix the diagnostics in the duo screen project.",
        )
        self.assertEqual(result.discovery.project_id, "duo-open")
        self.assertIsNone(result.role_id)
        self.assertEqual(result.role_source, "roleless_demand_pending")
        self.assertTrue(result.roleless_admission_pending)
        self.assertFalse(result.mutation_ready)

    def test_repository_url_is_strong_evidence(self):
        discovery = discover_project(
            self.registry,
            task_text="Work from https://github.com/boberino93-bit/samsungpowerbootstrap",
        )
        self.assertEqual(discovery.project_id, "fold7-power-lab")

    def test_explicit_role_is_preserved_when_authorized(self):
        result = resolve_unbound_intake(
            self.registry,
            task_text="Research the warp propulsion lab handoff.",
            requested_role="research",
        )
        self.assertEqual(result.discovery.project_id, "warp-propulsion-lab")
        self.assertEqual(result.role_id, "research")
        self.assertEqual(result.role_source, "explicit")

    def test_topic_similarity_alone_does_not_resolve_project(self):
        with self.assertRaisesRegex(UniversalIntakeError, "project_unresolved"):
            resolve_unbound_intake(
                self.registry,
                task_text="Improve the animation on the foldable phone.",
            )

    def test_multiple_project_aliases_fail_closed(self):
        with self.assertRaisesRegex(
            UniversalIntakeError,
            "conflicting_or_ambiguous_project_evidence",
        ):
            resolve_unbound_intake(
                self.registry,
                task_text="Compare duo screen with fold7 power lab.",
            )

    def test_conflicting_explicit_and_task_evidence_fails_closed(self):
        with self.assertRaisesRegex(
            UniversalIntakeError,
            "conflicting_or_ambiguous_project_evidence",
        ):
            resolve_unbound_intake(
                self.registry,
                explicit_project_id="benefitflow",
                task_text="Continue work in duo screen.",
            )

    def test_no_human_task_and_no_role_stays_unbound(self):
        with self.assertRaisesRegex(
            UniversalIntakeError,
            "role_required_without_human_task",
        ):
            resolve_unbound_intake(
                self.registry,
                explicit_project_id="duo-open",
                human_task_present=False,
            )

    def test_duplicate_alias_across_projects_is_rejected(self):
        registry = copy.deepcopy(self.registry)
        registry["projects"]["benefitflow"]["discovery_aliases"].append("duo screen")
        with self.assertRaisesRegex(UniversalIntakeError, "duplicate_discovery_alias"):
            validate_global_intake_registry(registry)

    def test_alias_cannot_impersonate_another_project_identifier(self):
        registry = copy.deepcopy(self.registry)
        registry["projects"]["benefitflow"]["discovery_aliases"].append("duo-open")
        with self.assertRaisesRegex(
            UniversalIntakeError,
            "discovery_alias_conflicts_with_routing_identifier",
        ):
            validate_global_intake_registry(registry)

    def test_primary_cannot_be_self_admissible(self):
        registry = copy.deepcopy(self.registry)
        registry["projects"]["duo-open"]["self_admissible_roles"] = ["primary"]
        with self.assertRaisesRegex(UniversalIntakeError, "privileged_role_cannot_be_self_admissible"):
            validate_global_intake_registry(registry)

    def test_roleless_admission_selects_highest_positive_local_pressure(self):
        intake = resolve_unbound_intake(
            self.registry,
            explicit_project_id="intercommunicationsenhancements",
        )
        local_contract = json.loads((ROOT / "AGENT_BOOTSTRAP.json").read_text())
        admitted = admit_roleless_role(
            self.registry,
            intake=intake,
            local_contract=local_contract,
            role_pressure={"research": 7, "manager": 3, "primary": 1000},
            state_is_fresh=True,
        )
        self.assertEqual(admitted.role_id, "research")
        self.assertEqual(admitted.role_source, "roleless_demand_driven")
        self.assertFalse(admitted.mutation_ready)

    def test_roleless_admission_ignores_privileged_pressure(self):
        intake = resolve_unbound_intake(
            self.registry,
            explicit_project_id="intercommunicationsenhancements",
        )
        local_contract = json.loads((ROOT / "AGENT_BOOTSTRAP.json").read_text())
        with self.assertRaisesRegex(UniversalIntakeError, "no_material_work"):
            admit_roleless_role(
                self.registry,
                intake=intake,
                local_contract=local_contract,
                role_pressure={"research": 0, "manager": 0, "primary": 1000},
                state_is_fresh=True,
            )

    def test_roleless_admission_requires_fresh_state(self):
        intake = resolve_unbound_intake(
            self.registry,
            explicit_project_id="intercommunicationsenhancements",
        )
        local_contract = json.loads((ROOT / "AGENT_BOOTSTRAP.json").read_text())
        with self.assertRaisesRegex(UniversalIntakeError, "stale_role_demand_state"):
            admit_roleless_role(
                self.registry,
                intake=intake,
                local_contract=local_contract,
                role_pressure={"research": 1},
                state_is_fresh=False,
            )

    def test_generic_binding_requires_roleless_admission_first(self):
        intake = resolve_unbound_intake(
            self.registry,
            explicit_project_id="intercommunicationsenhancements",
        )
        local_contract = json.loads((ROOT / "AGENT_BOOTSTRAP.json").read_text())
        with self.assertRaisesRegex(UniversalIntakeError, "roleless_admission_required"):
            complete_project_binding(
                self.registry,
                intake=intake,
                local_contract=local_contract,
            )

    def test_complete_binding_after_roleless_admission_reuses_route_gate(self):
        intake = resolve_unbound_intake(
            self.registry,
            explicit_project_id="intercommunicationsenhancements",
        )
        local_contract = json.loads((ROOT / "AGENT_BOOTSTRAP.json").read_text())
        intake = admit_roleless_role(
            self.registry,
            intake=intake,
            local_contract=local_contract,
            role_pressure={"research": 1, "manager": 2},
            state_is_fresh=True,
        )
        route = complete_project_binding(
            self.registry,
            intake=intake,
            local_contract=local_contract,
        )
        self.assertEqual(route.project_id, "intercommunicationsenhancements")
        self.assertEqual(route.role_id, "manager")
        self.assertEqual(route.repository, "boberino93-bit/intercommunicationsenhancements")

    def test_other_projects_fail_closed_until_local_roleless_admission_is_enabled(self):
        intake = resolve_unbound_intake(
            self.registry,
            explicit_project_id="duo-open",
        )
        self.assertTrue(intake.roleless_admission_pending)
        self.assertEqual(self.registry["projects"]["duo-open"]["self_admissible_roles"], [])

    def test_role_packages_include_universal_entrypoint_contract(self):
        dependency_map = json.loads(
            (ROOT / "packaging" / "agent_package_dependencies.json").read_text()
        )
        shared = set(dependency_map["shared_patterns"])
        self.assertIn("GLOBAL_AGENT_ENTRYPOINT.json", shared)
        self.assertIn("UNIVERSAL_AGENT_ENTRYPOINT.md", shared)
        self.assertIn("org_agent_mesh/*.py", shared)
        self.assertIn("protocols/*.md", shared)
        self.assertIn("governance/*.json", shared)


if __name__ == "__main__":
    unittest.main()
