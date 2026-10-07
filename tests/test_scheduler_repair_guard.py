from datetime import datetime, timezone
import unittest

from org_agent_mesh.scheduler_repair_guard import (
    RepairGrantError,
    evaluate_repair_grant,
)

UTC = timezone.utc
ACTOR = "bridge"
TARGET = "slot-1"


class SchedulerRepairGuardTests(unittest.TestCase):
    def grant(self):
        return {
            "status": "ACTIVE",
            "issued_at": "2026-10-07T20:00:00Z",
            "expires_at": "2026-10-08T20:00:00Z",
            "allowed_transition": "DISABLED_TO_ENABLED_ONLY",
            "authorized_repair_actors": [{"frontend_automation_id": ACTOR}],
            "authorized_target_frontend_automation_ids": [TARGET, "slot-3"],
            "repair_budget": {
                "window_minutes": 180,
                "max_repairs_per_target_in_window": 2,
                "max_total_repairs_in_window": 3,
                "count_statuses": ["APPLIED_AND_VERIFIED"],
            },
        }

    def now(self):
        return datetime(2026, 10, 7, 22, 0, tzinfo=UTC)

    def event(self, target=TARGET, at="2026-10-07T21:00:00Z"):
        return {
            "observed_at": at,
            "frontend_automation_id": target,
            "resulting_enabled_state": True,
            "status": "APPLIED_AND_VERIFIED",
        }

    def test_current_exact_grant_with_budget_allows_repair(self):
        decision = evaluate_repair_grant(
            self.grant(),
            actor_frontend_automation_id=ACTOR,
            target_frontend_automation_id=TARGET,
            observed_at=self.now(),
            ledger_events=[],
        )
        self.assertTrue(decision.allowed)
        self.assertFalse(decision.quarantine_required)

    def test_expired_grant_fails_closed(self):
        decision = evaluate_repair_grant(
            self.grant(),
            actor_frontend_automation_id=ACTOR,
            target_frontend_automation_id=TARGET,
            observed_at=datetime(2026, 10, 8, 20, 0, tzinfo=UTC),
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "REPAIR_GRANT_EXPIRED")

    def test_wrong_actor_or_target_is_denied(self):
        actor = evaluate_repair_grant(
            self.grant(),
            actor_frontend_automation_id="ordinary-worker",
            target_frontend_automation_id=TARGET,
            observed_at=self.now(),
        )
        target = evaluate_repair_grant(
            self.grant(),
            actor_frontend_automation_id=ACTOR,
            target_frontend_automation_id="personal-task",
            observed_at=self.now(),
        )
        self.assertEqual(actor.reason, "REPAIR_ACTOR_NOT_AUTHORIZED")
        self.assertEqual(target.reason, "REPAIR_TARGET_NOT_AUTHORIZED")

    def test_per_target_budget_exhaustion_requires_quarantine(self):
        events = [
            self.event(at="2026-10-07T20:30:00Z"),
            self.event(at="2026-10-07T21:30:00Z"),
        ]
        decision = evaluate_repair_grant(
            self.grant(),
            actor_frontend_automation_id=ACTOR,
            target_frontend_automation_id=TARGET,
            observed_at=self.now(),
            ledger_events=events,
        )
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.quarantine_required)
        self.assertEqual(decision.reason, "REPAIR_TARGET_BUDGET_EXHAUSTED")

    def test_global_budget_exhaustion_requires_quarantine(self):
        grant = self.grant()
        grant["repair_budget"]["max_repairs_per_target_in_window"] = 3
        events = [
            self.event(target=TARGET, at="2026-10-07T20:30:00Z"),
            self.event(target="slot-3", at="2026-10-07T21:00:00Z"),
            self.event(target="slot-3", at="2026-10-07T21:30:00Z"),
        ]
        decision = evaluate_repair_grant(
            grant,
            actor_frontend_automation_id=ACTOR,
            target_frontend_automation_id=TARGET,
            observed_at=self.now(),
            ledger_events=events,
        )
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.quarantine_required)
        self.assertEqual(decision.reason, "REPAIR_GLOBAL_BUDGET_EXHAUSTED")

    def test_future_ledger_event_is_rejected(self):
        with self.assertRaises(RepairGrantError):
            evaluate_repair_grant(
                self.grant(),
                actor_frontend_automation_id=ACTOR,
                target_frontend_automation_id=TARGET,
                observed_at=self.now(),
                ledger_events=[self.event(at="2026-10-07T23:00:00Z")],
            )


if __name__ == "__main__":
    unittest.main()
