"""PostgreSQL prototype for the IPG3 durable adapter contract.

Requires psycopg 3. The adapter relies on unique constraints, row locks and transactions.
It is a design candidate only; passing conformance does not by itself make it production-approved.
"""

from __future__ import annotations

import json
from datetime import timezone

from durable_adapter_api import AdapterConflict, DurableAdapter, LeaseConflict, LeaseOwnershipError, LeaseValue, StoredValue

try:
    import psycopg
except ImportError:  # pragma: no cover - exercised only when optional dependency is absent
    psycopg = None


class PostgresDurableAdapter(DurableAdapter):
    capabilities = frozenset({
        "EXCLUSIVE_CREATE", "COMPARE_AND_SET", "LEASE_TTL", "ATOMIC_COUNTER_CONSUME",
        "TRANSACTIONAL_BATCH", "APPEND_ONLY_LOG", "SERVER_TIME", "MULTI_PROCESS", "MULTI_NODE",
    })

    def __init__(self, dsn: str):
        if psycopg is None:
            raise RuntimeError("psycopg is required for PostgresDurableAdapter")
        self.dsn = dsn
        self._conn = psycopg.connect(dsn, autocommit=True)
        self._init_schema()

    def _init_schema(self):
        with self._conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ipg3_kv (
                    namespace TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value_json JSONB NOT NULL,
                    version BIGINT NOT NULL,
                    PRIMARY KEY(namespace, project_id, key)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ipg3_leases (
                    project_id TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    holder_instance_id TEXT NOT NULL,
                    expires_at TIMESTAMPTZ NOT NULL,
                    version BIGINT NOT NULL,
                    PRIMARY KEY(project_id, resource_id)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ipg3_events (
                    project_id TEXT NOT NULL,
                    sequence BIGINT NOT NULL,
                    event_id TEXT NOT NULL,
                    event_json JSONB NOT NULL,
                    PRIMARY KEY(project_id, sequence),
                    UNIQUE(project_id, event_id)
                )
            """)

    def reset_for_tests(self):
        with self._conn.cursor() as cur:
            cur.execute("TRUNCATE ipg3_events, ipg3_leases, ipg3_kv")

    @staticmethod
    def _json(value):
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def _stored(row):
        if row is None: return None
        value = row[0]
        if isinstance(value, str): value = json.loads(value)
        return StoredValue(value, int(row[1]))

    def exclusive_create(self, namespace, project_id, key, value):
        try:
            with self._conn.transaction(), self._conn.cursor() as cur:
                cur.execute("INSERT INTO ipg3_kv(namespace,project_id,key,value_json,version) VALUES (%s,%s,%s,%s::jsonb,0)", (namespace, project_id, key, self._json(value)))
        except Exception as exc:
            if getattr(exc, "sqlstate", None) == "23505": raise AdapterConflict("identity already exists") from exc
            raise
        return StoredValue(value, 0)

    def get(self, namespace, project_id, key):
        with self._conn.cursor() as cur:
            cur.execute("SELECT value_json,version FROM ipg3_kv WHERE namespace=%s AND project_id=%s AND key=%s", (namespace, project_id, key))
            return self._stored(cur.fetchone())

    def compare_and_set(self, namespace, project_id, key, *, expected_version, value):
        with self._conn.transaction(), self._conn.cursor() as cur:
            cur.execute("UPDATE ipg3_kv SET value_json=%s::jsonb, version=version+1 WHERE namespace=%s AND project_id=%s AND key=%s AND version=%s RETURNING version", (self._json(value), namespace, project_id, key, expected_version))
            row = cur.fetchone()
            if row is None: raise AdapterConflict("missing or stale version")
            return StoredValue(value, int(row[0]))

    def atomic_consume(self, namespace, project_id, key, *, expected_version, counter_field, limit_field, terminal_field, terminal_value):
        with self._conn.transaction(), self._conn.cursor() as cur:
            cur.execute("SELECT value_json,version FROM ipg3_kv WHERE namespace=%s AND project_id=%s AND key=%s FOR UPDATE", (namespace, project_id, key))
            row = cur.fetchone()
            if row is None or int(row[1]) != expected_version: raise AdapterConflict("missing or stale consumable record")
            value = row[0] if isinstance(row[0], dict) else json.loads(row[0])
            used = int(value[counter_field]); limit = int(value[limit_field])
            if used >= limit: raise AdapterConflict("consumable limit exhausted")
            value[counter_field] = used + 1
            if value[counter_field] >= limit: value[terminal_field] = terminal_value
            version = expected_version + 1
            cur.execute("UPDATE ipg3_kv SET value_json=%s::jsonb,version=%s WHERE namespace=%s AND project_id=%s AND key=%s", (self._json(value), version, namespace, project_id, key))
            return StoredValue(value, version)

    def claim_lease(self, project_id, resource_id, holder_instance_id, *, expires_at, now):
        if expires_at.tzinfo is None or now.tzinfo is None or expires_at <= now: raise ValueError("invalid lease time")
        with self._conn.transaction(), self._conn.cursor() as cur:
            cur.execute("SELECT holder_instance_id,expires_at,version FROM ipg3_leases WHERE project_id=%s AND resource_id=%s FOR UPDATE", (project_id, resource_id))
            row = cur.fetchone()
            if row is None:
                cur.execute("INSERT INTO ipg3_leases VALUES (%s,%s,%s,%s,0)", (project_id, resource_id, holder_instance_id, expires_at))
                version = 0
            elif row[0] == holder_instance_id and row[1] > now:
                return LeaseValue(project_id, resource_id, holder_instance_id, row[1].astimezone(timezone.utc).isoformat().replace("+00:00","Z"), int(row[2]))
            elif row[1] <= now:
                version = int(row[2]) + 1
                cur.execute("UPDATE ipg3_leases SET holder_instance_id=%s,expires_at=%s,version=%s WHERE project_id=%s AND resource_id=%s", (holder_instance_id, expires_at, version, project_id, resource_id))
            else:
                raise LeaseConflict("lease held by another execution instance")
            return LeaseValue(project_id, resource_id, holder_instance_id, expires_at.astimezone(timezone.utc).isoformat().replace("+00:00","Z"), version)

    def renew_lease(self, project_id, resource_id, holder_instance_id, *, expires_at, now, expected_version):
        with self._conn.transaction(), self._conn.cursor() as cur:
            cur.execute("UPDATE ipg3_leases SET expires_at=%s,version=version+1 WHERE project_id=%s AND resource_id=%s AND holder_instance_id=%s AND version=%s AND expires_at>%s RETURNING version", (expires_at, project_id, resource_id, holder_instance_id, expected_version, now))
            row = cur.fetchone()
            if row is None: raise LeaseOwnershipError("lease ownership/version/expiry mismatch")
            return LeaseValue(project_id, resource_id, holder_instance_id, expires_at.astimezone(timezone.utc).isoformat().replace("+00:00","Z"), int(row[0]))

    def release_lease(self, project_id, resource_id, holder_instance_id, *, expected_version):
        with self._conn.transaction(), self._conn.cursor() as cur:
            cur.execute("DELETE FROM ipg3_leases WHERE project_id=%s AND resource_id=%s AND holder_instance_id=%s AND version=%s", (project_id, resource_id, holder_instance_id, expected_version))
            if cur.rowcount != 1: raise LeaseOwnershipError("lease ownership/version mismatch")

    def append_event(self, project_id, sequence, event_id, event):
        try:
            with self._conn.transaction(), self._conn.cursor() as cur:
                cur.execute("INSERT INTO ipg3_events VALUES (%s,%s,%s,%s::jsonb)", (project_id, sequence, event_id, self._json(event)))
        except Exception as exc:
            if getattr(exc, "sqlstate", None) == "23505": raise AdapterConflict("event sequence/id already exists") from exc
            raise

    def read_events(self, project_id):
        with self._conn.cursor() as cur:
            cur.execute("SELECT event_json FROM ipg3_events WHERE project_id=%s ORDER BY sequence", (project_id,))
            rows = cur.fetchall()
        return [row[0] if isinstance(row[0], dict) else json.loads(row[0]) for row in rows]

    def close(self):
        self._conn.close()
