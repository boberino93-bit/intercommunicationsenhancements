from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from org_agent_mesh.constants import FRAMEWORK_VERSION, PROTOCOL_VERSION
from org_agent_mesh.package_manifest import validate_agent_package_manifest
from org_agent_mesh.project_scope import ProjectScopeError

BASE={"schema":"org-agent-mesh/agent-package-manifest/v3","project_id":"intercommunicationsenhancements","repository_identity":"boberino93-bit/intercommunicationsenhancements","canonical_branch":"main","coordination_root":".interagent","artifact_root":".interagent/artifacts","identity_lock_path":"PROJECT_IDENTITY_LOCK.json","bootstrap_order_path":"BOOTSTRAP_ORDER.json","dependency_map_path":"packaging/agent_package_dependencies.json","dependency_map_sha256":"a"*64,"agent_spawn_policy":{"status":"BOUND_ONLY"},"deployment_role":"PRIMARY","authority_tier":"ORCHESTRATOR","capabilities":["READ_SOURCE"],"framework_version":FRAMEWORK_VERSION,"protocol_version":PROTOCOL_VERSION,"package_version":FRAMEWORK_VERSION,"built_at_utc":"2026-10-03T23:59:00Z","source_revision":"0"*40,"component_sha256":{"PROJECT_IDENTITY_LOCK.json":"b"*64},"included_components":["PROJECT_IDENTITY_LOCK.json"]}

class PackageTest(unittest.TestCase):
    def test_current_package_validates(self): self.assertTrue(validate_agent_package_manifest(BASE,expected_project_id="intercommunicationsenhancements",expected_repository_identity="boberino93-bit/intercommunicationsenhancements",expected_coordination_root=".interagent"))
    def test_foreign_package_rejected(self):
        with self.assertRaises(ProjectScopeError): validate_agent_package_manifest(BASE,expected_project_id="other")
    def test_wrong_repository_rejected(self):
        with self.assertRaises(ProjectScopeError): validate_agent_package_manifest(BASE,expected_repository_identity="boberino93-bit/other")
    def test_stale_protocol_rejected(self):
        with self.assertRaises(ValueError): validate_agent_package_manifest(dict(BASE,protocol_version="2.3.0-alpha.1"),expected_project_id="intercommunicationsenhancements")
    def test_stale_framework_rejected(self):
        with self.assertRaises(ValueError): validate_agent_package_manifest(dict(BASE,framework_version="1.5.0-alpha.1",package_version="1.5.0-alpha.1"),expected_project_id="intercommunicationsenhancements")
    def test_unknown_capability_rejected(self):
        with self.assertRaises(ValueError): validate_agent_package_manifest(dict(BASE,capabilities=["NOT_REAL"]))
    def test_package_version_must_match_framework(self):
        with self.assertRaises(ValueError): validate_agent_package_manifest(dict(BASE,package_version="other"))

if __name__=="__main__": unittest.main()
