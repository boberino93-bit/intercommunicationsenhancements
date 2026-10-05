from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NewProjectBootstrapKitTests(unittest.TestCase):
    def test_manifest_is_unbound_and_has_required_templates(self):
        kit = json.loads((ROOT / "NEW_PROJECT_BOOTSTRAP.json").read_text())
        self.assertEqual(kit["seed_state"]["repository_binding"], "UNBOUND")
        self.assertFalse(kit["seed_state"]["github_required_to_start"])
        self.assertIsNone(kit["seed_state"]["repository_view"]["path"])
        self.assertTrue(kit["recursion"]["every_seeded_project_materializes_local_factory_pointer"])
        outputs = {item["output"] for item in kit["required_documents"]}
        self.assertEqual(
            outputs,
            {
                "AGENT_BOOTSTRAP.json",
                "PROJECT_IDENTITY_LOCK.json",
                "PROJECT_MANIFEST.json",
                "BOOTSTRAP_ORDER.json",
                "MASTER_HANDOFF.json",
                "AGENT_CONTEXT_REFERENCE.md",
                "START_HERE.md",
                "PROJECT_CHARTER.md",
                "HARDENING_STATUS.md",
                "NEW_PROJECT_BOOTSTRAP.json",
            },
        )
        self.assertIn(".interagent/handoffs", kit["required_directories"])
        for item in kit["required_documents"]:
            self.assertTrue((ROOT / item["template"]).is_file(), item["template"])

    def test_json_templates_parse_and_do_not_bind_source_repository(self):
        template_names = [
            "AGENT_BOOTSTRAP.template.json",
            "PROJECT_IDENTITY_LOCK.template.json",
            "PROJECT_MANIFEST.template.json",
            "BOOTSTRAP_ORDER.template.json",
            "MASTER_HANDOFF.template.json",
            "NEW_PROJECT_BOOTSTRAP.template.json",
        ]
        for name in template_names:
            raw = (ROOT / "templates" / "new-project" / name).read_text()
            parsed = json.loads(raw)
            repository = parsed.get("repository")
            if repository is not None:
                self.assertEqual(repository.get("binding_state"), "UNBOUND")
                self.assertIsNone(repository.get("full_name"))
                self.assertIsNone(repository.get("id"))
            self.assertNotIn('"full_name": "boberino93-bit/', raw)

    def test_recursive_pointer_is_unbound_and_canonical(self):
        pointer = json.loads((ROOT / "templates" / "new-project" / "NEW_PROJECT_BOOTSTRAP.template.json").read_text())
        self.assertEqual(pointer["source_project"]["repository_binding_state"], "UNBOUND")
        self.assertIsNone(pointer["source_project"]["repository"])
        self.assertEqual(pointer["canonical_kit"]["repository"], "boberino93-bit/intercommunicationsenhancements")
        self.assertTrue(pointer["rules"]["materialize_this_pointer_in_every_seeded_project"])
        self.assertTrue(pointer["rules"]["new_project_must_receive_master_handoff"])
        self.assertFalse(pointer["local_reference"]["copy_identity_values"])

    def test_global_entrypoint_has_explicit_new_project_branch(self):
        entrypoint = json.loads((ROOT / "GLOBAL_AGENT_ENTRYPOINT.json").read_text())
        branch = entrypoint["intent_branches"]["new_project_bootstrap"]
        self.assertEqual(branch["mode"], "UNBOUND_PROJECT_SEED")
        self.assertFalse(branch["repository_required"])
        self.assertEqual(branch["source_project_identity_inheritance"], "DENY")
        self.assertEqual(branch["cross_project_mutation"], "DENY")

    def test_local_bootstrap_exposes_project_factory_master_handoff_and_context_reference(self):
        bootstrap = json.loads((ROOT / "AGENT_BOOTSTRAP.json").read_text())
        self.assertEqual(bootstrap["project_factory"]["pointer"], "NEW_PROJECT_BOOTSTRAP.json")
        self.assertTrue(bootstrap["project_factory"]["supports_unbound_repository"])
        self.assertIn("NEW_PROJECT_BOOTSTRAP.json", bootstrap["handoff_paths"])
        self.assertIn("MASTER_HANDOFF.json", bootstrap["handoff_paths"])
        self.assertIn("AGENT_CONTEXT_REFERENCE.md", bootstrap["handoff_paths"])
        self.assertTrue(bootstrap["master_handoff"]["manual_checkpoint_required"])
        self.assertEqual(bootstrap["fresh_agent_context"]["authority"], "ORIENTATION_ONLY")
        self.assertEqual(bootstrap["authorized_roles"], ["primary", "manager", "research"])
        self.assertIn("recovery", bootstrap["execution_modes"])

    def test_new_project_templates_inherit_mutation_roleless_and_authentication_hardening(self):
        bootstrap_template = json.loads(
            (ROOT / "templates" / "new-project" / "AGENT_BOOTSTRAP.template.json").read_text()
        )
        authentication = bootstrap_template["authority_authentication"]
        self.assertTrue(authentication["explicit_principal_claim_required_before_authorization"])
        self.assertTrue(authentication["never_assume_current_speaker_is_authorized"])
        self.assertEqual(authentication["static_personal_fact_authentication"], "DENY")
        self.assertTrue(authentication["high_consequence_independent_external_proof_required"])
        self.assertFalse(authentication["agent_may_answer_its_own_challenge"])

        mutation = bootstrap_template["mutation_authorization"]
        self.assertEqual(mutation["invariant"], "INTENT_IS_NOT_AUTHORIZATION")
        self.assertTrue(mutation["required_before_every_external_mutation"])
        self.assertTrue(mutation["single_use_case_required"])
        self.assertFalse(mutation["session_wide_authorization"])
        self.assertFalse(mutation["conversation_wide_authorization"])
        self.assertFalse(mutation["prior_authorization_reuse"])
        self.assertFalse(mutation["role_is_authorization"])
        self.assertFalse(mutation["claim_or_lease_is_authorization"])
        roleless = bootstrap_template["roleless_agent_admission"]
        self.assertTrue(roleless["required_for_generic_human_launch_without_explicit_role"])
        self.assertFalse(roleless["primary_self_promotion"])
        self.assertFalse(roleless["role_or_claim_grants_mutation_authority"])
        self.assertEqual(roleless["self_admissible_roles"], ["research", "manager"])

        order_template = json.loads(
            (ROOT / "templates" / "new-project" / "BOOTSTRAP_ORDER.template.json").read_text()
        )
        self.assertEqual(order_template["schema"], "org-agent-mesh/bootstrap-order/v5")
        self.assertEqual(order_template["mutation_authorization"]["invariant"], "INTENT_IS_NOT_AUTHORIZATION")
        self.assertTrue(order_template["mutation_authorization"]["single_use_case_required"])
        self.assertFalse(order_template["roleless_admission"]["primary_self_promotion"])
        required_gates = {
            "explicit registered authority principal claim present",
            "current single-use authorization case present",
            "human authorization explicitly names current case id",
            "current case matches target mutation class bounded scope consequence and action digest",
            "current case is unconsumed and unexpired",
            "high-consequence independent principal proof satisfied when applicable",
        }
        self.assertTrue(required_gates.issubset(set(order_template["mutation_gate"])))

    def test_scheduled_launch_contract_propagates_to_new_projects(self):
        bootstrap_template = json.loads(
            (ROOT / "templates" / "new-project" / "AGENT_BOOTSTRAP.template.json").read_text()
        )
        scheduled = bootstrap_template["scheduled_launch_contract"]
        self.assertEqual(scheduled["context_schema"], "org-agent-mesh/scheduled-launch-context/v1")
        self.assertEqual(scheduled["route_schema"], "org-agent-mesh/scheduled-task-route/v2")
        self.assertTrue(scheduled["capture_from_local_contract"])
        self.assertTrue(scheduled["validate_against_local_contract_before_mutation"])
        self.assertEqual(scheduled["task_state_advancement_before_bootstrap_ready"], "DENY")
        self.assertFalse(scheduled["schedule_fire_is_authority"])
        self.assertFalse(scheduled["task_contract_is_future_mutation_authority"])
        self.assertTrue(scheduled["each_distinct_scheduled_mutation_case_requires_fresh_human_authorization"])

        order_template = json.loads(
            (ROOT / "templates" / "new-project" / "BOOTSTRAP_ORDER.template.json").read_text()
        )
        self.assertTrue(order_template["pre_provider_admission"]["required_for_dynamic_scheduled_launches"])
        self.assertEqual(order_template["pre_provider_admission"]["task_state_advancement_before_bootstrap_ready"], "DENY")
        self.assertEqual(
            order_template["launch_origin_rules"]["SCHEDULED_PROJECT_BOUND"],
            "require machine-readable launch context captured from this project's local contract and verify it before mutation",
        )
        self.assertEqual(order_template["autonomous_continuation"]["routine_confirmation"], "DENY_AFTER_VALID_ASSIGNMENT")
        self.assertTrue(order_template["autonomous_continuation"]["localized_fail_closed"])

        entrypoint = json.loads((ROOT / "GLOBAL_AGENT_ENTRYPOINT.json").read_text())
        scheduled_branch = entrypoint["intent_branches"]["scheduled_project_bound_task"]
        self.assertEqual(scheduled_branch["mode"], "PROJECT_BOUND_ROUTED")
        self.assertTrue(scheduled_branch["local_contract_verification_required"])
        self.assertEqual(scheduled_branch["topic_similarity_fallback"], "DENY")


if __name__ == "__main__":
    unittest.main()
