from datetime import datetime, timedelta, timezone
import unittest

from swarm_kernel.kernel import (
    ProjectConfig,
    backpressure_state,
    can_open_start_gate,
    circuit_state,
    convergence_gate,
    lease_transition_allowed,
    new_lease,
    preflight,
    record_path,
    validate_binding,
)


CFG = ProjectConfig("example", "owner/example", "main", "Example-AgentBus/")


class SwarmKernelTest(unittest.TestCase):
    def test_binding(self):
        with self.assertRaises(PermissionError):
            validate_binding(CFG, "other", "owner/example")

    def test_paths_and_gate(self):
        self.assertEqual(record_path("leases", "run_1", "task_1"), ".swarm/leases/run_1/task_1.json")
        with self.assertRaises(ValueError):
            record_path("leases", "../run", "task")
        self.assertFalse(can_open_start_gate(["a", "b"], ["a"])[0])

    def test_lease_and_gates(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        lease = new_lease(CFG, "run_1", "task", "a", 0, now)
        self.assertEqual(lease["version"], 1)
        self.assertEqual(lease_transition_allowed(lease, 1, "b", now)[1], "LEASE_HELD")
        self.assertEqual(
            lease_transition_allowed(lease, 1, "b", now + timedelta(seconds=1801))[1],
            "EXPIRED_RECLAIM",
        )
        self.assertEqual(circuit_state(CFG, 3), "DEGRADED_READ_ONLY")
        self.assertEqual(backpressure_state(CFG, 15), "HARD_STOP_SECONDARY_WORK")

    def test_preflight_convergence(self):
        checks = {
            "identity_binding": True,
            "run_epoch": True,
            "role_binding": True,
            "package_parity": True,
            "recovery_state": True,
            "manager_presence": True,
            "foreign_write_policy": True,
            "tests": False,
        }
        self.assertFalse(preflight(CFG, checks)["ready"])
        self.assertFalse(
            convergence_gate(
                research_accounted=True,
                manager_dispositions_complete=True,
                primary_decisions_persisted=True,
                package_parity_restored=True,
                unresolved_leases=1,
                recovery_checkpoint_valid=True,
            )["complete"]
        )


if __name__ == "__main__":
    unittest.main()
