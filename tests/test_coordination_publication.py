import unittest

from org_agent_mesh.coordination_publication import (
    CAPABILITY,
    CoordinationPublicationError,
    CoordinationRoute,
    issue_coordination_publication_permit,
    require_coordination_publication,
)
from org_agent_mesh.project_scope import ProjectScopeError


class CoordinationPublicationTests(unittest.TestCase):
    def setUp(self):
        self.route = CoordinationRoute(
            project_id="duo-open",
            repository="boberino93-bit/duo-open",
            agentbus_namespace="/DuoOpen-AgentBus/messages",
        )

    def test_primary_can_publish_internal_agentbus_message_without_token(self):
        permit = issue_coordination_publication_permit(
            actor_project_id="duo-open",
            actor_role="PRIMARY",
            actor_capabilities=[CAPABILITY],
            route=self.route,
            target_repository="boberino93-bit/duo-open",
            target_agentbus_namespace="/DuoOpen-AgentBus/messages",
        )
        self.assertFalse(permit.token_required)
        self.assertTrue(permit.agentbus_allowed)
        self.assertTrue(permit.artifactory_allowed)
        self.assertFalse(permit.authority_conveyed)

    def test_legacy_artifactory_alias_resolves_to_same_agentbus_namespace(self):
        route = CoordinationRoute(
            project_id="duo-open",
            repository="boberino93-bit/duo-open",
            artifactory_namespace="/DuoOpen-AgentBus/messages",
        )
        self.assertEqual(route.resolved_agentbus_namespace, "/DuoOpen-AgentBus/messages")
        self.assertTrue(require_coordination_publication(
            actor_project_id="duo-open",
            actor_role="MANAGER",
            actor_capabilities=[CAPABILITY],
            route=route,
            target_repository="boberino93-bit/duo-open",
            target_artifactory_namespace="/DuoOpen-AgentBus/messages",
        ))

    def test_manager_can_create_new_backup_message(self):
        self.assertTrue(require_coordination_publication(
            actor_project_id="duo-open",
            actor_role="MANAGER",
            actor_capabilities=[CAPABILITY],
            route=self.route,
            target_repository="boberino93-bit/duo-open",
            github_backup_path="agentbus-backup/coordination-messages/20261006T000000Z__manager.json",
        ))

    def test_workflow_dispatch_is_denied(self):
        with self.assertRaises(CoordinationPublicationError):
            require_coordination_publication(
                actor_project_id="duo-open",
                actor_role="PRIMARY",
                actor_capabilities=[CAPABILITY],
                route=self.route,
                target_repository="boberino93-bit/duo-open",
                github_backup_path="agentbus-backup/coordination-messages/msg.json",
                github_operation="WORKFLOW_DISPATCH",
            )

    def test_overwrite_is_denied(self):
        with self.assertRaises(CoordinationPublicationError):
            require_coordination_publication(
                actor_project_id="duo-open",
                actor_role="RESEARCH",
                actor_capabilities=[CAPABILITY],
                route=self.route,
                target_repository="boberino93-bit/duo-open",
                github_backup_path="agentbus-backup/coordination-messages/msg.json",
                github_operation="UPDATE_FILE",
            )

    def test_cross_project_target_is_denied(self):
        with self.assertRaises(ProjectScopeError):
            require_coordination_publication(
                actor_project_id="duo-open",
                actor_role="PRIMARY",
                actor_capabilities=[CAPABILITY],
                route=self.route,
                target_repository="boberino93-bit/benefitflow",
                target_agentbus_namespace="/DuoOpen-AgentBus/messages",
            )

    def test_wrong_agentbus_namespace_is_denied(self):
        with self.assertRaises(ProjectScopeError):
            require_coordination_publication(
                actor_project_id="duo-open",
                actor_role="PRIMARY",
                actor_capabilities=[CAPABILITY],
                route=self.route,
                target_repository="boberino93-bit/duo-open",
                target_agentbus_namespace="BenefitFlow-AgentBus/forum/",
            )

    def test_conflicting_aliases_are_denied(self):
        with self.assertRaises(CoordinationPublicationError):
            CoordinationRoute(
                project_id="duo-open",
                repository="boberino93-bit/duo-open",
                agentbus_namespace="/DuoOpen-AgentBus/messages",
                artifactory_namespace="/different/messages",
            )


if __name__ == "__main__":
    unittest.main()
