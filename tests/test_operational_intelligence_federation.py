from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.constants import PROTOCOL_VERSION
from org_agent_mesh.control_plane import AgentSession
from org_agent_mesh.durable_backend import SQLiteRecordBackend
from org_agent_mesh.operational_intelligence_federation import (
    OperationalIntelligenceRegistry,
    SanitizedSnapshotBridge,
    routing_state,
    validate_acceptance_receipt,
    validate_registry_entry,
    validate_routing_lineage,
)
from org_agent_mesh.project_scope import ProjectBinding, ProjectScopeError

NOW = datetime(2026, 10, 7, 14, 0, tzinfo=timezone.utc)


def session(project, *, capabilities=("WRITE_ACCEPTED_STATE", "CROSS_PROJECT_EXCHANGE")):
    binding = ProjectBinding(
        project,
        f"owner/{project}",
        f"/work/{project}",
        "primary",
        f"{project}-primary-1",
        PROTOCOL_VERSION,
        capabilities,
    )
    return AgentSession("primary").bind(binding).initialize().activate()


def registry_entry(**overrides):
    entry = {
        "schema": "org-agent-mesh/operational-intelligence-registry-entry/v1",
        "entry_id": "peer-ai-safety",
        "peer_project_id": "peer-project",
        "consumer_project_id": "local-project",
        "themes": ["ai-safety", "routing"],
        "expertise_tags": ["forensics"],
        "capability_refs": ["read-only-analysis"],
        "availability_state": "UNKNOWN",
        "validated_at_utc": "2026-10-07T13:30:00Z",
        "expires_at_utc": "2026-10-07T15:00:00Z",
        "provenance_refs": ["exchange-1"],
        "authority_conveyed": False,
    }
    entry.update(overrides)
    return entry


def acceptance(**overrides):
    receipt = {
        "schema": "org-agent-mesh/cross-project-acceptance-receipt/v1",
        "receipt_id": "receipt-1",
        "request_ref": "request-1",
        "correlation_id": "corr-1",
        "requesting_project_id": "origin-project",
        "target_project_id": "peer-project",
        "status": "ACCEPTED",
        "local_task_ref": "peer-task-1",
        "update_ref": None,
        "supersedes_ref": None,
        "created_at_utc": "2026-10-07T13:40:00Z",
        "expires_at_utc": "2026-10-07T15:00:00Z",
        "provenance_refs": ["peer-intake-1"],
        "authority_conveyed": False,
    }
    receipt.update(overrides)
    return receipt


def exchange(**overrides):
    value = {
        "schema": "org-agent-mesh/cross-project-exchange/v1",
        "exchange_id": "exchange-1",
        "source_project_id": "source-project",
        "destination_project_id": "destination-project",
        "requesting_agent_id": "primary",
        "purpose": "share sanitized bounded result",
        "data_classification": "INTERNAL_SANITIZED",
        "requested_artifacts": ["snapshot-1"],
        "allowed_use": "evaluation",
        "created_at_utc": "2026-10-07T13:00:00Z",
        "expires_at_utc": "2026-10-07T15:00:00Z",
        "correlation_id": "corr-1",
        "approval": {"status": "APPROVED", "approved_by": "human"},
    }
    value.update(overrides)
    return value


def snapshot(**overrides):
    value = {
        "schema": "org-agent-mesh/sanitized-intelligence-snapshot/v1",
        "snapshot_id": "snapshot-1",
        "subject": "bounded research result",
        "summary": "Sanitized result with no secret or mutable peer state.",
        "artifact_refs": ["artifact-1"],
        "provenance_refs": ["source-finding-1"],
        "created_at_utc": "2026-10-07T13:20:00Z",
        "expires_at_utc": "2026-10-07T14:50:00Z",
        "authority_conveyed": False,
    }
    value.update(overrides)
    return value


