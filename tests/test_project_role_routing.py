import json
from pathlib import Path
import unittest

from org_agent_mesh.project_role_routing import RoutingError, resolve_route, validate_local_contract, validate_registry

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = {
    "schema": "org-agent-mesh/project-role-routing-registry/v1",
    "routing_contract_version": "1.2.0",
    "mode": "FAIL_CLOSED",
    "projects": {
        "alpha": {
            "repository": "owner/alpha",
            "repository_id": 101,
            "forum_namespace": "alpha::messages",
            "forum_locator": {"authority": "INTERNAL_ARTIFACTORY", "namespace": "alpha::messages", "repository_view": {"mode": "SNAPSHOT_BACKUP", "path": "agentbus/messages"}},
            "artifact_namespace": "alpha::artifacts",
            "handoff_paths": ["START_HERE.md", "state"],
            "local_contract_path": "AGENT_BOOTSTRAP.json",
            "routing_contract_version": "1.2.0",
            "roles": ["primary", "manager", "research"],
        }
    },
}
LOCAL_CONTRACT = {
    "schema": "org-agent-mesh/local-agent-bootstrap/v1",
    "routing_contract_version": "1.2.0",
    "mode": "FAIL_CLOSED",
    "project_id": "alpha",
    "repository": {"full_name": "owner/alpha", "id": 101},
    "forum": {"authority": "INTERNAL_ARTIFACTORY", "namespace": "alpha::messages", "repository_view": {"mode": "SNAPSHOT_BACKUP", "path": "agentbus/messages"}},
    "artifact_namespace": "alpha::artifacts",
    "handoff_paths": ["START_HERE.md", "state"],
    "authorized_roles": ["primary", "manager", "research"],
}


