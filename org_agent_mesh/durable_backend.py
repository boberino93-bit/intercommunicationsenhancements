from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from typing import Protocol, runtime_checkable

from .control_plane import StaleVersion
from .project_scope import require_project_id, require_resource_id


SCHEMA_VERSION = 1


class DurableStateError(RuntimeError):
    """Base error for durable state failures."""


class CorruptDurableRecord(DurableStateError):
    """Persisted content failed integrity or structural validation."""


class IncompatibleDurableSchema(DurableStateError):
    """The durable store uses an unsupported schema version."""


@dataclass(frozen=True)
class DurableRecord:
    namespace: str
    project_id: str
    resource_id: str
    version: int
    payload: object
    updated_at_utc: str


def _utc_iso(now=None):
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_utc(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as exc:
        raise CorruptDurableRecord("persisted UTC timestamp is invalid") from exc
    if parsed.tzinfo is None:
        raise CorruptDurableRecord("persisted UTC timestamp is timezone-naive")
    return parsed.astimezone(timezone.utc)


def _canonical_json(payload):
    try:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise TypeError("durable payload must be JSON-serializable") from exc


def _digest(payload_json):
    return sha256(payload_json.encode("utf-8")).hexdigest()


def _namespace(value):
    return require_resource_id(value, field="namespace")


@runtime_checkable
class DurableRecordBackend(Protocol):
    def create(self, namespace, project_id, resource_id, payload, *, now=None):
        ...

    def read(self, namespace, project_id, resource_id):
        ...

    def compare_and_set(
        self,
        namespace,
        project_id,
        resource_id,
        *,
        expected_version,
        payload,
        now=None,
    ):
        ...

    def delete_if_version(self, namespace, project_id, resource_id, *, expected_version):
        ...

    def list_records(self, namespace, *, project_id=None):
        ...


class SQLiteRecordBackend:
    """Single-node crash-durable reference backend with transactional CAS.

    It intentionally does not claim distributed consensus. A production distributed
    adapter must satisfy the same create/CAS/delete atomicity contract or fail closed.
    """

    def __init__(self, path, *, timeout_seconds=5.0):
        if not isinstance(path, (str, Path)):
            raise TypeError("path must be a filesystem path")
        self.path = str(Path(path))
        if self.path == ":memory:":
            raise ValueError("durable backend requires a filesystem path")
        self.timeout_seconds = float(timeout_seconds)
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(
            self.path,
            timeout=self.timeout_seconds,
            isolation_level=None,
        )
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA synchronous = FULL")
        return connection

    def _initialize(self):
        connection = self._connect()
        try:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS mesh_metadata "
                "(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            current = connection.execute(
                "SELECT value FROM mesh_metadata WHERE key = 'schema_version'"
            ).fetchone()
            if current is None:
                connection.execute(
                    "INSERT INTO mesh_metadata(key, value) VALUES('schema_version', ?)",
                    (str(SCHEMA_VERSION),),
                )
            elif current[0] != str(SCHEMA_VERSION):
                raise IncompatibleDurableSchema(
                    f"unsupported durable schema version {current[0]!r}"
                )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS mesh_records (
                    namespace TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    version INTEGER NOT NULL CHECK(version >= 1),
                    payload_json TEXT NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    updated_at_utc TEXT NOT NULL,
                    PRIMARY KEY(namespace, project_id, resource_id)
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_mesh_records_project_namespace "
                "ON mesh_records(project_id, namespace)"
            )
            connection.execute("COMMIT")
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def _decode(self, row):
        if row is None:
            return None
        namespace, project_id, resource_id, version, payload_json, digest, updated_at = row
        try:
            namespace = _namespace(namespace)
            project_id = require_project_id(project_id)
            resource_id = require_resource_id(resource_id)
        except (TypeError, ValueError, PermissionError) as exc:
            raise CorruptDurableRecord("persisted record identity is invalid") from exc
        if not isinstance(version, int) or version < 1:
            raise CorruptDurableRecord("persisted record version is invalid")
        if _digest(payload_json) != digest:
            raise CorruptDurableRecord(
                f"checksum mismatch for {project_id!r}/{namespace!r}/{resource_id!r}"
            )
        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError as exc:
            raise CorruptDurableRecord("persisted payload JSON is invalid") from exc
        _parse_utc(updated_at)
        return DurableRecord(
            namespace,
            project_id,
            resource_id,
            version,
            payload,
            updated_at,
        )

    def create(self, namespace, project_id, resource_id, payload, *, now=None):
        namespace = _namespace(namespace)
        project_id = require_project_id(project_id)
        resource_id = require_resource_id(resource_id)
        payload_json = _canonical_json(payload)
        updated_at = _utc_iso(now)
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    """
                    INSERT INTO mesh_records(
                        namespace, project_id, resource_id, version,
                        payload_json, payload_sha256, updated_at_utc
                    ) VALUES (?, ?, ?, 1, ?, ?, ?)
                    """,
                    (
                        namespace,
                        project_id,
                        resource_id,
                        payload_json,
                        _digest(payload_json),
                        updated_at,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise StaleVersion("durable record already exists") from exc
            connection.execute("COMMIT")
            return DurableRecord(
                namespace, project_id, resource_id, 1, json.loads(payload_json), updated_at
            )
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def read(self, namespace, project_id, resource_id):
        namespace = _namespace(namespace)
        project_id = require_project_id(project_id)
        resource_id = require_resource_id(resource_id)
        connection = self._connect()
        try:
            row = connection.execute(
                """
                SELECT namespace, project_id, resource_id, version,
                       payload_json, payload_sha256, updated_at_utc
                FROM mesh_records
                WHERE namespace = ? AND project_id = ? AND resource_id = ?
                """,
                (namespace, project_id, resource_id),
            ).fetchone()
            return self._decode(row)
        finally:
            connection.close()

    def compare_and_set(
        self,
        namespace,
        project_id,
        resource_id,
        *,
        expected_version,
        payload,
        now=None,
    ):
        namespace = _namespace(namespace)
        project_id = require_project_id(project_id)
        resource_id = require_resource_id(resource_id)
        if not isinstance(expected_version, int) or expected_version < 1:
            raise ValueError("expected_version must be a positive integer")
        payload_json = _canonical_json(payload)
        updated_at = _utc_iso(now)
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                """
                UPDATE mesh_records
                SET version = version + 1,
                    payload_json = ?,
                    payload_sha256 = ?,
                    updated_at_utc = ?
                WHERE namespace = ? AND project_id = ? AND resource_id = ?
                  AND version = ?
                """,
                (
                    payload_json,
                    _digest(payload_json),
                    updated_at,
                    namespace,
                    project_id,
                    resource_id,
                    expected_version,
                ),
            )
            if cursor.rowcount != 1:
                current = connection.execute(
                    """
                    SELECT version FROM mesh_records
                    WHERE namespace = ? AND project_id = ? AND resource_id = ?
                    """,
                    (namespace, project_id, resource_id),
                ).fetchone()
                if current is None:
                    raise StaleVersion("durable record does not exist")
                raise StaleVersion(
                    f"stale durable version: expected {expected_version}, current {current[0]}"
                )
            connection.execute("COMMIT")
            return DurableRecord(
                namespace,
                project_id,
                resource_id,
                expected_version + 1,
                json.loads(payload_json),
                updated_at,
            )
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def delete_if_version(self, namespace, project_id, resource_id, *, expected_version):
        namespace = _namespace(namespace)
        project_id = require_project_id(project_id)
        resource_id = require_resource_id(resource_id)
        if not isinstance(expected_version, int) or expected_version < 1:
            raise ValueError("expected_version must be a positive integer")
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                """
                DELETE FROM mesh_records
                WHERE namespace = ? AND project_id = ? AND resource_id = ?
                  AND version = ?
                """,
                (namespace, project_id, resource_id, expected_version),
            )
            if cursor.rowcount != 1:
                current = connection.execute(
                    """
                    SELECT version FROM mesh_records
                    WHERE namespace = ? AND project_id = ? AND resource_id = ?
                    """,
                    (namespace, project_id, resource_id),
                ).fetchone()
                if current is None:
                    connection.execute("ROLLBACK")
                    return False
                raise StaleVersion(
                    f"stale durable version: expected {expected_version}, current {current[0]}"
                )
            connection.execute("COMMIT")
            return True
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def list_records(self, namespace, *, project_id=None):
        namespace = _namespace(namespace)
        if project_id is not None:
            project_id = require_project_id(project_id)
        connection = self._connect()
        try:
            if project_id is None:
                rows = connection.execute(
                    """
                    SELECT namespace, project_id, resource_id, version,
                           payload_json, payload_sha256, updated_at_utc
                    FROM mesh_records
                    WHERE namespace = ?
                    ORDER BY project_id, resource_id
                    """,
                    (namespace,),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT namespace, project_id, resource_id, version,
                           payload_json, payload_sha256, updated_at_utc
                    FROM mesh_records
                    WHERE namespace = ? AND project_id = ?
                    ORDER BY resource_id
                    """,
                    (namespace, project_id),
                ).fetchall()
            return [self._decode(row) for row in rows]
        finally:
            connection.close()
