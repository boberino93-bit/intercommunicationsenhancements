import unittest

from org_agent_mesh.coordination_publication import (
    CoordinationPublicationError,
    CoordinationRoute,
    require_coordination_publication,
)
from org_agent_mesh.project_scope import ProjectScopeError


def route(project_id="duo-open", repository="boberino93-bit/duo-open", namespace="/DuoOpen-AgentBus/messages"):
    return CoordinationRoute(project_id, repository, namespace)


class CoordinationPublicationTests(unittest.TestCase):
    def test_research_can_publish_to_own_project_forum_with_legacy_message_capability(self):
        self.assertTrue(require_coordination_publication(
            actor_project_id="duo-open",
            actor_role="RESEARCH",
            actor_capabilities=["PUBLISH_MESSAGE"],
            route=route(),
            target_repository="boberino93-bit/duo-open",
            target_artifactory_namespace="/DuoOpen-AgentBus/messages",
        ))

    def test_manager_can_create_github_backup_only_under_registered_prefix(self):
        self.assertTrue(require_coordination_publication(
            actor_project_id="duo-open",
            actor_role="MANAGER",
            actor_capabilities=["PUBLISH_MESSAGE"],
            route=route(),
            target_repository="boberino93-bit/duo-open",
            github_backup_path="agentbus-backup/coordination-messages/20261005T180000Z_manager.json",
        ))

    def test_backup_path_escape_and_non_backup_paths_are_denied(self):
        paths = [
            "README.md",
            "src/main.py",
            "agentbus-backup/other/message.json",
            "agentbus-backup/coordination-messages/../production.json",
            "/agentbus-backup/coordination-messages/message.json",
        ]
        for path in paths:
            with self.subTest(path=path):
                with self.assertRaises(CoordinationPublicationError):
                    require_coordination_publication(
                        actor_project_id="duo-open",
                        actor_role="RESEARCH",
                        actor_capabilities=["PUBLISH_MESSAGE"],
                        route=route(),
                        target_repository="boberino93-bit/duo-open",
                        github_backup_path=path,
                    )

    def test_foreign_repository_is_denied(self):
        with self.assertRaises(ProjectScopeError):
            require_coordination_publication(
                actor_project_id="duo-open",
                actor_role="MANAGER",
                actor_capabilities=["PUBLISH_MESSAGE"],
                route=route(),
                target_repository="boberino93-bit/benefitflow",
                github_backup_path="agentbus-backup/coordination-messages/message.json",
            )

    def test_foreign_artifactory_namespace_is_denied(self):
        with self.assertRaises(ProjectScopeError):
            require_coordination_publication(
                actor_project_id="duo-open",
                actor_role="RESEARCH",
                actor_capabilities=["PUBLISH_MESSAGE"],
                route=route(),
                target_repository="boberino93-bit/duo-open",
                target_artifactory_namespace="BenefitFlow-AgentBus/forum/",
            )

    def test_non_create_operations_are_denied(self):
        for operation in ["OVERWRITE", "DELETE", "RENAME", "MOVE"]:
            with self.subTest(operation=operation):
                with self.assertRaises(CoordinationPublicationError):
                    require_coordination_publication(
                        actor_project_id="duo-open",
                        actor_role="MANAGER",
                        actor_capabilities=["PUBLISH_MESSAGE"],
                        route=route(),
                        target_repository="boberino93-bit/duo-open",
                        github_backup_path="agentbus-backup/coordination-messages/message.json",
                        operation=operation,
                    )

    def test_authority_smuggling_is_denied(self):
        with self.assertRaises(CoordinationPublicationError):
            require_coordination_publication(
                actor_project_id="duo-open",
                actor_role="RESEARCH",
                actor_capabilities=["PUBLISH_MESSAGE"],
                route=route(),
                target_repository="boberino93-bit/duo-open",
                github_backup_path="agentbus-backup/coordination-messages/message.json",
                authority_conveyed=True,
            )

    def test_wrong_role_is_denied(self):
        with self.assertRaises(CoordinationPublicationError):
            require_coordination_publication(
                actor_project_id="duo-open",
                actor_role="PRIMARY",
                actor_capabilities=["PUBLISH_MESSAGE"],
                route=route(),
                target_repository="boberino93-bit/duo-open",
                github_backup_path="agentbus-backup/coordination-messages/message.json",
            )

    def test_xrp_artifactory_namespace_must_not_be_invented(self):
        xrp = CoordinationRoute("xrp-thesis", "boberino93-bit/XRPTHESIS", None)
        with self.assertRaises(CoordinationPublicationError):
            require_coordination_publication(
                actor_project_id="xrp-thesis",
                actor_role="RESEARCH",
                actor_capabilities=["PUBLISH_MESSAGE"],
                route=xrp,
                target_repository="boberino93-bit/XRPTHESIS",
                target_artifactory_namespace="/XRPTHESIS-AgentBus/messages",
            )


if __name__ == "__main__":
    unittest.main()
