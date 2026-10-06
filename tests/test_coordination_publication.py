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
            artifactory_namespace="/DuoOpen-AgentBus/messages",
        )

    def test_primary_can_publish_internal_message_without_token(self):
        permit = issue_coordination_publication_permit(
            actor_project_id="duo-open",
            actor_role="PRIMARY",
            actor_capabilities=[CAPABILITY],
            route=self.route,
            target_repository="boberino93-bit/duo-open",
            target_artifactory_namespace="/DuoOpen-AgentBus/messages",
        )
        self.assertFalse(permit.token_required)
        self.assertTrue(permit.artifactory_allowed)
        self.assertFalse(permit.authority_conveyed)

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
                target_artifactory_namespace="/DuoOpen-AgentBus/messages",
            )

    def test_wrong_artifactory_namespace_is_denied(self):
        with self.assertRaises(ProjectScopeError):
            require_coordination_publication(
                actor_project_id="duo-open",
                actor_role="PRIMARY",
                actor_capabilities=[CAPABILITY],
                route=self.route,
                target_repository="boberino93-bit/duo-open",
                target_artifactory_namespace="BenefitFlow-AgentBus/forum/",
            )


if __name__ == "__main__":
    unittest.main()
