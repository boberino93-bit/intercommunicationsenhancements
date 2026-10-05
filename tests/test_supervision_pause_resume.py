import unittest

from org_agent_mesh.supervision import (
    AgentControlState,
    AgentRecord,
    AgentRegistry,
    ReasonCode,
    Supervisor,
    SupervisorIdentity,
    SupervisoryAction,
)


class PauseResumeTests(unittest.TestCase):
    def test_continue_releases_paused_agent(self):
        registry = AgentRegistry()
        target = AgentRecord("duo-researcher", "research", project_id="duo-open")
        registry.register(target)
        supervisor = Supervisor(registry)
        identity = SupervisorIdentity("duo-primary-controller", "primary", "duo-open")

        supervisor.act(
            identity,
            "duo-researcher",
            SupervisoryAction.PAUSE,
            ReasonCode.AGENT_CONFLICT,
            "Coordinate competing lanes before continuing",
        )
        self.assertEqual(target.state, AgentControlState.PAUSE_REQUESTED)

        target.state = AgentControlState.PAUSED
        supervisor.act(
            identity,
            "duo-researcher",
            SupervisoryAction.CONTINUE,
            ReasonCode.MASTER_DIRECTION,
            "Coordination complete",
        )
        self.assertEqual(target.state, AgentControlState.RUNNING)


if __name__ == "__main__":
    unittest.main()
