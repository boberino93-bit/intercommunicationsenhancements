import json
from pathlib import Path
import unittest

from org_agent_mesh.project_role_routing import RoutingError, resolve_route, validate_registry


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = {
    "schema": "org-agent-mesh/project-role-routing-registry/v1",
    "mode": "FAIL_CLOSED",
    "projects": {
        "alpha": {
            "repository": "owner/alpha",
            "repository_id": 101,
            "forum_namespace": "alpha::messages",
            "artifact_namespace": "alpha::artifacts",
            "handoff_paths": [".interagent/messages", "PROJECT_MANIFEST.json"],
            "local_contract_path": "AGENT_BOOTSTRAP.json",
            "routing_contract_version": "1.1.0",
            "roles": ["primary", "manager", "research"],
        }
    },
}


class ProjectRoleRoutingTests(unittest.TestCase):
    def test_valid_route_resolves_and_acknowledges(self):
        route = resolve_route(
            REGISTRY,
            project_id="alpha",
            role_id="research",
            current_repository="owner/alpha",
            current_repository_id=101,
        )
        self.assertEqual(route.repository, "owner/alpha")
        self.assertEqual(route.repository_id, 101)
        self.assertEqual(route.forum_namespace, "alpha::messages")
        self.assertEqual(route.local_contract_path, "AGENT_BOOTSTRAP.json")
        self.assertIn("IDENTITY RESOLVED: project=alpha; role=research", route.acknowledgement("handoff-7"))

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
            resolve_route(
                REGISTRY,
                project_id="alpha",
                role_id="primary",
                current_repository="owner/alpha",
                current_repository_id=999,
            )

    def test_non_fail_closed_registry_is_rejected(self):
        registry = dict(REGISTRY)
        registry["mode"] = "PERMISSIVE"
        with self.assertRaisesRegex(RoutingError, "registry_not_fail_closed"):
            resolve_route(registry, project_id="alpha", role_id="primary", current_repository="owner/alpha")

    def test_duplicate_repository_binding_is_rejected(self):
        registry = json.loads(json.dumps(REGISTRY))
        registry["projects"]["beta"] = {
            **registry["projects"]["alpha"],
            "repository_id": 202,
            "forum_namespace": "beta::messages",
            "artifact_namespace": "beta::artifacts",
        }
        with self.assertRaisesRegex(RoutingError, "duplicate_repository_binding"):
            validate_registry(registry)

    def test_unsafe_handoff_path_is_rejected(self):
        registry = json.loads(json.dumps(REGISTRY))
        registry["projects"]["alpha"]["handoff_paths"] = ["../foreign/messages"]
        with self.assertRaisesRegex(RoutingError, "unsafe_handoff_path"):
            validate_registry(registry)

    def test_real_registry_validates(self):
        registry = json.loads((ROOT / "PROJECT_ROLE_ROUTING_REGISTRY.json").read_text())
        validate_registry(registry)
        for project in registry["projects"].values():
            self.assertIsInstance(project.get("repository_id"), int)
            self.assertEqual(project.get("local_contract_path"), "AGENT_BOOTSTRAP.json")
            self.assertEqual(project.get("routing_contract_version"), "1.1.0")

    def test_routing_contract_is_dependency_closed_for_role_packages(self):
        dependency_map = json.loads((ROOT / "packaging" / "agent_package_dependencies.json").read_text())
        shared = set(dependency_map["shared_patterns"])
        self.assertIn("PROJECT_ROLE_ROUTING_REGISTRY.json", shared)
        self.assertIn("AGENT_BOOTSTRAP.json", shared)
        self.assertIn("bootstrap/PROJECT_ROLE_DISCOVERY.md", shared)
        self.assertIn("bootstrap/IDENTITY_GATE.md", shared)
        self.assertIn("org_agent_mesh/*.py", shared)


if __name__ == "__main__":
    unittest.main()
