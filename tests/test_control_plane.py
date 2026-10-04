from datetime import datetime, timedelta, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.constants import PROTOCOL_VERSION
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


def active_session(project, agent, instance, capabilities):
    binding = ProjectBinding(project, f"repo/{project}", f"/work/{project}", agent, instance, PROTOCOL_VERSION, tuple(capabilities))
    return AgentSession(agent).bind(binding).initialize().activate()

BASE_CAPS = ("CLAIM_TASK", "WRITE_ACCEPTED_STATE", "CONTROL_PROJECT_LIFECYCLE")


class ControlPlaneTest(unittest.TestCase):
    def test_same_named_resources_do_not_collide_across_projects(self):
        leases = LeaseRegistry()
        a_session = active_session("a", "worker-a", "a-worker-a-1", BASE_CAPS)
        b_session = active_session("b", "worker-b", "b-worker-b-1", BASE_CAPS)
        a = leases.claim(a_session, "a", "task-001", ttl_seconds=30)
        b = leases.claim(b_session, "b", "task-001", ttl_seconds=30)
        self.assertNotEqual(a.lease_id, b.lease_id)
        self.assertEqual(a.resource_id, b.resource_id)

    def test_foreign_lease_claim_denied(self):
        session = active_session("a", "worker-a", "a-worker-a-1", BASE_CAPS)
        with self.assertRaises(ProjectScopeError):
            LeaseRegistry().claim(session, "b", "task-001")

    def test_raw_project_string_cannot_authorize_mutation(self):
        with self.assertRaises(AgentLifecycleError):
            LeaseRegistry().claim("a", "a", "task-001")

    def test_duplicate_claim_by_same_instance_is_idempotent(self):
        leases = LeaseRegistry(); session = active_session("a", "worker-a", "a-worker-a-1", BASE_CAPS)
        first = leases.claim(session, "a", "task-001", ttl_seconds=30)
        second = leases.claim(session, "a", "task-001", ttl_seconds=30)
        self.assertEqual(first, second)

    def test_competing_active_lease_is_denied(self):
        leases = LeaseRegistry(); first = active_session("a", "worker-a", "a-worker-a-1", BASE_CAPS); second = active_session("a", "worker-b", "a-worker-b-1", BASE_CAPS)
        leases.claim(first, "a", "task-001", ttl_seconds=30)
        with self.assertRaises(LeaseConflict):
            leases.claim(second, "a", "task-001", ttl_seconds=30)

    def test_concurrent_claim_has_one_effective_holder(self):
        leases = LeaseRegistry()
        sessions = [active_session("a", f"worker-{i}", f"a-worker-{i}-instance", BASE_CAPS) for i in range(8)]
        def attempt(session):
            try:
                return leases.claim(session, "a", "task-001", ttl_seconds=30).holder_agent_instance_id
            except LeaseConflict:
                return None
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(attempt, sessions))
        self.assertEqual(1, len({value for value in results if value is not None}))

    def test_expired_lease_recovers(self):
        leases = LeaseRegistry(); first_session = active_session("a", "worker-a", "a-worker-a-1", BASE_CAPS); second_session = active_session("a", "worker-b", "a-worker-b-1", BASE_CAPS)
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        old = leases.claim(first_session, "a", "task-001", ttl_seconds=1, now=start)
        self.assertEqual([old], leases.recover_expired(now=start + timedelta(seconds=2)))
        fresh = leases.claim(second_session, "a", "task-001", ttl_seconds=30, now=start + timedelta(seconds=2))
        self.assertEqual("a-worker-b-1", fresh.holder_agent_instance_id)

    def test_restarted_instance_cannot_renew_stale_instance_lease(self):
        leases = LeaseRegistry(); first = active_session("a", "worker", "a-worker-instance-1", BASE_CAPS); restarted = active_session("a", "worker", "a-worker-instance-2", BASE_CAPS)
        lease = leases.claim(first, "a", "task-001", ttl_seconds=30)
        with self.assertRaises(ProjectScopeError):
            leases.renew(restarted, "a", "task-001", lease.lease_id)

    def test_compare_and_set_rejects_stale_update(self):
        store = VersionedStateStore(); session = active_session("a", "worker", "a-worker-1", BASE_CAPS)
        first = store.initialize(session, "a", "artifact", {"value": 1})
        updated = store.compare_and_set(session, "a", "artifact", expected_version=first.version, value={"value": 2})
        self.assertEqual(2, updated.version)
        with self.assertRaises(StaleVersion):
            store.compare_and_set(session, "a", "artifact", expected_version=first.version, value={"value": 3})

    def test_project_pause_is_independent(self):
        registry = ProjectRegistry(); a_session = active_session("a", "primary-a", "a-primary-1", BASE_CAPS); b_session = active_session("b", "primary-b", "b-primary-1", BASE_CAPS)
        a = registry.register(a_session); registry.register(b_session)
        paused = registry.transition(a_session, "a", expected_version=a.version, status="PAUSED")
        self.assertEqual("PAUSED", paused.status)
        with self.assertRaises(ProjectLifecycleError):
            registry.assert_operation(a_session, "a", mutation=True, required_capability="CLAIM_TASK")
        self.assertTrue(registry.assert_operation(b_session, "b", mutation=True, required_capability="CLAIM_TASK"))

    def test_draining_allows_completion_but_denies_new_work(self):
        registry = ProjectRegistry(); session = active_session("a", "primary", "a-primary-1", BASE_CAPS)
        current = registry.register(session); registry.transition(session, "a", expected_version=current.version, status="DRAINING")
        with self.assertRaises(ProjectLifecycleError):
            registry.assert_operation(session, "a", mutation=True, required_capability="CLAIM_TASK")
        self.assertTrue(registry.assert_operation(session, "a", mutation=True, drain_completion=True, required_capability="CLAIM_TASK"))

    def test_unbound_agent_cannot_mutate(self):
        with self.assertRaises(AgentLifecycleError):
            AgentSession("worker").assert_mutation("a")

    def test_child_binding_inherits_parent_project_and_capabilities(self):
        parent = ProjectBinding("a", "repo/a", "/work/a", "primary", "a-primary-1", PROTOCOL_VERSION, ("CLAIM_TASK", "READ_SOURCE"))
        child = inherit_child_binding(parent, "researcher-01")
        self.assertEqual("a", child.project_id); self.assertEqual("repo/a", child.repository_identity); self.assertEqual(parent.capabilities, child.capabilities); self.assertNotEqual(parent.agent_instance_id, child.agent_instance_id)

    def test_child_cannot_escalate_capabilities(self):
        parent = ProjectBinding("a", "repo/a", "/work/a", "primary", "a-primary-1", PROTOCOL_VERSION, ("READ_SOURCE",))
        with self.assertRaises(ProjectScopeError):
            inherit_child_binding(parent, "researcher-01", capabilities=("READ_SOURCE", "WRITE_ACCEPTED_STATE"))

    def test_active_agent_rejects_foreign_mutation(self):
        session = active_session("a", "worker", "a-worker-1", BASE_CAPS)
        self.assertTrue(session.assert_mutation("a"))
        with self.assertRaises(ProjectScopeError):
            session.assert_mutation("b")


if __name__ == "__main__":
    unittest.main()
