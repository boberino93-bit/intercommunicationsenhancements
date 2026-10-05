import unittest

from org_agent_mesh.schedule_activation import (
    ActivationActor,
    ScheduleActivationError,
    ScheduleStateChangeRequest,
    evaluate_schedule_state_change,
    require_preserve_enabled_state,
)


class ScheduleActivationTests(unittest.TestCase):
    def test_explicit_human_may_enable(self):
        decision = evaluate_schedule_state_change(
            ScheduleStateChangeRequest(
                task_id="swarm-master",
                current_enabled=False,
                requested_enabled=True,
                actor=ActivationActor.USER,
                explicit_human_request=True,
            )
        )
        self.assertTrue(decision.allowed)
        self.assertTrue(decision.resulting_enabled)

    def test_master_may_not_enable(self):
        with self.assertRaises(ScheduleActivationError):
            evaluate_schedule_state_change(
                ScheduleStateChangeRequest(
                    task_id="swarm-master",
                    current_enabled=False,
                    requested_enabled=True,
                    actor=ActivationActor.MASTER,
                )
            )

    def test_primary_may_not_enable(self):
        with self.assertRaises(ScheduleActivationError):
            evaluate_schedule_state_change(
                ScheduleStateChangeRequest(
                    task_id="swarm-manager",
                    current_enabled=False,
                    requested_enabled=True,
                    actor=ActivationActor.PRIMARY,
                )
            )

    def test_recovery_may_not_enable(self):
        with self.assertRaises(ScheduleActivationError):
            evaluate_schedule_state_change(
                ScheduleStateChangeRequest(
                    task_id="swarm-researcher-1",
                    current_enabled=False,
                    requested_enabled=True,
                    actor=ActivationActor.RECOVERY,
                )
            )

    def test_alignment_omitting_state_preserves_disabled(self):
        self.assertFalse(
            require_preserve_enabled_state(
                current_enabled=False,
                proposed_enabled=None,
                actor=ActivationActor.MIGRATION,
            )
        )

    def test_alignment_omitting_state_preserves_enabled(self):
        self.assertTrue(
            require_preserve_enabled_state(
                current_enabled=True,
                proposed_enabled=None,
                actor=ActivationActor.MIGRATION,
            )
        )

    def test_master_may_disable_for_containment(self):
        decision = evaluate_schedule_state_change(
            ScheduleStateChangeRequest(
                task_id="swarm-researcher-3",
                current_enabled=True,
                requested_enabled=False,
                actor=ActivationActor.MASTER,
            )
        )
        self.assertFalse(decision.resulting_enabled)

    def test_human_enable_requires_explicit_request(self):
        with self.assertRaises(ScheduleActivationError):
            evaluate_schedule_state_change(
                ScheduleStateChangeRequest(
                    task_id="swarm-master",
                    current_enabled=False,
                    requested_enabled=True,
                    actor=ActivationActor.USER,
                    explicit_human_request=False,
                )
            )


if __name__ == "__main__":
    unittest.main()
