from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.constants import PROTOCOL_VERSION
from org_agent_mesh.control_plane import AgentSession, LeaseConflict, StaleVersion
from org_agent_mesh.durable_backend import (
    CorruptDurableRecord,
    IncompatibleDurableSchema,
    SQLiteRecordBackend,
)
from org_agent_mesh.durable_state import (
    DurableLeaseRegistry,
    DurableVersionedStateStore,
)
from org_agent_mesh.project_scope import ProjectBinding, ProjectScopeError


CAPS = ("CLAIM_TASK", "WRITE_ACCEPTED_STATE")


def active_session(project, agent, instance):
    binding = ProjectBinding(
        project,
        f"repo/{project}",
        f"/work/{project}",
        agent,
        instance,
        PROTOCOL_VERSION,
        CAPS,
    )
    return AgentSession(agent).bind(binding).initialize().activate()


class DurableStateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "mesh-state.sqlite3"

    def tearDown(self):
        self.tmp.cleanup()

    def backend(self):
        return SQLiteRecordBackend(self.db)

    def test_state_survives_backend_reopen(self):
        session = active_session("a", "worker", "a-worker-1")
        first = DurableVersionedStateStore(self.backend())
        created = first.initialize(session, "a", "accepted", {"value": 1})

        reopened = DurableVersionedStateStore(self.backend())
        recovered = reopened.read("a", "accepted")
        self.assertEqual(created, recovered)

        updated = reopened.compare_and_set(
            session,
            "a",
            "accepted",
            expected_version=recovered.version,
            value={"value": 2},
        )
        self.assertEqual(2, updated.version)
        self.assertEqual({"value": 2}, updated.value)

    def test_same_resource_id_is_isolated_by_project(self):
        a = active_session("a", "worker-a", "a-worker-1")
        b = active_session("b", "worker-b", "b-worker-1")
        store = DurableVersionedStateStore(self.backend())
        store.initialize(a, "a", "shared", {"project": "a"})
        store.initialize(b, "b", "shared", {"project": "b"})
        self.assertEqual("a", store.read("a", "shared").value["project"])
        self.assertEqual("b", store.read("b", "shared").value["project"])

    def test_concurrent_state_cas_has_single_winner(self):
        session = active_session("a", "worker", "a-worker-1")
        seed = DurableVersionedStateStore(self.backend())
        seed.initialize(session, "a", "accepted", {"winner": None})

        def attempt(value):
            store = DurableVersionedStateStore(self.backend())
            try:
                return store.compare_and_set(
                    session,
                    "a",
                    "accepted",
                    expected_version=1,
                    value={"winner": value},
                )
            except StaleVersion:
                return None

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(attempt, range(8)))

        winners = [record for record in results if record is not None]
        self.assertEqual(1, len(winners))
        final = DurableVersionedStateStore(self.backend()).read("a", "accepted")
        self.assertEqual(2, final.version)
        self.assertEqual(winners[0].value, final.value)

    def test_active_lease_survives_restart_and_blocks_competitor(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        first_session = active_session("a", "worker-a", "a-worker-a-1")
        second_session = active_session("a", "worker-b", "a-worker-b-1")
        first = DurableLeaseRegistry(self.backend())
        lease = first.claim(
            first_session, "a", "task-001", ttl_seconds=60, now=start
        )

        reopened = DurableLeaseRegistry(self.backend())
        self.assertEqual(
            lease,
            reopened.get("a", "task-001", now=start + timedelta(seconds=1)),
        )
        with self.assertRaises(LeaseConflict):
            reopened.claim(
                second_session,
                "a",
                "task-001",
                ttl_seconds=60,
                now=start + timedelta(seconds=1),
            )

    def test_expired_lease_is_reclaimed_after_restart(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        first_session = active_session("a", "worker-a", "a-worker-a-1")
        second_session = active_session("a", "worker-b", "a-worker-b-1")
        lease = DurableLeaseRegistry(self.backend()).claim(
            first_session, "a", "task-001", ttl_seconds=1, now=start
        )

        reopened = DurableLeaseRegistry(self.backend())
        fresh = reopened.claim(
            second_session,
            "a",
            "task-001",
            ttl_seconds=60,
            now=start + timedelta(seconds=2),
        )
        self.assertEqual(lease.version + 1, fresh.version)
        self.assertEqual("a-worker-b-1", fresh.holder_agent_instance_id)
        self.assertNotEqual(lease.lease_id, fresh.lease_id)

    def test_concurrent_durable_lease_claim_has_single_holder(self):
        sessions = [
            active_session("a", f"worker-{i}", f"a-worker-{i}-instance")
            for i in range(8)
        ]

        def attempt(session):
            registry = DurableLeaseRegistry(self.backend())
            try:
                return registry.claim(
                    session, "a", "task-001", ttl_seconds=60
                ).holder_agent_instance_id
            except LeaseConflict:
                return None

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(attempt, sessions))

        holders = {value for value in results if value is not None}
        self.assertEqual(1, len(holders))
        final = DurableLeaseRegistry(self.backend()).get("a", "task-001")
        self.assertIn(final.holder_agent_instance_id, holders)

    def test_restarted_instance_cannot_renew_persisted_lease(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        original = active_session("a", "worker", "a-worker-1")
        restarted = active_session("a", "worker", "a-worker-2")
        lease = DurableLeaseRegistry(self.backend()).claim(
            original, "a", "task-001", ttl_seconds=60, now=start
        )

        with self.assertRaises(ProjectScopeError):
            DurableLeaseRegistry(self.backend()).renew(
                restarted,
                "a",
                "task-001",
                lease.lease_id,
                ttl_seconds=60,
                now=start + timedelta(seconds=1),
            )

    def test_checksum_tampering_fails_closed(self):
        session = active_session("a", "worker", "a-worker-1")
        DurableVersionedStateStore(self.backend()).initialize(
            session, "a", "accepted", {"safe": True}
        )
        connection = sqlite3.connect(self.db)
        try:
            connection.execute(
                """
                UPDATE mesh_records
                SET payload_json = ?
                WHERE namespace = ? AND project_id = ? AND resource_id = ?
                """,
                ('{"safe":false}', "accepted_state", "a", "accepted"),
            )
            connection.commit()
        finally:
            connection.close()

        with self.assertRaises(CorruptDurableRecord):
            DurableVersionedStateStore(self.backend()).read("a", "accepted")

    def test_unknown_schema_version_fails_closed(self):
        self.backend()
        connection = sqlite3.connect(self.db)
        try:
            connection.execute(
                "UPDATE mesh_metadata SET value = '999' WHERE key = 'schema_version'"
            )
            connection.commit()
        finally:
            connection.close()

        with self.assertRaises(IncompatibleDurableSchema):
            SQLiteRecordBackend(self.db)


if __name__ == "__main__":
    unittest.main()
