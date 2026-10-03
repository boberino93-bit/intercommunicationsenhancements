from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.package_manifest import validate_agent_package_manifest
from org_agent_mesh.project_scope import ProjectScopeError

BASE = {
    "schema": "org-agent-mesh/agent-package-manifest/v1",
    "project_id": "intercommunicationsenhancements",
    "deployment_role": "PRIMARY",
    "authority_tier": "ORCHESTRATOR",
    "framework_version": "1.2.0-alpha.1",
    "protocol_version": "2.1.0-alpha.1",
    "package_version": "1.2.0-alpha.1",
    "source_revision": "test",
    "included_components": []
}


class PackageTest(unittest.TestCase):
    def test_current_package_validates(self):
        self.assertTrue(validate_agent_package_manifest(BASE, expected_project_id="intercommunicationsenhancements"))

    def test_foreign_package_rejected(self):
        with self.assertRaises(ProjectScopeError):
            validate_agent_package_manifest(BASE, expected_project_id="other")

    def test_stale_protocol_rejected(self):
        with self.assertRaises(ValueError):
            validate_agent_package_manifest(dict(BASE, protocol_version="1.0"), expected_project_id="intercommunicationsenhancements")


if __name__ == "__main__":
    unittest.main()
