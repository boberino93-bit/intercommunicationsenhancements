from datetime import datetime, timedelta, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.control_plane import (
    AgentLifecycleError,
    AgentSession,
    inherit_child_binding,
    LeaseConflict,
    LeaseRegistry,
    ProjectLifecycleError,
    ProjectRegistry,
    StaleVersion,
    VersionedStateStore,
)
from org_agent_mesh.project_scope import ProjectBinding, ProjectScopeError


class ControlPlaneTest(unittest.TestCase):
    def test_same_named_resources_do_not_collide_across_projects(self):
        leases = LeaseRegistry()
        a = leases.claim("a", "a", "task-001", "worker-a", ttl_seconds=30)
        b = leases.claim("b", "b", "task-001", "worker-b", ttl_seconds=30)
        self.assertNotEqual(a.lease_id, b.lease_id)
        self.assertEqual(a.resource_id, b.resource_id)

    def test_foreign_lease_claim_denied(self):
        with self.assertRaises(ProjectScopeError):
            LeaseRegistry().claim("a", "b", "task-001", "worker-a")

    def test_duplicate_claim_by_same_instance_is_idempotent(self):
        leases = LeaseRegistry()
        first = leases.claim("a", "a", "task-001", "worker-a", ttl_seconds=30)
        second = leases.claim("a", "a", "task-001", "worker-a", ttl_seconds=30)
        self.assertEqual(first, second)

    def test_competing_active_lease_is_denied(self):
        leases = LeaseRegistry()
        leases.claim("a", "a", "task-001", "worker-a", ttl_seconds=30)
        with self.assertRaises(LeaseConflict):
            leases.claim("a", "a", "task-001", "worker-b", ttl_seconds=30)

    def test_concurrent_claim_has_one_effective_holder(self):
        leases = LeaseRegistry()
        def attempt(holder):
            try:
                return leases.claim("a", "a", "task-001", holder, ttl_seconds=30).holder_agent_instance_id
            except LeaseConflict:
                return None
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(attempt, [f"worker-{i}" for i in range(8)]))
        winners = {value for value in results if value is not None}
        self.assertEqual(1, len(winners))

    def test_expired_lease_recovers(self):
        leases = LeaseRegistry()
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        old = leases.claim("a", "a", "task-001", "worker-a", ttl_seconds=1, now=start)
        recovered = leases.recover_expired(now=start + timedelta(seconds=2))
        self.assertEqual([old], recovered)
        fresh = leases.claim("a", "a", "task-001", "worker-b", ttl_seconds=30, now=start + timedelta(seconds=2))
        self.assertEqual("worker-b", fresh.holder_agent_instance_id)

    def test_restarted_instance_cannot_renew_stale_instance_lease(self):
        leases = LeaseRegistry()
        lease = leases.claim("a", "a", "task-001", "worker-instance-1", ttl_seconds=30)
        with self.assertRaises(ProjectScopeError):
            leases.renew("a", "a", "task-001", "worker-instance-2", lease.lease_id)

    def test_compare_and_set_rejects_stale_update(self):
        store = VersionedStateStore()
        first = store.initialize("a", "a", "artifact", {"value": 1}, actor_agent_instance_id="worker-1")
        updated = store.compare_and_set(
            "a", "a", "artifact", expected_version=first.version, value={"value": 2},
            actor_agent_instance_id="worker-1"
        )
        self.assertEqual(2, updated.version)
        with self.assertRaises(StaleVersion):
            store.compare_and_set(
                "a", "a", "artifact", expected_version=first.version, value={"value": 3},
                actor_agent_instance_id="worker-2"
            )

    def test_project_pause_is_independent(self):
        registry = ProjectRegistry()
        a = registry.register("a", "repo/a")
        registry.register("b", "repo/b")
        paused = registry.transition("a", "a", expected_version=a.version, status="PAUSED")
        self.assertEqual("PAUSED", paused.status)
        with self.assertRaises(ProjectLifecycleError):
            registry.assert_operation("a", "a", mutation=True)
        self.assertTrue(registry.assert_operation("b", "b", mutation=True))

    def test_draining_allows_completion_but_denies_new_work(self):
        registry = ProjectRegistry()
        current = registry.register("a", "repo/a")
        registry.transition("a", "a", expected_version=current.version, status="DRAINING")
        with self.assertRaises(ProjectLifecycleError):
            registry.assert_operation("a", "a", mutation=True)
        self.assertTrue(registry.assert_operation("a", "a", mutation=True, drain_completion=True))

    def test_unbound_agent_cannot_mutate(self):
        session = AgentSession("worker")
        with self.assertRaises(AgentLifecycleError):
            session.assert_mutation("a")

    def test_child_binding_inherits_parent_project(self):
        parent = ProjectBinding("a", "repo/a", "/work/a", "primary", "a::primary-1", "2.4.0-alpha.1")
        child = inherit_child_binding(parent, "researcher-01")
        self.assertEqual("a", child.project_id)
        self.assertEqual("repo/a", child.repository_identity)
        self.assertNotEqual(parent.agent_instance_id, child.agent_instance_id)

    def test_active_agent_rejects_foreign_mutation(self):
        binding = ProjectBinding("a", "repo/a", "/work/a", "worker", "a::worker-1", "2.4.0-alpha.1")
        session = AgentSession("worker").bind(binding).initialize().activate()
        self.assertTrue(session.assert_mutation("a"))
        with self.assertRaises(ProjectScopeError):
            session.assert_mutation("b")


if __name__ == "__main__":
    unittest.main()
