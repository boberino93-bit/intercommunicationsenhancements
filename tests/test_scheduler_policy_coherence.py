from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SchedulerPolicyCoherenceTests(unittest.TestCase):
    def load(self, path):
        return json.loads((ROOT / path).read_text())

    def test_global_activation_gate_remains_closed_except_scoped_human_repair_grant(self):
        entrypoint = self.load("GLOBAL_AGENT_ENTRYPOINT.json")
        directive = self.load("governance/SCHEDULER_SYNCHRONIZATION_DIRECTIVE.json")
        policy = self.load("governance/INTERNAL_SPAWN_SCHEDULER_POLICY.json")
        grant = self.load("governance/SCHEDULER_ACTIVATION_GRANT_2026-10-07.json")

        # General self-activation remains prohibited. The liveness path is not a general
        # recovery capability: it is an exact-target exception backed by this explicit
        # current human authorization grant.
        global_activation = entrypoint["scheduled_task_activation_policy"]
        self.assertFalse(global_activation["automatic_reenable"])
        self.assertFalse(global_activation["recovery_may_enable"])
        self.assertFalse(global_activation["migration_or_alignment_may_enable"])

        reconciliation = directive["reconciliation"]
        self.assertNotIn("enabled_state_when_binding_policy_authorizes_it", reconciliation["automatic_fields"])
        self.assertTrue(
            reconciliation["disabled_to_enabled_requires_direct_human_enablement_or_active_scoped_human_repair_grant"]
        )
        self.assertTrue(reconciliation["capacity_availability_is_not_activation_authorization"])
        self.assertTrue(reconciliation["capacity_release_alone_does_not_enable_task"])
        self.assertTrue(reconciliation["mirror_policy_may_auto_enable_only_under_active_scoped_human_repair_grant"])

        boundary = policy["scheduler_state_boundary"]
        self.assertTrue(boundary["may_enable_mapped_chatgpt_task_when_binding_policy_is_MIRROR"])
        self.assertTrue(
            boundary["may_enable_mapped_chatgpt_task_when_binding_policy_is_MIRROR_WHEN_ACCOUNT_CAPACITY_AVAILABLE"]
        )
        self.assertTrue(boundary["enable_repair_requires_active_scoped_human_authorization"])
        self.assertTrue(
            boundary["disabled_to_enabled_requires_direct_human_request_or_active_scoped_human_repair_grant"]
        )
        self.assertTrue(boundary["capacity_availability_is_not_activation_authorization"])
        self.assertTrue(boundary["capacity_deferred_enablement_may_retry_after_capacity_release_under_active_repair_grant"])
        self.assertEqual(
            boundary["capacity_release_action"],
            "RETRY_IF_ACTIVE_SCOPED_HUMAN_REPAIR_GRANT_ELSE_REPORT_READY_FOR_HUMAN_ENABLEMENT",
        )

        self.assertEqual(grant["allowed_transition"], "DISABLED_TO_ENABLED_ONLY")
        self.assertTrue(grant["required_conditions"]["exact_declared_binding_required"])
        self.assertTrue(grant["required_conditions"]["canonical_backend_enabled_required"])
        self.assertTrue(grant["required_conditions"]["account_capacity_available_required"])
        self.assertTrue(grant["prohibited_targets"]["mirror_disabled_standby"])
        self.assertTrue(grant["prohibited_targets"]["frontend_only_personal"])
        self.assertFalse(grant["mutation_limits"]["create_task"])
        self.assertFalse(grant["mutation_limits"]["replace_task"])

    def test_capacity_binding_can_retry_only_under_scoped_repair_grant(self):
        bindings = self.load("governance/SCHEDULER_FRONTEND_BINDINGS.json")
        slot1 = next(b for b in bindings["bindings"] if b["binding_id"] == "capacity-slot-1-frontend")
        self.assertEqual(slot1["enabled_state_policy"], "MIRROR_WHEN_ACCOUNT_CAPACITY_AVAILABLE")
        self.assertEqual(
            slot1["capacity_release_action"],
            "RETRY_ONLY_UNDER_ACTIVE_SCOPED_HUMAN_REPAIR_GRANT",
        )
        self.assertEqual(slot1["liveness_repair_role"], "SECONDARY_LIVENESS_SENTINEL")
        self.assertEqual(slot1["repair_authorization_ref"], bindings["activation_grant"])
        self.assertIn("Capacity availability alone never grants activation", slot1["capacity_note"])

    def test_dead_identity_replacement_is_human_gated(self):
        directive = self.load("governance/SCHEDULER_SYNCHRONIZATION_DIRECTIVE.json")
        policy = self.load("governance/INTERNAL_SPAWN_SCHEDULER_POLICY.json")
        bindings = self.load("governance/SCHEDULER_FRONTEND_BINDINGS.json")

        reconciliation = directive["reconciliation"]
        self.assertEqual(
            reconciliation["missing_or_unavailable_identity_disposition"],
            "REPLACEMENT_AUTHORIZATION_REQUIRED",
        )
        self.assertTrue(reconciliation["replacement_requires_explicit_current_human_authorization"])
        self.assertTrue(
            reconciliation["replacement_must_preserve_enabled_state_unless_activation_is_separately_authorized"]
        )

        boundary = policy["scheduler_state_boundary"]
        self.assertTrue(boundary["missing_mapped_task_requires_human_replacement_authorization"])
        self.assertTrue(boundary["unavailable_mapped_task_requires_human_replacement_authorization"])
        self.assertTrue(boundary["stale_execution_is_not_replacement_authority"])

        health = bindings["identity_health_policy"]
        self.assertTrue(health["probe_by_declared_frontend_automation_id"])
        self.assertTrue(health["missing_or_unavailable_requires_explicit_human_replacement_authorization"])
        self.assertTrue(health["stale_execution_is_report_only"])
        self.assertTrue(health["title_similarity_does_not_establish_identity"])


if __name__ == "__main__":
    unittest.main()
