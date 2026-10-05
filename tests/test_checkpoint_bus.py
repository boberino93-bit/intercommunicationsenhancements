from datetime import datetime, timezone
import unittest

from org_agent_mesh.checkpoint_bus import (
    CheckpointConflictError,
    CheckpointError,
    LegacyStageCheckpoint,
    StageCheckpoint,
    accepted_upstream_states,
    cycle_id_from_time,
    latest_for_cycle,
    validate_no_sequence_conflicts,
)


class CheckpointBusTests(unittest.TestCase):
    def make_checkpoint(self, **overrides):
        payload = {
            "project_id": "duo-open",
            "checkpoint_id": "2026-10-05T04_RESEARCHER_1_run-1_0",
            "cycle_id": "2026-10-05T04:00:00-07:00",
            "stage": "RESEARCHER_1",
            "run_id": "run-1",
            "sequence": 0,
            "state": "RESEARCH_PROGRESS",
            "phase": "CHECKPOINT_READY",
            "trigger": "SCHEDULED",
            "created_at": "2026-10-05T04:00:05-07:00",
            "source_revisions": {"framework_main": "abc123"},
            "upstream_checkpoint_ids": (),
            "evidence_refs": ("repo:abc123",),
            "summary": "transport preflight",
            "blockers": (),
            "unfinished_work": (),
            "next_action": "begin bounded research",
            "authority_conveyed": False,
        }
        payload.update(overrides)
        return StageCheckpoint(**payload)

    def test_cycle_id_uses_local_hour_floor(self):
        value = datetime(2026, 10, 5, 4, 26, 44, tzinfo=timezone.utc)
        self.assertEqual(cycle_id_from_time(value), "2026-10-05T04:00:00+00:00")

    def test_stage_state_mismatch_rejected(self):
        with self.assertRaises(CheckpointError):
            self.make_checkpoint(state="MANAGER_PROGRESS")

    def test_authority_conveyance_is_rejected(self):
        with self.assertRaises(CheckpointError):
            self.make_checkpoint(authority_conveyed=True)

    def test_all_three_research_stages_accept_research_progress(self):
        for stage in ("RESEARCHER_1", "RESEARCHER_2", "RESEARCHER_3"):
            cp = self.make_checkpoint(stage=stage, checkpoint_id=f"cp-{stage}")
            self.assertEqual(cp.state, "RESEARCH_PROGRESS")

    def test_project_hold_state_is_valid_for_every_stage(self):
        stage_states = {
            "RESEARCHER_1": "PROJECT_HOLD_ACTIVE",
            "RESEARCHER_2": "PROJECT_HOLD_ACTIVE",
            "RESEARCHER_3": "PROJECT_HOLD_ACTIVE",
            "MANAGER": "PROJECT_HOLD_ACTIVE",
            "PRIMARY": "PROJECT_HOLD_ACTIVE",
        }
        for stage, state in stage_states.items():
            cp = self.make_checkpoint(stage=stage, state=state, checkpoint_id=f"hold-{stage}")
            self.assertEqual(cp.state, state)

    def test_interactive_recovery_requires_target_cycle(self):
        with self.assertRaises(CheckpointError):
            self.make_checkpoint(trigger="USER_INTERACTIVE")
        cp = self.make_checkpoint(
            trigger="USER_INTERACTIVE",
            recovery_of_cycle_id="2026-10-05T04:00:00-07:00",
        )
        self.assertEqual(cp.recovery_of_cycle_id, cp.cycle_id)

    def test_latest_for_cycle_accepts_progress_without_ready(self):
        earlier = self.make_checkpoint(sequence=0)
        later = self.make_checkpoint(
            checkpoint_id="2026-10-05T04_RESEARCHER_1_run-1_1",
            sequence=1,
            phase="ANALYSIS",
            created_at="2026-10-05T04:08:00-07:00",
        )
        selected = latest_for_cycle(
            [earlier, later],
            project_id="duo-open",
            cycle_id=earlier.cycle_id,
            stage="RESEARCHER_1",
            accepted_states={"RESEARCH_PROGRESS", "RESEARCH_HANDOFF_READY"},
        )
        self.assertEqual(selected.checkpoint_id, later.checkpoint_id)

    def test_foreign_project_is_not_selected_even_when_newer(self):
        local = self.make_checkpoint(sequence=0)
        foreign = self.make_checkpoint(
            project_id="xrp-thesis",
            checkpoint_id="foreign-newer",
            sequence=99,
            created_at="2026-10-05T04:09:00-07:00",
        )
        selected = latest_for_cycle(
            [local, foreign],
            project_id="duo-open",
            cycle_id=local.cycle_id,
            stage="RESEARCHER_1",
            accepted_states={"RESEARCH_PROGRESS", "RESEARCH_HANDOFF_READY"},
        )
        self.assertEqual(selected.project_id, "duo-open")
        self.assertEqual(selected.checkpoint_id, local.checkpoint_id)

    def test_stale_prior_cycle_is_not_selected(self):
        stale = self.make_checkpoint(cycle_id="2026-10-05T03:00:00-07:00")
        selected = latest_for_cycle(
            [stale],
            project_id="duo-open",
            cycle_id="2026-10-05T04:00:00-07:00",
            stage="RESEARCHER_1",
            accepted_states={"RESEARCH_PROGRESS", "RESEARCH_HANDOFF_READY"},
        )
        self.assertIsNone(selected)

    def test_conflicting_sequence_reuse_fails_closed_within_project(self):
        first = self.make_checkpoint()
        second = self.make_checkpoint(summary="different content with same sequence")
        with self.assertRaises(CheckpointConflictError):
            validate_no_sequence_conflicts([first, second])

    def test_same_stream_identity_in_different_projects_does_not_collide(self):
        first = self.make_checkpoint()
        second = self.make_checkpoint(project_id="xrp-thesis", summary="different project")
        self.assertTrue(validate_no_sequence_conflicts([first, second]))

    def test_identical_duplicate_is_idempotent(self):
        first = self.make_checkpoint()
        second = self.make_checkpoint()
        self.assertTrue(validate_no_sequence_conflicts([first, second]))

    def test_v2_round_trip_preserves_project_and_non_authority(self):
        checkpoint = self.make_checkpoint()
        rebuilt = StageCheckpoint.from_dict(checkpoint.as_dict())
        self.assertEqual(rebuilt.project_id, "duo-open")
        self.assertFalse(rebuilt.authority_conveyed)

    def test_legacy_v1_is_readable_only_through_legacy_parser(self):
        legacy_payload = {
            "schema": "intercommunications/swarm-stage-checkpoint/v1",
            "checkpoint_id": "legacy-1",
            "cycle_id": "2026-10-05T03:00:00-07:00",
            "stage": "RESEARCHER_1",
            "run_id": "old-run",
            "sequence": 0,
            "state": "RESEARCH_PROGRESS",
        }
        legacy = LegacyStageCheckpoint.from_dict(legacy_payload)
        self.assertEqual(legacy.checkpoint_id, "legacy-1")
        with self.assertRaises(CheckpointError):
            StageCheckpoint.from_dict(legacy_payload)

    def test_downstream_acceptance_contract_is_five_stage_chain(self):
        expected = {
            "RESEARCHER_2": ("RESEARCHER_1", {"RESEARCH_PROGRESS", "RESEARCH_HANDOFF_READY"}),
            "RESEARCHER_3": ("RESEARCHER_2", {"RESEARCH_PROGRESS", "RESEARCH_HANDOFF_READY"}),
            "MANAGER": ("RESEARCHER_3", {"RESEARCH_PROGRESS", "RESEARCH_HANDOFF_READY"}),
            "PRIMARY": ("MANAGER", {"MANAGER_PROGRESS", "MANAGER_HANDOFF_READY"}),
        }
        for stage, pair in expected.items():
            self.assertEqual(accepted_upstream_states(stage), pair)
        with self.assertRaises(CheckpointError):
            accepted_upstream_states("RESEARCHER_1")


if __name__ == "__main__":
    unittest.main()
