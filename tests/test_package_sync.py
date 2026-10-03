from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.package_manifest import validate_agent_package_manifest
from org_agent_mesh.project_scope import ProjectScopeError

BASE = {
    "schema": "org-agent-mesh/agent-package-manifest/v2",
    "project_id": "intercommunicationsenhancements",
    "repository_identity": "boberino93-bit/intercommunicationsenhancements",
    "canonical_branch": "main",
    "coordination_root": ".interagent",
    "artifact_root": ".interagent/artifacts",
    "identity_lock_path": "PROJECT_IDENTITY_LOCK.json",
    "bootstrap_order_path": "BOOTSTRAP_ORDER.json",
    "coordination_snapshot_path": ".interagent/directives/2026-10-03-project-identity-recovery.json",
    "agent_spawn_policy": {"status": "BOUND_ONLY"},
    "deployment_role": "PRIMARY",
    "authority_tier": "ORCHESTRATOR",
    "framework_version": "1.3.0-alpha.1",
    "protocol_version": "2.2.0-alpha.1",
    "package_version": "1.3.0-alpha.1",
    "source_revision": "0" * 40,
    "identity_artifact_sha256": {"PROJECT_IDENTITY_LOCK.json": "a"},
    "component_sha256": {"PROJECT_IDENTITY_LOCK.json": "a"},
    "included_components": ["PROJECT_IDENTITY_LOCK.json"]
}


class PackageTest(unittest.TestCase):
    def test_current_package_validates(self):
        self.assertTrue(validate_agent_package_manifest(
            BASE,
            expected_project_id="intercommunicationsenhancements",
            expected_repository_identity="boberino93-bit/intercommunicationsenhancements",
            expected_coordination_root=".interagent",
        ))

    def test_foreign_package_rejected(self):
        with self.assertRaises(ProjectScopeError):
            validate_agent_package_manifest(BASE, expected_project_id="other")

    def test_wrong_repository_rejected(self):
        with self.assertRaises(ProjectScopeError):
            validate_agent_package_manifest(BASE, expected_repository_identity="boberino93-bit/other")

    def test_stale_protocol_rejected(self):
        with self.assertRaises(ValueError):
            validate_agent_package_manifest(dict(BASE, protocol_version="1.0"), expected_project_id="intercommunicationsenhancements")


if __name__ == "__main__":
    unittest.main()
