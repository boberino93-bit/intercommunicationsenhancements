import unittest

from org_agent_mesh.supervision import (
    AgentControlState,
    AgentRecord,
    AgentRegistrationError,
    AgentRegistry,
    AuthorityError,
    AuthorityService,
    ReasonCode,
    Supervisor,
    SupervisorIdentity,
    SupervisoryAction,
    may_spawn_replacement,
)


class SupervisionTests(unittest.TestCase):
    def setUp(self):
        self.registry = AgentRegistry()
        self.master = AgentRecord("master", "master", roaming=True)
        self.registry.register(self.master)
        self.primary = AgentRecord("duo-primary", "primary", project_id="duo-open")
        self.registry.register(self.primary)
        self.manager = AgentRecord(
            "duo-manager", "manager", project_id="duo-open", parent_agent_id="duo-primary"
        )
        self.registry.register(self.manager)
        self.researcher = AgentRecord(
            "duo-researcher", "research", project_id="duo-open", parent_agent_id="duo-manager"
        )
        self.registry.register(self.researcher)
        self.warp = AgentRecord("warp-researcher", "research", project_id="warp-propulsion-lab")
        self.registry.register(self.warp)
        self.supervisor = Supervisor(self.registry, AuthorityService())

    def test_master_global_stop(self):
        self.supervisor.act(
            SupervisorIdentity("master-controller", "master"),
            "warp-researcher",
            SupervisoryAction.STOP,
            ReasonCode.GOAL_MISALIGNMENT,
            "No longer advances the governing objective",
        )
        self.assertEqual(self.warp.state, AgentControlState.STOP_REQUESTED)
        self.assertFalse(self.warp.allow_respawn)

    def test_primary_cannot_control_foreign_project(self):
        with self.assertRaises(AuthorityError):
            self.supervisor.act(
                SupervisorIdentity("duo-primary-controller", "primary", "duo-open"),
                "warp-researcher",
                SupervisoryAction.STOP,
                ReasonCode.PROJECT_GOAL_CONFLICT,
                "Foreign project",
            )

    def test_stop_tree_propagates_and_blocks_child_spawn(self):
        self.supervisor.act(
            SupervisorIdentity("master-controller", "master"),
            "duo-manager",
            SupervisoryAction.STOP_TREE,
            ReasonCode.SUPERSEDED,
            "Branch is no longer required",
        )
        self.assertEqual(self.manager.state, AgentControlState.STOP_REQUESTED)
        self.assertEqual(self.researcher.state, AgentControlState.STOP_REQUESTED)
        self.assertFalse(self.manager.allow_respawn)
        self.assertFalse(self.researcher.allow_respawn)
        with self.assertRaises(AgentRegistrationError):
            self.registry.register(
                AgentRecord(
                    "duo-child-new",
                    "research",
                    project_id="duo-open",
                    parent_agent_id="duo-manager",
                )
            )

    def test_redirect_increments_revision(self):
        before = self.researcher.assignment_revision
        self.supervisor.act(
            SupervisorIdentity("duo-primary-controller", "primary", "duo-open"),
            "duo-researcher",
            SupervisoryAction.REDIRECT,
            ReasonCode.INSTRUCTION_DRIFT,
            "Current direction is useful but wrong",
            redirect_instruction="Validate the current architecture instead",
        )
        self.assertEqual(self.researcher.state, AgentControlState.REDIRECT_REQUESTED)
        self.assertEqual(self.researcher.assignment_revision, before + 1)

    def test_intentional_stop_prevents_blind_scheduler_respawn(self):
        self.researcher.allow_respawn = False
        self.researcher.assignment_revision = 4
        self.assertFalse(
            may_spawn_replacement(self.researcher, new_task_revision=4, authorization_source="SCHEDULE")
        )
        self.assertFalse(
            may_spawn_replacement(self.researcher, new_task_revision=5, authorization_source="SCHEDULE")
        )

    def test_master_new_revision_and_user_override_can_restart(self):
        self.researcher.allow_respawn = False
        self.researcher.assignment_revision = 4
        self.assertTrue(
            may_spawn_replacement(self.researcher, new_task_revision=5, authorization_source="MASTER")
        )
        self.assertTrue(
            may_spawn_replacement(self.researcher, new_task_revision=4, authorization_source="USER")
        )

    def test_master_record_must_be_roaming(self):
        with self.assertRaises(AgentRegistrationError):
            AgentRecord("bad-master", "master", roaming=False)


if __name__ == "__main__":
    unittest.main()
