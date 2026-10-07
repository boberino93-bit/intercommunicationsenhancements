from datetime import datetime, timezone
import json
import tempfile
import unittest
from pathlib import Path

from org_agent_mesh.internal_scheduler import (
    DispatchResult,
    InternalSchedulerError,
    ScheduleJob,
    WebhookSpawnAdapter,
    dispatch_ticket,
    due_boundary,
    evaluate_registry,
    make_ticket,
    run_once,
)


class _ReceiptAdapter:
    def dispatch(self, ticket):
        return DispatchResult(
            "SESSION_STARTED_VERIFIED",
            "HOST_START_RECEIPT_VERIFIED",
            f"receipt:{ticket.occurrence_id}",
        )


class InternalSchedulerTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 7, 12, 7, tzinfo=timezone.utc)
        self.job = ScheduleJob(
            job_id="bounded",
            enabled=True,
            minute_offsets=(5,),
            grace_minutes=10,
            launch_scope="GLOBAL_DEMAND_ROUTED_CAPACITY",
            requested_roles=("research", "manager"),
        )

    def test_due_boundary_uses_latest_boundary_inside_grace(self):
        boundary = due_boundary(self.job, self.now)
        self.assertEqual(boundary, datetime(2026, 10, 7, 12, 5, tzinfo=timezone.utc))

    def test_missed_old_boundary_is_not_replayed(self):
        late = datetime(2026, 10, 7, 12, 20, tzinfo=timezone.utc)
        self.assertIsNone(due_boundary(self.job, late))

    def test_ticket_identity_is_deterministic_for_occurrence(self):
        boundary = due_boundary(self.job, self.now)
        one = make_ticket(self.job, boundary, self.now)
        two = make_ticket(self.job, boundary, self.now)
        self.assertEqual(one.occurrence_id, two.occurrence_id)
        self.assertEqual(one.ticket_id, two.ticket_id)
        self.assertFalse(one.authority_conveyed)
        self.assertFalse(one.mutation_authority_conveyed)

    def test_primary_cannot_enter_schedule_registry(self):
        raw = {
            "job_id": "bad",
            "enabled": True,
            "schedule": {"type": "HOURLY_MINUTE_OFFSETS", "minute_offsets": [5], "grace_minutes": 10},
            "launch_scope": "GLOBAL",
            "requested_roles": ["primary"],
            "max_workers_per_occurrence": 1,
            "primary_prohibited": True,
        }
        with self.assertRaises(InternalSchedulerError):
            ScheduleJob.from_dict(raw)

    def test_registry_coalesces_to_one_current_occurrence(self):
        registry = {
            "catch_up_policy": "COALESCE_TO_LATEST",
            "jobs": [
                {
                    "job_id": "bounded",
                    "enabled": True,
                    "schedule": {"type": "HOURLY_MINUTE_OFFSETS", "minute_offsets": [5], "grace_minutes": 10},
                    "launch_scope": "GLOBAL_DEMAND_ROUTED_CAPACITY",
                    "requested_roles": ["research", "manager"],
                    "max_workers_per_occurrence": 1,
                    "primary_prohibited": True,
                }
            ],
        }
        tickets = evaluate_registry(registry, self.now)
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0].scheduled_for, "2026-10-07T12:05:00Z")

    def test_start_is_verified_only_from_adapter_receipt(self):
        boundary = due_boundary(self.job, self.now)
        ticket = make_ticket(self.job, boundary, self.now)
        final = dispatch_ticket(ticket, _ReceiptAdapter())
        self.assertEqual(final.status, "SESSION_STARTED_VERIFIED")
        self.assertTrue(final.host_start_receipt.startswith("receipt:"))

    def test_unconfigured_webhook_adapter_reports_unavailable(self):
        boundary = due_boundary(self.job, self.now)
        ticket = make_ticket(self.job, boundary, self.now)
        result = WebhookSpawnAdapter(endpoint=None, token=None).dispatch(ticket)
        self.assertEqual(result.status, "SPAWN_ADAPTER_UNAVAILABLE")
        self.assertIsNone(result.host_start_receipt)

    def test_run_once_dispatches_and_records_verified_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "registry.json"
            policy = root / "policy.json"
            out = root / "out"
            registry.write_text(json.dumps({
                "catch_up_policy": "COALESCE_TO_LATEST",
                "jobs": [
                    {
                        "job_id": "bounded",
                        "enabled": True,
                        "schedule": {
                            "type": "HOURLY_MINUTE_OFFSETS",
                            "minute_offsets": [5],
                            "grace_minutes": 10,
                        },
                        "launch_scope": "GLOBAL_DEMAND_ROUTED_CAPACITY",
                        "requested_roles": ["research", "manager"],
                        "max_workers_per_occurrence": 1,
                        "primary_prohibited": True,
                    }
                ],
            }))
            policy.write_text(json.dumps({
                "service": {"enabled": True},
                "delegated_spawn_authority": {
                    "primary_allowed": False,
                    "master_allowed": False,
                    "max_tickets_per_scheduler_invocation": 1,
                },
            }))
            result = run_once(
                registry,
                policy,
                out,
                self.now,
                dispatch=True,
                adapter=_ReceiptAdapter(),
            )
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].status, "SESSION_STARTED_VERIFIED")
            self.assertTrue(result[0].host_start_receipt.startswith("receipt:"))
            summary = json.loads((out / "run-summary.json").read_text())
            self.assertTrue(summary["dispatch_requested"])
            self.assertEqual(summary["verified_start_count"], 1)
            self.assertEqual(summary["adapter_unavailable_count"], 0)
            self.assertEqual(summary["adapter_rejected_count"], 0)

    def test_policy_disabled_emits_no_tickets_but_writes_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "registry.json"
            policy = root / "policy.json"
            out = root / "out"
            registry.write_text(json.dumps({"catch_up_policy": "COALESCE_TO_LATEST", "jobs": []}))
            policy.write_text(json.dumps({
                "service": {"enabled": False},
                "delegated_spawn_authority": {
                    "primary_allowed": False,
                    "master_allowed": False,
                    "max_tickets_per_scheduler_invocation": 3,
                },
            }))
            result = run_once(registry, policy, out, self.now, dispatch=False)
            self.assertEqual(result, [])
            summary = json.loads((out / "run-summary.json").read_text())
            self.assertEqual(summary["due_ticket_count"], 0)
            self.assertEqual(summary["verified_start_count"], 0)


if __name__ == "__main__":
    unittest.main()