class FederationTests(unittest.TestCase):
    def backend(self, directory):
        return SQLiteRecordBackend(Path(directory) / "mesh.sqlite3")

    def test_registry_rejects_unsanitized_extra_fields(self):
        with self.assertRaises(ProjectScopeError):
            validate_registry_entry(registry_entry(secret="nope"), now=NOW)

    def test_registry_requires_explicit_non_authoritative_availability(self):
        with self.assertRaises(ProjectScopeError):
            validate_registry_entry(registry_entry(authority_conveyed=True), now=NOW)
        with self.assertRaises(ValueError):
            validate_registry_entry(registry_entry(availability_state="NOT_APPLICABLE"), now=NOW)

    def test_registry_is_local_copy_by_value_and_discovery_is_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = self.backend(directory)
            registry = OperationalIntelligenceRegistry(backend)
            record = registry.publish(
                session("local-project"),
                "local-project",
                registry_entry(),
                source_exchange_ref="exchange-1",
                now=NOW,
            )
            self.assertEqual("local-project", record.project_id)
            self.assertIsNone(backend.read(registry.NAMESPACE, "peer-project", "peer-ai-safety"))
            found = registry.discover("local-project", themes=["ai-safety"], now=NOW)
            self.assertEqual(1, len(found))
            self.assertEqual("peer-project", found[0].payload["entry"]["peer_project_id"])

    def test_expired_registry_entries_are_not_discovered(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = self.backend(directory)
            registry = OperationalIntelligenceRegistry(backend)
            registry.publish(
                session("local-project"),
                "local-project",
                registry_entry(expires_at_utc="2026-10-07T14:01:00Z"),
                source_exchange_ref="exchange-1",
                now=NOW,
            )
            later = datetime(2026, 10, 7, 14, 2, tzinfo=timezone.utc)
            self.assertEqual([], registry.discover("local-project", themes=["ai-safety"], now=later))

    def test_routing_lineage_detects_cycles(self):
        lineage = validate_routing_lineage(
            correlation_id="corr-1",
            origin_project_id="origin-project",
            target_project_id="peer-project",
            visited_project_ids=["origin-project"],
        )
        self.assertEqual(("origin-project", "peer-project"), lineage)
        with self.assertRaises(ProjectScopeError):
            validate_routing_lineage(
                correlation_id="corr-1",
                origin_project_id="origin-project",
                target_project_id="origin-project",
                visited_project_ids=["origin-project", "peer-project"],
            )
        with self.assertRaises(ProjectScopeError):
            validate_routing_lineage(
                correlation_id="corr-1",
                origin_project_id="origin-project",
                target_project_id="third-project",
                visited_project_ids=["origin-project", "peer-project", "origin-project"],
            )

    def test_acceptance_is_not_active_execution(self):
        self.assertTrue(validate_acceptance_receipt(acceptance(), now=NOW))
        self.assertEqual("ACCEPTED", routing_state(acceptance(), now=NOW))
        self.assertNotIn("assignment_ref", acceptance())

    def test_decline_cannot_smuggle_task_reference(self):
        with self.assertRaises(ValueError):
            validate_acceptance_receipt(
                acceptance(status="DECLINED", local_task_ref="peer-task-1"),
                now=NOW,
            )

    def test_update_receipt_requires_explicit_supersession_chain(self):
        pending = acceptance(
            status="UPDATE_PENDING",
            local_task_ref="peer-task-1",
            update_ref="update-1",
            supersedes_ref="receipt-1",
        )
        self.assertTrue(validate_acceptance_receipt(pending, now=NOW))
        with self.assertRaises(ValueError):
            validate_acceptance_receipt(
                acceptance(status="UPDATE_ACCEPTED", update_ref="update-1", supersedes_ref=None),
                now=NOW,
            )

    def test_snapshot_export_requires_sanitized_classification(self):
        with tempfile.TemporaryDirectory() as directory:
            bridge = SanitizedSnapshotBridge(self.backend(directory))
            with self.assertRaises(ProjectScopeError):
                bridge.publish_export(
                    session("source-project"),
                    exchange(data_classification="SENSITIVE"),
                    snapshot(),
                    now=NOW,
                )

    def test_snapshot_cannot_outlive_exchange(self):
        with tempfile.TemporaryDirectory() as directory:
            bridge = SanitizedSnapshotBridge(self.backend(directory))
            with self.assertRaises(ProjectScopeError):
                bridge.publish_export(
                    session("source-project"),
                    exchange(expires_at_utc="2026-10-07T14:30:00Z"),
                    snapshot(expires_at_utc="2026-10-07T14:50:00Z"),
                    now=NOW,
                )

    def test_snapshot_bridge_is_copy_by_value_and_does_not_promote_accepted_state(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = self.backend(directory)
            bridge = SanitizedSnapshotBridge(backend)
            exported = bridge.publish_export(
                session("source-project"),
                exchange(),
                snapshot(),
                now=NOW,
            )
            imported = bridge.import_export(
                session("destination-project"),
                source_project_id="source-project",
                snapshot_id="snapshot-1",
                now=NOW,
            )
            self.assertEqual("source-project", exported.project_id)
            self.assertEqual("destination-project", imported.project_id)
            self.assertFalse(imported.payload["accepted_state"])
            self.assertFalse(imported.payload["authority_conveyed"])
            self.assertIsNone(
                backend.read(bridge.IMPORT_NAMESPACE, "source-project", "snapshot-1")
            )

    def test_foreign_destination_session_cannot_import(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = self.backend(directory)
            bridge = SanitizedSnapshotBridge(backend)
            bridge.publish_export(session("source-project"), exchange(), snapshot(), now=NOW)
            with self.assertRaises(ProjectScopeError):
                bridge.import_export(
                    session("other-project"),
                    source_project_id="source-project",
                    snapshot_id="snapshot-1",
                    now=NOW,
                )

    def test_import_requires_cross_project_capability(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = self.backend(directory)
            bridge = SanitizedSnapshotBridge(backend)
            bridge.publish_export(session("source-project"), exchange(), snapshot(), now=NOW)
            with self.assertRaises(ProjectScopeError):
                bridge.import_export(
                    session("destination-project", capabilities=("WRITE_ACCEPTED_STATE",)),
                    source_project_id="source-project",
                    snapshot_id="snapshot-1",
                    now=NOW,
                )


if __name__ == "__main__":
    unittest.main()