class ProjectRoleRoutingTests(unittest.TestCase):
    def test_valid_route_resolves_and_acknowledges(self):
        route = resolve_route(REGISTRY, project_id="alpha", role_id="research", current_repository="owner/alpha", current_repository_id=101)
        self.assertEqual(route.repository, "owner/alpha")
        self.assertEqual(route.forum_authority, "INTERNAL_ARTIFACTORY")
        self.assertEqual(route.forum_repository_view_mode, "SNAPSHOT_BACKUP")
        self.assertEqual(route.forum_repository_view_path, "agentbus/messages")
        self.assertIn("IDENTITY RESOLVED: project=alpha; role=research", route.acknowledgement("handoff-7"))

    def test_local_contract_matches_registry(self):
        validate_local_contract(REGISTRY, project_id="alpha", contract=LOCAL_CONTRACT)

    def test_local_contract_forum_drift_fails_closed(self):
        contract = json.loads(json.dumps(LOCAL_CONTRACT))
        contract["forum"]["repository_view"]["mode"] = "LIVE_MIRROR"
        with self.assertRaisesRegex(RoutingError, "local_contract_forum_repository_view_mismatch"):
            validate_local_contract(REGISTRY, project_id="alpha", contract=contract)

    def test_forum_namespace_and_locator_must_agree(self):
        registry = json.loads(json.dumps(REGISTRY))
        registry["projects"]["alpha"]["forum_locator"]["namespace"] = "beta::messages"
        with self.assertRaisesRegex(RoutingError, "forum_locator_namespace_mismatch"):
            validate_registry(registry)

    def test_none_repository_view_requires_null_path(self):
        registry = json.loads(json.dumps(REGISTRY))
        registry["projects"]["alpha"]["forum_locator"]["repository_view"] = {"mode": "NONE", "path": "fake/messages"}
        with self.assertRaisesRegex(RoutingError, "forum_repository_view_path_must_be_null"):
            validate_registry(registry)

    def test_unknown_project_fails_closed(self):
        with self.assertRaisesRegex(RoutingError, "unknown_project"):
            resolve_route(REGISTRY, project_id="beta", role_id="primary", current_repository="owner/beta")

    def test_unknown_role_fails_closed(self):
        with self.assertRaisesRegex(RoutingError, "unknown_or_unauthorized_role"):
            resolve_route(REGISTRY, project_id="alpha", role_id="admin", current_repository="owner/alpha")

    def test_repository_mismatch_fails_closed(self):
        with self.assertRaisesRegex(RoutingError, "repository_identity_mismatch"):
            resolve_route(REGISTRY, project_id="alpha", role_id="primary", current_repository="owner/beta")

    def test_stable_repository_id_mismatch_fails_closed(self):
        with self.assertRaisesRegex(RoutingError, "repository_stable_id_mismatch"):
            resolve_route(REGISTRY, project_id="alpha", role_id="primary", current_repository="owner/alpha", current_repository_id=999)

    def test_non_fail_closed_registry_is_rejected(self):
        registry = dict(REGISTRY)
        registry["mode"] = "PERMISSIVE"
        with self.assertRaisesRegex(RoutingError, "registry_not_fail_closed"):
            resolve_route(registry, project_id="alpha", role_id="primary", current_repository="owner/alpha")

    def test_duplicate_repository_binding_is_rejected(self):
        registry = json.loads(json.dumps(REGISTRY))
        beta = json.loads(json.dumps(registry["projects"]["alpha"]))
        beta.update({"repository_id": 202, "forum_namespace": "beta::messages", "artifact_namespace": "beta::artifacts"})
        beta["forum_locator"]["namespace"] = "beta::messages"
        registry["projects"]["beta"] = beta
        with self.assertRaisesRegex(RoutingError, "duplicate_repository_binding"):
            validate_registry(registry)

    def test_unsafe_handoff_path_is_rejected(self):
        registry = json.loads(json.dumps(REGISTRY))
        registry["projects"]["alpha"]["handoff_paths"] = ["../foreign/messages"]
        with self.assertRaisesRegex(RoutingError, "unsafe_handoff_path"):
            validate_registry(registry)

    def test_real_registry_and_local_contract_validate_v14(self):
        registry = json.loads((ROOT / "PROJECT_ROLE_ROUTING_REGISTRY.json").read_text())
        validate_registry(registry)
        self.assertEqual(registry.get("routing_contract_version"), "1.4.0")
        self.assertIn("fold7-power-lab", registry["projects"])
        self.assertIn("ai-behaviour-control-lab", registry["projects"])
        awareness = registry["communication_awareness"]
        self.assertTrue(awareness["required_on_startup"])
        for project in registry["projects"].values():
            self.assertIsInstance(project.get("repository_id"), int)
            self.assertEqual(project.get("local_contract_path"), "AGENT_BOOTSTRAP.json")
            self.assertEqual(project.get("routing_contract_version"), "1.4.0")
            self.assertEqual(project["forum_locator"]["authority"], "INTERNAL_ARTIFACTORY")
            self.assertEqual(project["roles"], ["primary", "manager", "research"])
            self.assertIn("MASTER_HANDOFF.json", project["handoff_paths"])
            self.assertEqual(project["master_handoff_path"], "MASTER_HANDOFF.json")
        local_contract = json.loads((ROOT / "AGENT_BOOTSTRAP.json").read_text())
        validate_local_contract(registry, project_id="intercommunicationsenhancements", contract=local_contract)
        self.assertEqual(local_contract.get("communication_awareness"), awareness)

    def test_v14_rejects_role_mode_overlap(self):
        registry = json.loads((ROOT / "PROJECT_ROLE_ROUTING_REGISTRY.json").read_text())
        registry["projects"]["benefitflow"]["execution_modes"].append("research")
        with self.assertRaisesRegex(RoutingError, "role_execution_mode_overlap"):
            validate_registry(registry)

    def test_v14_requires_master_handoff_in_handoff_paths(self):
        registry = json.loads((ROOT / "PROJECT_ROLE_ROUTING_REGISTRY.json").read_text())
        registry["projects"]["duo-open"]["handoff_paths"].remove("MASTER_HANDOFF.json")
        with self.assertRaisesRegex(RoutingError, "master_handoff_missing_from_handoff_paths"):
            validate_registry(registry)

    def test_v14_local_contract_cannot_disable_master_handoff(self):
        registry = json.loads((ROOT / "PROJECT_ROLE_ROUTING_REGISTRY.json").read_text())
        contract = json.loads((ROOT / "AGENT_BOOTSTRAP.json").read_text())
        contract["master_handoff"]["required_before_mutation"] = False
        with self.assertRaisesRegex(RoutingError, "local_master_handoff_gate_disabled"):
            validate_local_contract(registry, project_id="intercommunicationsenhancements", contract=contract)

    def test_v13_requires_communication_awareness(self):
        registry = json.loads((ROOT / "PROJECT_ROLE_ROUTING_REGISTRY.json").read_text())
        registry.pop("communication_awareness")
        with self.assertRaisesRegex(RoutingError, "missing_communication_awareness"):
            validate_registry(registry)

    def test_v13_rejects_permissive_visibility_default(self):
        registry = json.loads((ROOT / "PROJECT_ROLE_ROUTING_REGISTRY.json").read_text())
        registry["communication_awareness"]["default_visibility_claim"] = "FULL"
        with self.assertRaisesRegex(RoutingError, "unsafe_default_visibility_claim"):
            validate_registry(registry)

    def test_routing_contract_is_dependency_closed_for_role_packages(self):
        dependency_map = json.loads((ROOT / "packaging" / "agent_package_dependencies.json").read_text())
        shared = set(dependency_map["shared_patterns"])
        for expected in ("PROJECT_ROLE_ROUTING_REGISTRY.json", "AGENT_BOOTSTRAP.json", "MASTER_HANDOFF.json", "bootstrap/PROJECT_ROLE_DISCOVERY.md", "bootstrap/IDENTITY_GATE.md", "org_agent_mesh/*.py", "protocols/*.md", "schemas/*.json"):
            self.assertIn(expected, shared)


if __name__ == "__main__":
    unittest.main()
