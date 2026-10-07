from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SchedulerSynchronizationTests(unittest.TestCase):
    def load(self, path):
        return json.loads((ROOT / path).read_text())

    def test_bootstrap_loads_sync_contract(self):
        bootstrap = self.load("bootstrap/INTERNAL_SCHEDULER_SERVICE.json")
        self.assertEqual(bootstrap["scheduler_sync_directive"], "governance/SCHEDULER_SYNCHRONIZATION_DIRECTIVE.json")
        self.assertEqual(bootstrap["frontend_binding_registry"], "governance/SCHEDULER_FRONTEND_BINDINGS.json")
        self.assertEqual(bootstrap["control_interface"], "governance/SCHEDULER_CONTROL_INTERFACE.json")
        self.assertTrue(bootstrap["invariants"]["declared_mapping_required_for_frontend_backend_sync"])
        self.assertTrue(bootstrap["invariants"]["unmapped_frontend_task_mutation_prohibited"])

    def test_only_declared_bindings_may_auto_repair(self):
        directive = self.load("governance/SCHEDULER_SYNCHRONIZATION_DIRECTIVE.json")
        rec = directive["reconciliation"]
        self.assertEqual(rec["mode"], "DECLARED_MAPPING_ONLY")
        self.assertTrue(rec["automatic_repair_authorized_for_mapped_non_destructive_fields"])
        self.assertTrue(rec["never_infer_mapping_by_title_similarity"])
        self.assertTrue(rec["never_create_or_delete_frontend_task_without_explicit_binding_record"])
        self.assertTrue(rec["never_import_unmapped_personal_frontend_tasks_into_backend"])

    def test_backend_job_is_mapped_to_bootstrap_bridge(self):
        bindings = self.load("governance/SCHEDULER_FRONTEND_BINDINGS.json")["bindings"]
        mapped = [b for b in bindings if b["mode"] == "MIRROR"]
        self.assertEqual(len(mapped), 1)
        binding = mapped[0]
        self.assertEqual(binding["backend_job_id"], "global-bounded-capacity-hourly")
        self.assertEqual(binding["frontend_title"], "Bootstrap Spawn Bridge")
        self.assertEqual(binding["enabled_state_policy"], "MIRROR")

    def test_personal_and_legacy_frontend_tasks_are_not_auto_mutated(self):
        bindings = self.load("governance/SCHEDULER_FRONTEND_BINDINGS.json")["bindings"]
        for binding in bindings:
            if binding["mode"].startswith("FRONTEND_ONLY"):
                self.assertIsNone(binding["backend_job_id"])
                self.assertEqual(binding["enabled_state_policy"], "FRONTEND_ONLY")

    def test_policy_allows_only_mapped_scheduler_reconciliation(self):
        policy = self.load("governance/INTERNAL_SPAWN_SCHEDULER_POLICY.json")
        boundary = policy["scheduler_state_boundary"]
        self.assertTrue(boundary["synchronization_authorized_by_human_directive"])
        self.assertTrue(boundary["declared_mapping_required"])
        self.assertTrue(boundary["may_reconcile_mapped_chatgpt_scheduled_tasks"])
        self.assertFalse(boundary["may_modify_unmapped_chatgpt_tasks"])
        self.assertFalse(boundary["may_create_or_delete_unmapped_chatgpt_tasks"])
        self.assertFalse(boundary["may_infer_mapping_from_title_similarity"])

    def test_control_interface_has_short_commands_and_project_glance(self):
        control = self.load("governance/SCHEDULER_CONTROL_INTERFACE.json")
        commands = control["commands"]
        for command in [
            "scheduler status",
            "scheduler health",
            "scheduler reconcile",
            "scheduler pause",
            "scheduler resume",
            "scheduler run",
            "project status",
            "project status <project_id>",
            "projects refresh",
        ]:
            self.assertIn(command, commands)
        self.assertTrue(control["safety"]["unmapped_personal_tasks_cannot_be_changed_by_scheduler_commands"])
        self.assertTrue(control["safety"]["project_glance_is_not_project_authority"])
        self.assertEqual(control["surfaces"]["project_glance"]["cache"], "PROJECT_GLANCE_INDEX.json")

    def test_project_glance_interface_is_stale_aware_and_cache_first(self):
        glance = self.load("governance/PROJECT_GLANCE_INTERFACE.json")
        self.assertEqual(glance["semantics"]["authority"], "READ_ONLY_DERIVED_CACHE")
        self.assertTrue(glance["semantics"]["unknown_is_not_idle"])
        self.assertTrue(glance["semantics"]["stale_is_not_current"])
        self.assertTrue(glance["response_contract"]["do_not_requery_all_projects_when_cache_is_fresh"])
        self.assertTrue(glance["response_contract"]["deep_audit_only_when_stale_conflicting_or_requested"])


if __name__ == "__main__":
    unittest.main()
