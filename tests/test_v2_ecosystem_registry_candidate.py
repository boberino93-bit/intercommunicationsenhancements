from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.constants import PROTOCOL_VERSION
from org_agent_mesh.control_plane import AgentSession, StaleVersion
from org_agent_mesh.durable_backend import SQLiteRecordBackend
from org_agent_mesh.ecosystem_coordination import SanitizedEcosystemRegistry
from org_agent_mesh.project_scope import ProjectBinding, ProjectScopeError


LOCAL = "coordinator-project"


def session(project=LOCAL):
    binding = ProjectBinding(
        project,
        f"owner/{project}",
        f"/work/{project}",
        "primary",
        f"{project}-primary-1",
        PROTOCOL_VERSION,
        ("WRITE_ACCEPTED_STATE",),
    )
    return AgentSession("primary").bind(binding).initialize().activate()


def summary(peer="peer-project", *, status="ACTIVE"):
    return {
        "project_id": peer,
        "project_name": "Peer Project",
        "purpose": "sanitized test summary",
        "status": status,
        "repository_identity": f"owner/{peer}",
        "canonical_branch": "main",
        "board_root": f"/{peer}/AgentBus",
        "protocol_version": PROTOCOL_VERSION,
        "package_version": "1.6.0-alpha.1",
        "capacity_state": "SAFE",
        "backup_state": "VERIFIED",
        "recovery_state": "VERIFIED",
        "allowed_cross_project_links": [],
        "last_verified": "2026-10-04T16:00:00Z",
    }


class CandidateV2EcosystemRegistryTests(unittest.TestCase):
    def backend(self, directory):
        return SQLiteRecordBackend(Path(directory) / "mesh.sqlite3")

    def test_peer_summary_is_stored_under_local_project_only(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = self.backend(directory)
            registry = SanitizedEcosystemRegistry(backend)
            record = registry.publish(
                session(),
                LOCAL,
                summary(),
                source_exchange_ref="exchange-1",
            )
            self.assertEqual(LOCAL, record.project_id)
            self.assertEqual("peer-project", record.payload["summary"]["project_id"])
            self.assertIsNone(
                backend.read("ecosystem-summaries", "peer-project", "project-peer-project")
            )
            self.assertEqual(1, len(registry.list_local(LOCAL)))

    def test_registry_rejects_unsanitized_extra_field(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = SanitizedEcosystemRegistry(self.backend(directory))
            unsafe = dict(summary(), secret="never-export")
            with self.assertRaises(ProjectScopeError):
                registry.publish(
                    session(),
                    LOCAL,
                    unsafe,
                    source_exchange_ref="exchange-1",
                )

    def test_replacement_requires_compare_and_set_version(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = SanitizedEcosystemRegistry(self.backend(directory))
            first = registry.publish(
                session(),
                LOCAL,
                summary(),
                source_exchange_ref="exchange-1",
            )
            with self.assertRaises(StaleVersion):
                registry.publish(
                    session(),
                    LOCAL,
                    summary(status="PAUSED"),
                    source_exchange_ref="exchange-2",
                )
            updated = registry.publish(
                session(),
                LOCAL,
                summary(status="PAUSED"),
                source_exchange_ref="exchange-2",
                expected_version=first.version,
            )
            self.assertEqual("PAUSED", updated.payload["summary"]["status"])

    def test_foreign_session_cannot_write_local_registry(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = SanitizedEcosystemRegistry(self.backend(directory))
            with self.assertRaises(ProjectScopeError):
                registry.publish(
                    session("other-project"),
                    LOCAL,
                    summary(),
                    source_exchange_ref="exchange-1",
                )


if __name__ == "__main__":
    unittest.main()
