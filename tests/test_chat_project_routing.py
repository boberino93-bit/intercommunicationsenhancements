import unittest

from org_agent_mesh.chat_project_routing import ChatProjectRouter


class FakeAdapter:
    def __init__(self, direct=True):
        self.direct = direct
        self.projects = {}
        self.created = 0
        self.moves = 0

    def supports_direct_create(self):
        return self.direct

    def create_conversation(self, *, title, project):
        self.created += 1
        conversation_id = f"c{self.created}"
        self.projects[conversation_id] = project
        return conversation_id

    def move_conversation(self, *, conversation_id, project):
        self.moves += 1
        self.projects[conversation_id] = project

    def detect_project(self, *, conversation_id):
        return self.projects.get(conversation_id)


class ChatProjectRoutingTests(unittest.TestCase):
    def test_duo_direct_create(self):
        adapter = FakeAdapter(direct=True)
        result = ChatProjectRouter(adapter).assign(
            agent_id="duo-researcher-1",
            agent_type="research",
            project_id="duo-open",
            title="Duo researcher",
        )
        self.assertEqual(result.status, "OK")
        self.assertEqual(result.detected_project, "Duo Screen")
        self.assertEqual(result.method, "direct-create")

    def test_master_remains_global(self):
        adapter = FakeAdapter(direct=True)
        result = ChatProjectRouter(adapter).assign(
            agent_id="master",
            agent_type="master",
            project_id=None,
            title="Master",
            roaming=True,
        )
        self.assertEqual(result.status, "SKIPPED")
        self.assertIsNone(result.detected_project)

    def test_unknown_project_fails_without_guess(self):
        adapter = FakeAdapter(direct=True)
        result = ChatProjectRouter(adapter).assign(
            agent_id="unknown-agent",
            agent_type="research",
            project_id="unknown-project",
            title="Unknown",
        )
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(adapter.created, 0)

    def test_already_assigned_is_idempotent(self):
        adapter = FakeAdapter(direct=True)
        conversation_id = adapter.create_conversation(title="Warp", project="Warp-Propulsion-lab")
        result = ChatProjectRouter(adapter).assign(
            agent_id="warp-researcher",
            agent_type="research",
            project_id="warp-propulsion-lab",
            title="Warp",
            conversation_id=conversation_id,
        )
        self.assertEqual(result.status, "OK")
        self.assertEqual(result.method, "already-assigned")
        self.assertEqual(adapter.moves, 0)

    def test_move_fallback_is_verified(self):
        adapter = FakeAdapter(direct=False)
        result = ChatProjectRouter(adapter).assign(
            agent_id="benefitflow-researcher",
            agent_type="research",
            project_id="benefitflow",
            title="BenefitFlow researcher",
        )
        self.assertEqual(result.status, "OK")
        self.assertEqual(result.detected_project, "Benefitflow")
        self.assertGreaterEqual(adapter.moves, 1)


if __name__ == "__main__":
    unittest.main()
