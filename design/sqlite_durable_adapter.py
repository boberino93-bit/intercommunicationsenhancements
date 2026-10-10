"""SQLite prototype for the IPG3 durable adapter contract.

SQLite is useful for local/multi-process conformance experiments but is not claimed as a
multi-node production backend. Transactions use BEGIN IMMEDIATE to serialize correctness-
sensitive mutations. State is JSON encoded and project-qualified in primary keys.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import timezone
from pathlib import Path
from threading import RLock

from durable_adapter_api import (
    AdapterConflict,
    DurableAdapter,
    LeaseConflict,
    LeaseOwnershipError,
    LeaseValue,
    StoredValue,
)


class SQLiteDurableAdapter(DurableAdapter):
    capabilities = frozenset({
        "EXCLUSIVE_CREATE", "COMPARE_AND_SET", "LEASE_TTL", "ATOMIC_COUNTER_CONSUME",
        "TRANSACTIONAL_BATCH", "APPEND_ONLY_LOG", "MULTI_PROCESS",
    })

    def __init__(self, path):
        self.path = str(Path(path))
        self._lock = RLock()
        self._conn = sqlite3.connect(self.path, timeout=30.0, isolation_level=None, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=FULL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def _init_schema(self):
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS kv (
                namespace TEXT NOT NULL,
                project_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value_json TEXT NOT NULL,
                version INTEGER NOT NULL,
                PRIMARY KEY(namespace, project_id, key)
            );
            CREATE TABLE IF NOT EXISTS leases (
                project_id TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                holder_instance_id TEXT NOT NULL,
                expires_at REAL NOT NULL,
                version INTEGER NOT NULL,
                PRIMARY KEY(project_id, resource_id)
            );
            CREATE TABLE IF NOT EXISTS events (
                project_id TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                event_id TEXT NOT NULL,
                event_json TEXT NOT NULL,
                PRIMARY KEY(project_id, sequence),
                UNIQUE(project_id, event_id)
            );
            """
        )

    @staticmethod
    def _dump(value):
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def _load(value):
        return json.loads(value)

    @staticmethod
    def _ts(value):
        if value.tzinfo is None:
            raise ValueError("datetime must be timezone-aware")
        return value.astimezone(timezone.utc).timestamp()

    @staticmethod
    def _iso_ts(ts):
        from datetime import datetime
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")

    def _transaction(self):
        class Tx:
            def __init__(self, outer): self.outer = outer
            def __enter__(self):
                self.outer._lock.acquire()
                self.outer._conn.execute("BEGIN IMMEDIATE")
                return self.outer._conn
            def __exit__(self, exc_type, exc, tb):
                try:
                    self.outer._conn.execute("ROLLBACK" if exc_type else "COMMIT")
                finally:
                    self.outer._lock.release()
                return False
        return Tx(self)

    def exclusive_create(self, namespace, project_id, key, value):
        try:
            with self._transaction() as conn:
                conn.execute(
                    "INSERT INTO kv(namespace, project_id, key, value_json, version) VALUES (?, ?, ?, ?, 0)",
                    (namespace, project_id, key, self._dump(value)),
                )
        except sqlite3.IntegrityError as exc:
            raise AdapterConflict("identity already exists") from exc
        return StoredValue(value, 0)

    def get(self, namespace, project_id, key):
        row = self._conn.execute(
            "SELECT value_json, version FROM kv WHERE namespace=? AND project_id=? AND key=?",
            (namespace, project_id, key),
        ).fetchone()
        return None if row is None else StoredValue(self._load(row[0]), row[1])

    def compare_and_set(self, namespace, project_id, key, *, expected_version, value):
        with self._transaction() as conn:
            row = conn.execute(
                "SELECT version FROM kv WHERE namespace=? AND project_id=? AND key=?",
                (namespace, project_id, key),
            ).fetchone()
            if row is None:
                raise AdapterConflict("identity not found")
            if row[0] != expected_version:
                raise AdapterConflict("stale version")
            version = expected_version + 1
            conn.execute(
                "UPDATE kv SET value_json=?, version=? WHERE namespace=? AND project_id=? AND key=? AND version=?",
                (self._dump(value), version, namespace, project_id, key, expected_version),
            )
            return StoredValue(value, version)

    def atomic_consume(self, namespace, project_id, key, *, expected_version, counter_field, limit_field, terminal_field, terminal_value):
        with self._transaction() as conn:
            row = conn.execute(
                "SELECT value_json, version FROM kv WHERE namespace=? AND project_id=? AND key=?",
                (namespace, project_id, key),
            ).fetchone()
            if row is None or row[1] != expected_version:
                raise AdapterConflict("missing or stale consumable record")
            value = self._load(row[0])
            used = int(value[counter_field]); limit = int(value[limit_field])
            if used >= limit:
                raise AdapterConflict("consumable limit exhausted")
            value[counter_field] = used + 1
            if value[counter_field] >= limit:
                value[terminal_field] = terminal_value
            version = expected_version + 1
            conn.execute(
                "UPDATE kv SET value_json=?, version=? WHERE namespace=? AND project_id=? AND key=? AND version=?",
                (self._dump(value), version, namespace, project_id, key, expected_version),
            )
            return StoredValue(value, version)

    def claim_lease(self, project_id, resource_id, holder_instance_id, *, expires_at, now):
        exp = self._ts(expires_at); current = self._ts(now)
        if exp <= current: raise ValueError("lease expiry must be in the future")
        with self._transaction() as conn:
            row = conn.execute(
                "SELECT holder_instance_id, expires_at, version FROM leases WHERE project_id=? AND resource_id=?",
                (project_id, resource_id),
            ).fetchone()
            if row is None:
                version = 0
                conn.execute("INSERT INTO leases VALUES (?, ?, ?, ?, ?)", (project_id, resource_id, holder_instance_id, exp, version))
            elif row[0] == holder_instance_id and row[1] > current:
                return LeaseValue(project_id, resource_id, holder_instance_id, self._iso_ts(row[1]), row[2])
            elif row[1] <= current:
                version = row[2] + 1
                conn.execute(
                    "UPDATE leases SET holder_instance_id=?, expires_at=?, version=? WHERE project_id=? AND resource_id=? AND version=?",
                    (holder_instance_id, exp, version, project_id, resource_id, row[2]),
                )
            else:
                raise LeaseConflict("lease held by another execution instance")
            return LeaseValue(project_id, resource_id, holder_instance_id, self._iso_ts(exp), version)

    def renew_lease(self, project_id, resource_id, holder_instance_id, *, expires_at, now, expected_version):
        exp = self._ts(expires_at); current = self._ts(now)
        if exp <= current: raise ValueError("lease expiry must be in the future")
        with self._transaction() as conn:
            row = conn.execute(
                "SELECT holder_instance_id, expires_at, version FROM leases WHERE project_id=? AND resource_id=?",
                (project_id, resource_id),
            ).fetchone()
            if row is None or row[0] != holder_instance_id:
                raise LeaseOwnershipError("lease not held by this execution instance")
            if row[2] != expected_version:
                raise LeaseOwnershipError("stale lease version")
            if row[1] <= current:
                raise LeaseOwnershipError("expired lease cannot be renewed")
            version = expected_version + 1
            conn.execute(
                "UPDATE leases SET expires_at=?, version=? WHERE project_id=? AND resource_id=? AND holder_instance_id=? AND version=?",
                (exp, version, project_id, resource_id, holder_instance_id, expected_version),
            )
            return LeaseValue(project_id, resource_id, holder_instance_id, self._iso_ts(exp), version)

    def release_lease(self, project_id, resource_id, holder_instance_id, *, expected_version):
        with self._transaction() as conn:
            cur = conn.execute(
                "DELETE FROM leases WHERE project_id=? AND resource_id=? AND holder_instance_id=? AND version=?",
                (project_id, resource_id, holder_instance_id, expected_version),
            )
            if cur.rowcount != 1:
                raise LeaseOwnershipError("lease ownership/version mismatch")

    def append_event(self, project_id, sequence, event_id, event):
        try:
            with self._transaction() as conn:
                conn.execute("INSERT INTO events VALUES (?, ?, ?, ?)", (project_id, sequence, event_id, self._dump(event)))
        except sqlite3.IntegrityError as exc:
            raise AdapterConflict("event sequence/id already exists") from exc

    def read_events(self, project_id):
        rows = self._conn.execute("SELECT event_json FROM events WHERE project_id=? ORDER BY sequence", (project_id,)).fetchall()
        return [self._load(row[0]) for row in rows]

    def close(self):
        self._conn.close()
