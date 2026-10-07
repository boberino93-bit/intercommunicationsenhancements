from datetime import datetime, timezone
import unittest

from org_agent_mesh.internal_scheduler import (
    BootstrapInternalScheduler,
    HostLaunchReceipt,
    InternalScheduleSpec,
    InternalSchedulerError,
)


UTC = timezone.utc


class AcceptedAdapter:
    def submit(self, ticket):
        return HostLaunchReceipt(
            ticket_id=ticket.ticket_id,
            provider_result="ACCEPTED",
            session_started=True,
            external_execution_id="exec-1",
        )


class RateLimitedAdapter:
    def submit(self, ticket):
        return HostLaunchReceipt(
            ticket_id=ticket.ticket_id,
            provider_result="RATE_LIMITED",
            session_started=False,
        )


class InternalSchedulerTests(unittest.TestCase):
    def _spec(self, **kwargs):
        base = dict(
            schedule_id="capacity-slot-2",
            project_id="intercommunicationsenhancements",
            task_id="bounded-research-unit",
            role_id="research",
            interval_seconds=3600,
            next_due_at=datetime(2026, 10, 7, 10, 0, tzinfo=UTC),
        )
        base.update(kwargs)
        return InternalScheduleSpec(**base)

    def test_due_schedule_emits_spawn_ticket_not_session(self):
        scheduler = BootstrapInternalScheduler()
        scheduler.register(self._spec())
        emitted = scheduler.tick(datetime(2026, 10, 7, 10, 0, tzinfo=UTC))
        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0].state, "READY_FOR_HOST_ADMISSION")
        self.assertFalse(emitted[0].session_started)
        self.assertFalse(emitted[0].authority_conveyed)

    def test_missed_hourly_boundaries_coalesce_to_latest(self):
        scheduler = BootstrapInternalScheduler()
        scheduler.register(self._spec())
        emitted = scheduler.tick(datetime(2026, 10, 7, 13, 35, tzinfo=UTC))
        self.assertEqual(len(emitted), 1)
        self.assertEqual(
            emitted[0].scheduled_for,
            datetime(2026, 10, 7, 13, 0, tzinfo=UTC),
        )
        self.assertEqual(
            scheduler.schedules[0].next_due_at,
            datetime(2026, 10, 7, 14, 0, tzinfo=UTC),
        )

    def test_same_boundary_is_idempotent(self):
        scheduler = BootstrapInternalScheduler()
        scheduler.register(self._spec())
        first = scheduler.tick(datetime(2026, 10, 7, 10, 0, tzinfo=UTC))
        second = scheduler.tick(datetime(2026, 10, 7, 10, 0, tzinfo=UTC))
        self.assertEqual(len(first), 1)
        self.assertEqual(second, ())
        self.assertEqual(len(scheduler.tickets), 1)

    def test_pending_ticket_prevents_restart_stampede(self):
        scheduler = BootstrapInternalScheduler()
        scheduler.register(self._spec())
        scheduler.tick(datetime(2026, 10, 7, 10, 0, tzinfo=UTC))
        emitted = scheduler.tick(datetime(2026, 10, 7, 15, 0, tzinfo=UTC))
        self.assertEqual(emitted, ())
        self.assertEqual(len(scheduler.tickets), 1)

    def test_disabled_schedule_emits_nothing(self):
        scheduler = BootstrapInternalScheduler()
        scheduler.register(self._spec(enabled=False))
        self.assertEqual(
            scheduler.tick(datetime(2026, 10, 7, 12, 0, tzinfo=UTC)),
            (),
        )

    def test_disabled_to_enabled_requires_explicit_human_action(self):
        scheduler = BootstrapInternalScheduler()
        scheduler.register(self._spec(enabled=False))
        with self.assertRaises(InternalSchedulerError):
            scheduler.set_enabled(
                "capacity-slot-2",
                True,
                explicit_human_action=False,
            )
        scheduler.set_enabled(
            "capacity-slot-2",
            True,
            explicit_human_action=True,
        )
        self.assertTrue(scheduler.schedules[0].enabled)

    def test_primary_creation_is_rejected(self):
        with self.assertRaises(InternalSchedulerError):
            self._spec(role_id="primary")

    def test_missing_host_adapter_is_explicit_not_fake_success(self):
        scheduler = BootstrapInternalScheduler()
        scheduler.register(self._spec())
        ticket = scheduler.tick(datetime(2026, 10, 7, 10, 0, tzinfo=UTC))[0]
        result = scheduler.dispatch(
            ticket.ticket_id,
            datetime(2026, 10, 7, 10, 0, 1, tzinfo=UTC),
            None,
        )
        self.assertEqual(result.state, "HOST_SPAWN_ADAPTER_REQUIRED")
        self.assertFalse(result.session_started)

    def test_host_acceptance_then_bootstrap_ready_then_completion(self):
        scheduler = BootstrapInternalScheduler()
        scheduler.register(self._spec())
        ticket = scheduler.tick(datetime(2026, 10, 7, 10, 0, tzinfo=UTC))[0]
        accepted = scheduler.dispatch(
            ticket.ticket_id,
            datetime(2026, 10, 7, 10, 0, 1, tzinfo=UTC),
            AcceptedAdapter(),
        )
        self.assertEqual(accepted.state, "PROVIDER_ACCEPTED")
        self.assertTrue(accepted.session_started)
        ready = scheduler.mark_bootstrap_ready(
            ticket.ticket_id,
            datetime(2026, 10, 7, 10, 0, 2, tzinfo=UTC),
        )
        self.assertEqual(ready.state, "BOOTSTRAP_READY")
        completed = scheduler.mark_completed(ticket.ticket_id)
        self.assertEqual(completed.state, "COMPLETED")

    def test_rate_limit_enters_retry_wait_without_session(self):
        scheduler = BootstrapInternalScheduler()
        scheduler.register(self._spec())
        ticket = scheduler.tick(datetime(2026, 10, 7, 10, 0, tzinfo=UTC))[0]
        result = scheduler.dispatch(
            ticket.ticket_id,
            datetime(2026, 10, 7, 10, 0, 1, tzinfo=UTC),
            RateLimitedAdapter(),
        )
        self.assertEqual(result.state, "RETRY_WAIT")
        self.assertFalse(result.session_started)
        self.assertIsNotNone(result.next_eligible_at)

    def test_snapshot_preserves_truth_invariants(self):
        scheduler = BootstrapInternalScheduler()
        scheduler.register(self._spec())
        scheduler.tick(datetime(2026, 10, 7, 10, 0, tzinfo=UTC))
        snapshot = scheduler.snapshot()
        self.assertEqual(snapshot["schema"], "org-agent-mesh/internal-scheduler-state/v1")
        self.assertFalse(snapshot["invariants"]["spawn_ticket_is_session_started"])
        self.assertFalse(snapshot["invariants"]["schedule_fire_is_mutation_authority"])
        self.assertFalse(snapshot["invariants"]["primary_creation_allowed"])


if __name__ == "__main__":
    unittest.main()
