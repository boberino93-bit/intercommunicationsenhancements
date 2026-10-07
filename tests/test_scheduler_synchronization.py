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

    def test_capacity_lanes_are_one_to_one_mapped_and_plan_limit_aware(self):
        registry = self.load("governance/INTERNAL_SPAWN_SCHEDULES.json")
        bindings = self.load("governance/SCHEDULER_FRONTEND_BINDINGS.json")["bindings"]
        jobs = registry["jobs"]
        mapped = [b for b in bindings if b["mode"] == "MIRROR"]

        self.assertEqual(registry["distribution"]["strategy"], "PLAN_LIMIT_AWARE_EVEN_12_MINUTE_STAGGER")
        self.assertEqual(registry["distribution"]["frontend_active_task_limit"], 5)
        self.assertEqual(len(jobs), 6)
        self.assertEqual(len(mapped), 6)
        self.assertEqual(sum(1 for job in jobs if job["enabled"]), 5)

        expected_active_offsets = [0, 12, 24, 36, 48]
        observed_active_offsets = sorted(
            job["schedule"]["minute_offsets"][0] for job in jobs if job["enabled"]
        )
        self.assertEqual(observed_active_offsets, expected_active_offsets)
        standby = [job for job in jobs if not job["enabled"]]
        self.assertEqual(len(standby), 1)
        self.assertEqual(standby[0]["job_id"], "global-capacity-slot-2")

        backend_ids = {job["job_id"] for job in jobs}
        mapped_ids = {binding["backend_job_id"] for binding in mapped}
        self.assertEqual(backend_ids, mapped_ids)
        self.assertEqual(len({binding["frontend_automation_id"] for binding in mapped}), 6)

        for job in jobs:
            if job["enabled"]:
                self.assertEqual(job["schedule"]["grace_minutes"], 11)
            self.assertEqual(job["max_workers_per_occurrence"], 1)
            self.assertEqual(job["execution_surface"], "CHATGPT_FRONTEND_MAPPED")
            self.assertTrue(job["primary_prohibited"])
            self.assertTrue(job["full_swarm_prohibited"])

    def test_backend_clock_spacing_dispatch_and_execution_surface_remain_governed(self):
        workflow = (ROOT / ".github/workflows/internal-spawn-scheduler.yml").read_text()
        self.assertIn('cron: "0,12,24,36,48 * * * *"', workflow)
        self.assertIn("--dispatch", workflow)
        self.assertIn("ORG_AGENT_MESH_SPAWN_ENDPOINT", workflow)
        self.assertIn("ORG_AGENT_MESH_SPAWN_TOKEN", workflow)

        policy = self.load("governance/INTERNAL_SPAWN_SCHEDULER_POLICY.json")
        self.assertTrue(policy["service"]["host_adapter_required_for_real_spawn"])
        self.assertTrue(policy["service"]["host_start_receipt_required_for_session_started"])
        delegated = policy["delegated_spawn_authority"]
        self.assertEqual(delegated["max_workers_per_occurrence"], 1)
        self.assertEqual(delegated["max_tickets_per_scheduler_invocation"], 1)
        self.assertFalse(delegated["full_swarm_auto_start_allowed"])

        surface = policy["execution_surface_isolation"]
        self.assertTrue(surface["exactly_one_execution_surface_per_occurrence"])
        self.assertFalse(surface["frontend_mapped_backend_webhook_dispatch"])
        self.assertFalse(surface["backend_host_adapter_frontend_execution"])
        self.assertTrue(surface["backend_host_dispatch_requires_explicit_execution_surface"])
        self.assertTrue(surface["duplicate_cross_surface_execution_prohibited"])

        registry = self.load("governance/INTERNAL_SPAWN_SCHEDULES.json")
        offsets = sorted(
            job["schedule"]["minute_offsets"][0]
            for job in registry["jobs"]
            if job["enabled"]
        )
        grace = registry["distribution"]["grace_minutes"]
        cyclic_gaps = [
            (offsets[(i + 1) % len(offsets)] - offsets[i]) % 60
            for i in range(len(offsets))
        ]
        self.assertTrue(all(gap == 12 for gap in cyclic_gaps))
        self.assertLess(grace, min(cyclic_gaps))

    def test_capacity_defer_and_standby_policies_are_explicit(self):
        bindings = self.load("governance/SCHEDULER_FRONTEND_BINDINGS.json")["bindings"]
        by_title = {binding["frontend_title"]: binding for binding in bindings}
        self.assertEqual(
            by_title["Swarm Capacity Slot 1"]["enabled_state_policy"],
            "MIRROR_WHEN_ACCOUNT_CAPACITY_AVAILABLE",
        )
        self.assertEqual(
            by_title["Swarm Capacity Slot 2"]["enabled_state_policy"],
            "MIRROR_DISABLED_STANDBY",
        )

    def test_personal_frontend_tasks_are_not_auto_mutated(self):
        bindings = self.load("governance/SCHEDULER_FRONTEND_BINDINGS.json")["bindings"]
        personal = [binding for binding in bindings if binding["mode"] == "FRONTEND_ONLY_PERSONAL"]
        self.assertGreaterEqual(len(personal), 1)
        for binding in personal:
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

    def test_control_interface_has_short_commands(self):
        control = self.load("governance/SCHEDULER_CONTROL_INTERFACE.json")
        commands = control["commands"]
        for command in ["scheduler status", "scheduler health", "scheduler reconcile", "scheduler pause", "scheduler resume", "scheduler run"]:
            self.assertIn(command, commands)
        self.assertTrue(control["safety"]["unmapped_personal_tasks_cannot_be_changed_by_scheduler_commands"])


if __name__ == "__main__":
    unittest.main()
