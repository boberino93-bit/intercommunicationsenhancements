import unittest

from org_agent_mesh.communication_awareness import assess_communication_visibility
from org_agent_mesh.project_role_routing import ResolvedRoute, RoutingError


def route(view_mode="SNAPSHOT_BACKUP", view_path="agentbus/messages"):
    return ResolvedRoute(
        project_id="alpha",
        role_id="research",
        repository="owner/alpha",
        repository_id=101,
        forum_namespace="alpha::messages",
        forum_authority="INTERNAL_ARTIFACTORY",
        forum_repository_view_mode=view_mode,
        forum_repository_view_path=view_path,
        artifact_namespace="alpha::artifacts",
        handoff_paths=("START_HERE.md",),
        local_contract_path="AGENT_BOOTSTRAP.json",
        routing_contract_version="1.3.0",
    )


class CommunicationAwarenessTests(unittest.TestCase):
    def test_direct_partial_never_claims_full_visibility(self):
        result = assess_communication_visibility(
            route(),
            direct_forum_access=True,
            direct_forum_namespace="alpha::messages",
        )
        self.assertEqual(result.access_mode, "DIRECT")
        self.assertFalse(result.full_project_forum_visibility_proven)
        self.assertEqual(result.coverage, "PARTIAL_REGISTERED_PROJECT_FORUM")

    def test_direct_full_scope_may_claim_full_registered_forum_only(self):
        result = assess_communication_visibility(
            route(),
            direct_forum_access=True,
            direct_forum_namespace="alpha::messages",
            direct_scope_complete=True,
        )
        self.assertTrue(result.full_project_forum_visibility_proven)
        self.assertEqual(result.coverage, "FULL_REGISTERED_PROJECT_FORUM")

    def test_wrong_direct_namespace_blocks_mutation(self):
        result = assess_communication_visibility(
            route(),
            direct_forum_access=True,
            direct_forum_namespace="beta::messages",
        )
        self.assertEqual(result.access_mode, "CONFLICT")
        self.assertTrue(result.mutation_blocked)

    def test_snapshot_is_not_live(self):
        result = assess_communication_visibility(
            route(), repository_view_observed=True, repository_view_fresh=True
        )
        self.assertEqual(result.access_mode, "SNAPSHOT_ONLY")
        self.assertFalse(result.authoritative_live_access)

    def test_live_mirror_remains_non_authoritative(self):
        result = assess_communication_visibility(
            route("LIVE_MIRROR", "mirror/messages"),
            repository_view_observed=True,
            repository_view_fresh=True,
        )
        self.assertEqual(result.access_mode, "LIVE_MIRROR")
        self.assertFalse(result.authoritative_live_access)
        self.assertFalse(result.full_project_forum_visibility_proven)

    def test_stale_live_mirror_is_explicit(self):
        result = assess_communication_visibility(
            route("LIVE_MIRROR", "mirror/messages"),
            repository_view_observed=True,
            repository_view_fresh=False,
        )
        self.assertEqual(result.access_mode, "STALE_MIRROR")

    def test_handoff_only_is_explicit(self):
        result = assess_communication_visibility(route(), handoff_observed=True)
        self.assertEqual(result.access_mode, "HANDOFF_ONLY")

    def test_none_is_explicit(self):
        result = assess_communication_visibility(route())
        self.assertEqual(result.access_mode, "NONE")

    def test_full_scope_requires_direct_access(self):
        with self.assertRaisesRegex(RoutingError, "full_scope_without_direct_forum_access"):
            assess_communication_visibility(route(), direct_scope_complete=True)

    def test_none_view_rejects_claimed_repository_view(self):
        with self.assertRaisesRegex(RoutingError, "unexpected_repository_forum_view"):
            assess_communication_visibility(
                route("NONE", None), repository_view_observed=True
            )


if __name__ == "__main__":
    unittest.main()
