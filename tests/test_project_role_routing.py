import unittest

from org_agent_mesh.project_role_routing import RoutingError, resolve_route


REGISTRY = {
    "mode": "FAIL_CLOSED",
    "projects": {
        "alpha": {
            "repository": "owner/alpha",
            "forum_namespace": "alpha::messages",
            "artifact_namespace": "alpha::artifacts",
            "handoff_paths": [".interagent/messages", "PROJECT_MANIFEST.json"],
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
        )
        self.assertEqual(route.repository, "owner/alpha")
        self.assertEqual(route.forum_namespace, "alpha::messages")
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

    def test_non_fail_closed_registry_is_rejected(self):
        registry = dict(REGISTRY)
        registry["mode"] = "PERMISSIVE"
        with self.assertRaisesRegex(RoutingError, "registry_not_fail_closed"):
            resolve_route(registry, project_id="alpha", role_id="primary", current_repository="owner/alpha")


if __name__ == "__main__":
    unittest.main()
