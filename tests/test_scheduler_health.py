from datetime import datetime, timezone
import unittest

from org_agent_mesh.scheduler_health import evaluate_scheduler_health

UTC = timezone.utc


class SchedulerHealthTests(unittest.TestCase):
    def setUp(self):
        self.registry = {
            "jobs": [
                {
                    "job_id": "lane-a",
                    "enabled": True,
                    "execution_surface": "CHATGPT_FRONTEND_MAPPED",
                    "schedule": {"type": "HOURLY_MINUTE_OFFSETS", "minute_offsets": [12], "grace_minutes": 11},
                },
                {
                    "job_id": "standby",
                    "enabled": False,
                    "execution_surface": "CHATGPT_FRONTEND_MAPPED",
                    "schedule": {"type": "HOURLY_MINUTE_OFFSETS", "minute_offsets": [6], "grace_minutes": 5},
                },
            ]
        }
        self.bindings = {
            "bindings": [
                {
                    "binding_id": "lane-a-frontend",
                    "backend_job_id": "lane-a",
                    "frontend_automation_id": "task-a",
                },
                {
                    "binding_id": "standby-frontend",
                    "backend_job_id": "standby",
                    "frontend_automation_id": "task-standby",
                },
            ]
        }
        self.policy = {
            "required_consecutive_verified_occurrences": 3,
            "receipt_acceptance_window_minutes": 30,
            "receipt_persistence_grace_minutes": 5,
            "health_evidence_deadline_minutes": 35,
        }
        self.now = datetime(2026, 10, 7, 21, 30, tzinfo=UTC)

    def audit(self, occurrence_ids):
        return {"accepted_receipts": [{"occurrence_id": value} for value in occurrence_ids]}

    def test_zero_receipts_is_degraded_not_success(self):
        report = evaluate_scheduler_health(
            registry=self.registry,
            bindings=self.bindings,
            receipt_audit=self.audit([]),
            policy=self.policy,
            observed_at=self.now,
        )
        self.assertEqual(report["overall_state"], "DEGRADED")
        self.assertEqual(report["unhealthy_lane_count"], 1)
        self.assertEqual(report["lanes"][0]["state"], "DEGRADED_MISSING_EXECUTION_EVIDENCE")
        self.assertEqual(report["lanes"][0]["latest_mature_occurrence_id"], "lane-a:20261007T2012Z")
        self.assertEqual(report["lanes"][0]["health_evidence_deadline_minutes"], 35)

    def test_current_occurrence_inside_receipt_deadline_does_not_false_degrade(self):
        report = evaluate_scheduler_health(
            registry=self.registry,
            bindings=self.bindings,
            receipt_audit=self.audit([
                "lane-a:20261007T2012Z",
                "lane-a:20261007T1912Z",
                "lane-a:20261007T1812Z",
            ]),
            policy=self.policy,
            observed_at=self.now,
        )
        self.assertEqual(report["overall_state"], "HEALTHY")
        self.assertNotIn("lane-a:20261007T2112Z", report["lanes"][0]["evaluated_occurrence_ids"])

    def test_one_success_is_recovering_not_healthy(self):
        report = evaluate_scheduler_health(
            registry=self.registry,
            bindings=self.bindings,
            receipt_audit=self.audit(["lane-a:20261007T2012Z"]),
            policy=self.policy,
            observed_at=self.now,
        )
        self.assertEqual(report["overall_state"], "DEGRADED")
        self.assertEqual(report["lanes"][0]["state"], "RECOVERING")
        self.assertEqual(report["lanes"][0]["verified_consecutive_occurrences"], 1)

    def test_three_consecutive_mature_occurrences_qualify_health(self):
        report = evaluate_scheduler_health(
            registry=self.registry,
            bindings=self.bindings,
            receipt_audit=self.audit([
                "lane-a:20261007T2012Z",
                "lane-a:20261007T1912Z",
                "lane-a:20261007T1812Z",
            ]),
            policy=self.policy,
            observed_at=self.now,
        )
        self.assertEqual(report["overall_state"], "HEALTHY")
        self.assertTrue(report["lanes"][0]["healthy"])

    def test_latest_missing_breaks_health_even_when_older_are_verified(self):
        report = evaluate_scheduler_health(
            registry=self.registry,
            bindings=self.bindings,
            receipt_audit=self.audit([
                "lane-a:20261007T1912Z",
                "lane-a:20261007T1812Z",
                "lane-a:20261007T1712Z",
            ]),
            policy=self.policy,
            observed_at=self.now,
        )
        self.assertEqual(report["overall_state"], "DEGRADED")
        self.assertEqual(report["lanes"][0]["verified_consecutive_occurrences"], 0)

    def test_disabled_standby_is_excluded(self):
        report = evaluate_scheduler_health(
            registry=self.registry,
            bindings=self.bindings,
            receipt_audit=self.audit([
                "lane-a:20261007T2012Z",
                "lane-a:20261007T1912Z",
                "lane-a:20261007T1812Z",
            ]),
            policy=self.policy,
            observed_at=self.now,
        )
        self.assertEqual(report["lane_count"], 1)
        self.assertEqual(report["lanes"][0]["job_id"], "lane-a")

    def test_deadline_shorter_than_receipt_sla_fails_closed_as_unqualified(self):
        policy = dict(self.policy)
        policy["health_evidence_deadline_minutes"] = 20
        report = evaluate_scheduler_health(
            registry=self.registry,
            bindings=self.bindings,
            receipt_audit=self.audit([]),
            policy=policy,
            observed_at=self.now,
        )
        self.assertEqual(report["overall_state"], "DEGRADED")
        self.assertEqual(report["lanes"][0]["state"], "UNQUALIFIED")
        self.assertIn("receipt acceptance", report["lanes"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
