from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.launch_admission import (
    LaunchAdmissionController,
    LaunchAdmissionError,
    LaunchAdmissionPolicy,
    LaunchAttemptState,
    deterministic_launch_offset_seconds,
)


NOW = datetime(2026, 10, 4, 10, 0, tzinfo=timezone.utc)


class LaunchAdmissionTests(unittest.TestCase):
    def test_too_many_requests_is_retryable_and_does_not_advance_task(self):
        controller = LaunchAdmissionController(
            LaunchAdmissionPolicy(
                max_inflight=1,
                min_start_interval_seconds=1,
                base_backoff_seconds=10,
                max_backoff_seconds=60,
                max_attempts=3,
                jitter_percent=0,
            )
        )
        state = LaunchAttemptState(
            project_id="intercommunicationsenhancements",
            task_id="nightly-digest",
            occurrence_id="run-001",
        )
        decision = controller.admit(state, NOW)
        self.assertTrue(decision.admitted)
        rejected = controller.provider_result(decision.state, "TOO_MANY_REQUESTS", NOW)
        self.assertEqual(rejected.status, "RETRY_WAIT")
        self.assertFalse(controller.may_advance_task_state(rejected))
        self.assertEqual(rejected.next_eligible_at, NOW + timedelta(seconds=10))

    def test_backoff_blocks_early_retry(self):
        controller = LaunchAdmissionController(
            LaunchAdmissionPolicy(
                min_start_interval_seconds=1,
                base_backoff_seconds=10,
                max_backoff_seconds=60,
                jitter_percent=0,
            )
        )
        state = LaunchAttemptState(
            project_id="intercommunicationsenhancements",
            task_id="nightly-digest",
            occurrence_id="run-001",
        )
        admitted = controller.admit(state, NOW).state
        retry = controller.provider_result(admitted, "RATE_LIMITED", NOW)
        decision = controller.admit(retry, NOW + timedelta(seconds=5))
        self.assertFalse(decision.admitted)
        self.assertEqual(decision.reason, "backoff")

    def test_concurrency_gate_blocks_second_start(self):
        controller = LaunchAdmissionController(
            LaunchAdmissionPolicy(max_inflight=1, min_start_interval_seconds=1)
        )
        first = LaunchAttemptState(
            project_id="intercommunicationsenhancements",
            task_id="task-a",
            occurrence_id="run-001",
        )
        second = LaunchAttemptState(
            project_id="intercommunicationsenhancements",
            task_id="task-b",
            occurrence_id="run-001",
        )
        self.assertTrue(controller.admit(first, NOW).admitted)
        decision = controller.admit(second, NOW)
        self.assertFalse(decision.admitted)
        self.assertEqual(decision.reason, "concurrency_limit")

    def test_task_can_advance_only_after_bootstrap_ready(self):
        controller = LaunchAdmissionController(
            LaunchAdmissionPolicy(min_start_interval_seconds=1)
        )
        state = LaunchAttemptState(
            project_id="intercommunicationsenhancements",
            task_id="nightly-digest",
            occurrence_id="run-001",
        )
        admitted = controller.admit(state, NOW).state
        accepted = controller.provider_result(admitted, "ACCEPTED", NOW)
        self.assertFalse(controller.may_advance_task_state(accepted))
        ready = controller.bootstrap_ready(accepted, NOW + timedelta(seconds=2))
        self.assertTrue(controller.may_advance_task_state(ready))
        self.assertEqual(controller.complete(ready).status, "COMPLETED")

    def test_complete_before_bootstrap_ready_is_rejected(self):
        controller = LaunchAdmissionController()
        state = LaunchAttemptState(
            project_id="intercommunicationsenhancements",
            task_id="nightly-digest",
            occurrence_id="run-001",
            status="PROVIDER_ACCEPTED",
            attempt=1,
        )
        with self.assertRaises(LaunchAdmissionError):
            controller.complete(state)

    def test_deterministic_stagger_is_stable(self):
        first = deterministic_launch_offset_seconds(
            "intercommunicationsenhancements", "nightly-digest", window_seconds=600
        )
        second = deterministic_launch_offset_seconds(
            "intercommunicationsenhancements", "nightly-digest", window_seconds=600
        )
        self.assertEqual(first, second)
        self.assertGreaterEqual(first, 0)
        self.assertLess(first, 600)


if __name__ == "__main__":
    unittest.main()
