import unittest

from org_agent_mesh.coordination_publication import (
    CoordinationPublicationError,
    CoordinationRoute,
    require_coordination_publication,
)
from org_agent_mesh.project_scope import ProjectScopeError


def route(project_id="duo-open", repository="boberino93-bit/duo-open", namespace="/DuoOpen-AgentBus/messages"):
    return CoordinationRoute(project_id, repository, namespace)


def publish(*, role="RESEARCH", namespace="/DuoOpen-AgentBus/messages", github_path="agentbus-backup/coordination-messages/message.json", route_value=None, repository="boberino93-bit/duo-open", capabilities=("PUBLISH_MESSAGE",), operation="CREATE_NEW_MESSAGE", authority_conveyed=False):
    return require_coordination_publication(
        actor_project_id="duo-open",
        actor_role=role,
        actor_capabilities=capabilities,
        route=route_value or route(),
        target_repository=repository,
        target_artifactory_namespace=namespace,
        github_backup_path=github_path,
        operation=operation,
        authority_conveyed=authority_conveyed,
    )


class CoordinationPublicationTests(unittest.TestCase):
    def test_research_requires_both_registered_destinations(self):
        self.assertTrue(publish())

    def test_forum_only_is_denied(self):
        with self.assertRaisesRegex(CoordinationPublicationError, "DUAL_PERSISTENCE_DESTINATIONS_REQUIRED"):
            publish(github_path=None)

    def test_github_only_is_denied(self):
        with self.assertRaisesRegex(CoordinationPublicationError, "DUAL_PERSISTENCE_DESTINATIONS_REQUIRED"):
            publish(namespace=None)

    def test_primary_and_recovery_can_use_bounded_persistence_capability(self):
        self.assertTrue(publish(role="PRIMARY"))
        self.assertTrue(publish(role="RECOVERY"))

    def test_unknown_role_is_denied(self):
        with self.assertRaises(CoordinationPublicationError):
            publish(role="MASTER")

    def test_missing_capability_is_denied(self):
        with self.assertRaises(CoordinationPublicationError):
            publish(capabilities=())

    def test_backup_path_escape_and_non_backup_paths_are_denied(self):
        for path in [
            "README.md",
            "src/main.py",
            "agentbus-backup/other/message.json",
            "agentbus-backup/coordination-messages/../production.json",
            "/agentbus-backup/coordination-messages/message.json",
        ]:
            with self.subTest(path=path):
                with self.assertRaises(CoordinationPublicationError):
                    publish(github_path=path)

    def test_foreign_repository_is_denied(self):
        with self.assertRaises(ProjectScopeError):
            publish(repository="boberino93-bit/benefitflow")

    def test_foreign_artifactory_namespace_is_denied(self):
        with self.assertRaises(ProjectScopeError):
            publish(namespace="BenefitFlow-AgentBus/forum/")

    def test_non_create_operations_are_denied(self):
        for operation in ["OVERWRITE", "DELETE", "RENAME", "MOVE"]:
            with self.subTest(operation=operation):
                with self.assertRaises(CoordinationPublicationError):
                    publish(operation=operation)

    def test_authority_smuggling_is_denied(self):
        with self.assertRaises(CoordinationPublicationError):
            publish(authority_conveyed=True)

    def test_route_without_registered_forum_namespace_is_denied(self):
        incomplete = CoordinationRoute("duo-open", "boberino93-bit/duo-open", None)
        with self.assertRaisesRegex(CoordinationPublicationError, "DUAL_PERSISTENCE_ROUTE_INCOMPLETE"):
            publish(route_value=incomplete)

    def test_xrp_artifactory_namespace_must_not_be_invented_until_route_normalized(self):
        xrp = CoordinationRoute("xrp-thesis", "boberino93-bit/XRPTHESIS", None)
        with self.assertRaises(CoordinationPublicationError):
            require_coordination_publication(
                actor_project_id="xrp-thesis",
                actor_role="RESEARCH",
                actor_capabilities=["PUBLISH_MESSAGE"],
                route=xrp,
                target_repository="boberino93-bit/XRPTHESIS",
                target_artifactory_namespace="/XRPTHESIS-AgentBus/messages",
                github_backup_path="agentbus-backup/coordination-messages/message.json",
            )


if __name__ == "__main__":
    unittest.main()
