import unittest

from org_agent_mesh.schedule_activation import ActivationActor
from org_agent_mesh.scheduler_reconciliation import (
    FrontendTaskHealth,
    ReconciliationAction,
    ReconciliationRequest,
    decide_frontend_reconciliation,
)


class SchedulerReconciliationTests(unittest.TestCase):
    def test_capacity_release_does_not_auto_enable_without_repair_authorization(self):
        decision = decide_frontend_reconciliation(
            ReconciliationRequest(
                task_id="slot-1",
                current_enabled=False,
                backend_enabled=True,
                enabled_state_policy="MIRROR_WHEN_ACCOUNT_CAPACITY_AVAILABLE",
                account_capacity_available=True,
                actor=ActivationActor.SYSTEM,
            )
        )
        self.assertEqual(decision.action, ReconciliationAction.ENABLE_AUTHORIZATION_REQUIRED)
        self.assertFalse(decision.may_mutate_frontend)
        self.assertFalse(decision.resulting_enabled)

    def test_declared_repair_actor_with_human_authorization_may_restore_mapped_task(self):
        decision = decide_frontend_reconciliation(
            ReconciliationRequest(
                task_id="slot-1",
                current_enabled=False,
                backend_enabled=True,
                enabled_state_policy="MIRROR_WHEN_ACCOUNT_CAPACITY_AVAILABLE",
                account_capacity_available=True,
                actor=ActivationActor.RECOVERY,
                declared_repair_actor=True,
                repair_authorization_ref="governance/SCHEDULER_ACTIVATION_GRANT_2026-10-07.json",
                repair_scope_contains_task=True,
            )
        )
        self.assertEqual(decision.action, ReconciliationAction.ENABLE_AUTHORIZED)
        self.assertTrue(decision.may_mutate_frontend)
        self.assertTrue(decision.resulting_enabled)

    def test_repair_actor_without_scope_match_cannot_enable(self):
        decision = decide_frontend_reconciliation(
            ReconciliationRequest(
                task_id="unmapped-or-paused",
                current_enabled=False,
                backend_enabled=True,
                enabled_state_policy="MIRROR",
                actor=ActivationActor.RECOVERY,
                declared_repair_actor=True,
                repair_authorization_ref="governance/SCHEDULER_ACTIVATION_GRANT_2026-10-07.json",
                repair_scope_contains_task=False,
            )
        )
        self.assertEqual(decision.action, ReconciliationAction.ENABLE_AUTHORIZATION_REQUIRED)
        self.assertFalse(decision.may_mutate_frontend)
        self.assertFalse(decision.resulting_enabled)

    def test_explicit_current_human_request_may_enable(self):
        decision = decide_frontend_reconciliation(
            ReconciliationRequest(
                task_id="slot-1",
                current_enabled=False,
                backend_enabled=True,
                enabled_state_policy="MIRROR_WHEN_ACCOUNT_CAPACITY_AVAILABLE",
                account_capacity_available=True,
                actor=ActivationActor.USER,
                explicit_human_request=True,
            )
        )
        self.assertEqual(decision.action, ReconciliationAction.ENABLE_AUTHORIZED)
        self.assertTrue(decision.may_mutate_frontend)
        self.assertTrue(decision.resulting_enabled)

    def test_capacity_full_is_deferred_without_attempting_activation(self):
        decision = decide_frontend_reconciliation(
            ReconciliationRequest(
                task_id="slot-1",
                current_enabled=False,
                backend_enabled=True,
                enabled_state_policy="MIRROR_WHEN_ACCOUNT_CAPACITY_AVAILABLE",
                account_capacity_available=False,
            )
        )
        self.assertEqual(decision.action, ReconciliationAction.CAPACITY_LIMIT_DEFERRED)
        self.assertFalse(decision.may_mutate_frontend)

    def test_missing_identity_requires_explicit_replacement_authorization(self):
        decision = decide_frontend_reconciliation(
            ReconciliationRequest(
                task_id="slot-3",
                current_enabled=True,
                backend_enabled=True,
                enabled_state_policy="MIRROR",
                health=FrontendTaskHealth.MISSING,
            )
        )
        self.assertEqual(decision.action, ReconciliationAction.REPLACEMENT_AUTHORIZATION_REQUIRED)
        self.assertFalse(decision.may_mutate_frontend)

    def test_unavailable_identity_requires_explicit_replacement_authorization(self):
        decision = decide_frontend_reconciliation(
            ReconciliationRequest(
                task_id="slot-5",
                current_enabled=True,
                backend_enabled=True,
                enabled_state_policy="MIRROR",
                health=FrontendTaskHealth.UNAVAILABLE,
            )
        )
        self.assertEqual(decision.action, ReconciliationAction.REPLACEMENT_AUTHORIZATION_REQUIRED)
        self.assertFalse(decision.may_mutate_frontend)

    def test_stale_execution_is_reported_not_replaced(self):
        decision = decide_frontend_reconciliation(
            ReconciliationRequest(
                task_id="slot-4",
                current_enabled=True,
                backend_enabled=True,
                enabled_state_policy="MIRROR",
                health=FrontendTaskHealth.STALE,
            )
        )
        self.assertEqual(decision.action, ReconciliationAction.STALE_EXECUTION_REPORTED)
        self.assertFalse(decision.may_mutate_frontend)

    def test_system_may_disable_mirror_for_containment(self):
        decision = decide_frontend_reconciliation(
            ReconciliationRequest(
                task_id="slot-4",
                current_enabled=True,
                backend_enabled=False,
                enabled_state_policy="MIRROR",
                actor=ActivationActor.SYSTEM,
            )
        )
        self.assertEqual(decision.action, ReconciliationAction.DISABLE_AUTHORIZED)
        self.assertTrue(decision.may_mutate_frontend)
        self.assertFalse(decision.resulting_enabled)

    def test_standby_remains_disabled(self):
        decision = decide_frontend_reconciliation(
            ReconciliationRequest(
                task_id="slot-2",
                current_enabled=False,
                backend_enabled=True,
                enabled_state_policy="MIRROR_DISABLED_STANDBY",
            )
        )
        self.assertEqual(decision.action, ReconciliationAction.NO_STATE_CHANGE)
        self.assertFalse(decision.resulting_enabled)

    def test_frontend_only_task_is_not_reconciled(self):
        decision = decide_frontend_reconciliation(
            ReconciliationRequest(
                task_id="personal",
                current_enabled=True,
                backend_enabled=False,
                enabled_state_policy="FRONTEND_ONLY",
            )
        )
        self.assertEqual(decision.action, ReconciliationAction.NO_STATE_CHANGE)
        self.assertFalse(decision.may_mutate_frontend)
        self.assertTrue(decision.resulting_enabled)


if __name__ == "__main__":
    unittest.main()
