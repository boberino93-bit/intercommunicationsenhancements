from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import os
import tempfile
import unittest

from durable_adapter_api import AdapterConflict, LeaseConflict, LeaseOwnershipError
from sqlite_durable_adapter import SQLiteDurableAdapter

try:
    from postgres_durable_adapter import PostgresDurableAdapter
except Exception:
    PostgresDurableAdapter = None

NOW = datetime(2026, 10, 4, 4, 0, 0, tzinfo=timezone.utc)


def run_black_box_suite(testcase, factory, *, reset=None):
    if reset: reset()

    # A1 exclusive create: exactly one effective winner.
    def contender(i):
        adapter = factory()
        try:
            adapter.exclusive_create("msg", "project-a", "same", {"winner": i})
            return "WIN"
        except AdapterConflict:
            return "LOSE"
        finally:
            adapter.close()
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(contender, range(32)))
    testcase.assertEqual(results.count("WIN"), 1)
    testcase.assertEqual(results.count("LOSE"), 31)

    # A2 CAS: one stale writer must lose.
    adapter = factory()
    adapter.exclusive_create("state", "project-a", "resource", {"v": 0})
    current = adapter.get("state", "project-a", "resource")
    updated = adapter.compare_and_set("state", "project-a", "resource", expected_version=current.version, value={"v": 1})
    testcase.assertEqual(updated.version, 1)
    with testcase.assertRaises(AdapterConflict):
        adapter.compare_and_set("state", "project-a", "resource", expected_version=current.version, value={"v": 2})

    # A4 consumable authorization.
    adapter.exclusive_create("approval", "project-a", "approval-1", {"uses": 0, "max_uses": 1, "status": "ISSUED"})
    consumed = adapter.atomic_consume("approval", "project-a", "approval-1", expected_version=0, counter_field="uses", limit_field="max_uses", terminal_field="status", terminal_value="CONSUMED")
    testcase.assertEqual(consumed.value["uses"], 1)
    testcase.assertEqual(consumed.value["status"], "CONSUMED")
    with testcase.assertRaises(AdapterConflict):
        adapter.atomic_consume("approval", "project-a", "approval-1", expected_version=0, counter_field="uses", limit_field="max_uses", terminal_field="status", terminal_value="CONSUMED")

    # A3 leases: execution-instance ownership, expiry and takeover.
    first = adapter.claim_lease("project-a", "resource-lease", "instance-1", expires_at=NOW + timedelta(minutes=10), now=NOW)
    with testcase.assertRaises(LeaseConflict):
        adapter.claim_lease("project-a", "resource-lease", "instance-2", expires_at=NOW + timedelta(minutes=20), now=NOW)
    renewed = adapter.renew_lease("project-a", "resource-lease", "instance-1", expires_at=NOW + timedelta(minutes=20), now=NOW, expected_version=first.version)
    testcase.assertGreater(renewed.version, first.version)
    with testcase.assertRaises(LeaseOwnershipError):
        adapter.release_lease("project-a", "resource-lease", "instance-2", expected_version=renewed.version)
    takeover = adapter.claim_lease("project-a", "resource-lease", "instance-2", expires_at=NOW + timedelta(minutes=40), now=NOW + timedelta(minutes=30))
    testcase.assertEqual(takeover.holder_instance_id, "instance-2")

    # Project isolation: identical logical key is distinct state.
    adapter.exclusive_create("state", "project-b", "same-name", {"project": "b"})
    adapter.exclusive_create("state", "project-a", "same-name", {"project": "a"})
    testcase.assertEqual(adapter.get("state", "project-a", "same-name").value["project"], "a")
    testcase.assertEqual(adapter.get("state", "project-b", "same-name").value["project"], "b")

    # A6 append-only events: sequence/id collision rejected and order preserved.
    adapter.append_event("project-a", 0, "event-0", {"n": 0})
    adapter.append_event("project-a", 1, "event-1", {"n": 1})
    with testcase.assertRaises(AdapterConflict):
        adapter.append_event("project-a", 1, "event-other", {"n": 999})
    testcase.assertEqual(adapter.read_events("project-a"), [{"n": 0}, {"n": 1}])
    adapter.close()


class SQLiteConformanceTests(unittest.TestCase):
    def test_black_box_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            path = os.path.join(temp, "ipg3.db")
            run_black_box_suite(self, lambda: SQLiteDurableAdapter(path))


@unittest.skipUnless(os.environ.get("IPG3_POSTGRES_DSN") and PostgresDurableAdapter is not None, "PostgreSQL conformance DSN unavailable")
class PostgresConformanceTests(unittest.TestCase):
    def test_black_box_contract(self):
        dsn = os.environ["IPG3_POSTGRES_DSN"]
        controller = PostgresDurableAdapter(dsn)
        controller.reset_for_tests()
        controller.close()
        run_black_box_suite(self, lambda: PostgresDurableAdapter(dsn))


if __name__ == "__main__":
    unittest.main()
