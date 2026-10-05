from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import unittest

from org_agent_mesh.project_work_control import (
    ProjectWorkControlError,
    WorkControlEvent,
    derive_project_work_state,
    require_new_mutation_allowed_by_hold_state,
    require_project_work_allowed,
)

ROOT = Path(__file__).resolve().parents[1]


class ProjectWorkControlRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((ROOT / "governance" / "PROJECT_WORK_CONTROL.json").read_text())

    def event(self, **overrides):
        payload = {
            "schema": "org-agent-mesh/project-work-control-event/v1",
            "event_id": "evt-hold-1",
            "project_id": "warp-propulsion-lab",
            "action": "HOLD",
            "hold_order_id": "hold-warp-1",
            "issued_at": "2026-10-05T07:00:00-07:00",
            "effective_at": "2026-10-05T07:00:00-07:00",
            "expires_at": "2027-01-05T07:00:00-08:00",
            "resume_policy": "MANUAL",
            "reason_code": "HUMAN_PRIORITY",
            "human_reason": "Pause project work while priorities are reassessed.",
            "metadata": {"review_note": "preserve current partial state"},
            "claimed_principal": "registered-human-principal",
            "authentication_ref": "auth-proof-ref",
            "authorization_case_id": "AUTH-hold-1",
            "preserve_partial_state": True,
            "source_revision": "abc123",
        }
        payload.update(overrides)
        return payload

    def test_active_projection_allows_work(self):
        state = derive_project_work_state(
            self.registry,
            [],
            project_id="warp-propulsion-lab",
            now=datetime.fromisoformat("2026-10-05T07:30:00-07:00"),
        )
        self.assertEqual(state.state, "ACTIVE")
        self.assertTrue(state.project_work_allowed)
        self.assertTrue(state.new_mutation_allowed_by_hold_state)
        require_project_work_allowed(state)
        require_new_mutation_allowed_by_hold_state(state)

    def test_validated_hold_blocks_project_work_and_respawn(self):
        event = WorkControlEvent.from_dict(self.event())
        state = derive_project_work_state(
            self.registry,
            [event],
            project_id="warp-propulsion-lab",
            now=datetime.fromisoformat("2026-10-05T07:30:00-07:00"),
            validated_event_ids=[event.event_id],
        )
        self.assertEqual(state.state, "HOLD")
        self.assertEqual(state.active_hold_order_id, "hold-warp-1")
        self.assertFalse(state.project_work_allowed)
        self.assertFalse(state.respawn_allowed)
        with self.assertRaisesRegex(ProjectWorkControlError, "project_work_blocked:HOLD"):
            require_project_work_allowed(state)

    def test_unverified_hold_signal_blocks_new_mutation_only_while_verifying(self):
        event = WorkControlEvent.from_dict(self.event())
        state = derive_project_work_state(
            self.registry,
            [event],
            project_id="warp-propulsion-lab",
            now=datetime.fromisoformat("2026-10-05T07:30:00-07:00"),
            validated_event_ids=[],
        )
        self.assertEqual(state.state, "ACTIVE")
        self.assertTrue(state.project_work_allowed)
        self.assertTrue(state.mutation_blocked_pending_verification)
        self.assertEqual(state.unverified_hold_event_ids, ("evt-hold-1",))
        with self.assertRaisesRegex(ProjectWorkControlError, "UNVERIFIED_HOLD_SIGNAL"):
            require_new_mutation_allowed_by_hold_state(state)

    def test_manual_expiry_stays_blocked_until_human_resume(self):
        event = WorkControlEvent.from_dict(
            self.event(expires_at="2026-10-05T08:00:00-07:00", resume_policy="MANUAL")
        )
        state = derive_project_work_state(
            self.registry,
            [event],
            project_id="warp-propulsion-lab",
            now=datetime.fromisoformat("2026-10-05T08:01:00-07:00"),
            validated_event_ids=[event.event_id],
        )
        self.assertEqual(state.state, "HOLD_EXPIRED_PENDING_HUMAN_RESUME")
        self.assertFalse(state.project_work_allowed)

    def test_explicit_auto_at_expiry_releases_logical_hold(self):
        event = WorkControlEvent.from_dict(
            self.event(expires_at="2026-10-05T08:00:00-07:00", resume_policy="AUTO_AT_EXPIRY")
        )
        state = derive_project_work_state(
            self.registry,
            [event],
            project_id="warp-propulsion-lab",
            now=datetime.fromisoformat("2026-10-05T08:01:00-07:00"),
            validated_event_ids=[event.event_id],
        )
        self.assertEqual(state.state, "ACTIVE")
        self.assertTrue(state.project_work_allowed)

    def test_matching_resume_event_restores_active_state(self):
        hold = WorkControlEvent.from_dict(self.event())
        resume = WorkControlEvent.from_dict(
            self.event(
                event_id="evt-resume-1",
                action="RESUME",
                issued_at="2026-10-06T07:00:00-07:00",
                effective_at="2026-10-06T07:00:00-07:00",
                expires_at=None,
                human_reason="Resume the held project.",
                authorization_case_id="AUTH-resume-1",
            )
        )
        state = derive_project_work_state(
            self.registry,
            [hold, resume],
            project_id="warp-propulsion-lab",
            now=datetime.fromisoformat("2026-10-06T07:01:00-07:00"),
            validated_event_ids=[hold.event_id, resume.event_id],
        )
        self.assertEqual(state.state, "ACTIVE")
        self.assertEqual(state.source_event_id, "evt-resume-1")

    def test_extend_must_match_active_hold_order(self):
        hold = WorkControlEvent.from_dict(self.event())
        extend = WorkControlEvent.from_dict(
            self.event(
                event_id="evt-extend-1",
                action="EXTEND_HOLD",
                hold_order_id="different-hold",
                issued_at="2026-10-06T07:00:00-07:00",
                effective_at="2026-10-06T07:00:00-07:00",
                expires_at="2027-02-05T07:00:00-08:00",
                authorization_case_id="AUTH-extend-1",
            )
        )
        with self.assertRaisesRegex(ProjectWorkControlError, "extend_hold_does_not_match_active_hold"):
            derive_project_work_state(
                self.registry,
                [hold, extend],
                project_id="warp-propulsion-lab",
                now=datetime.fromisoformat("2026-10-06T07:01:00-07:00"),
                validated_event_ids=[hold.event_id, extend.event_id],
            )

    def test_registry_projection_can_represent_a_persisted_manual_hold(self):
        registry = deepcopy(self.registry)
        registry["projects"]["warp-propulsion-lab"] = {
            "state": "HOLD",
            "active_hold": {
                "hold_order_id": "persisted-hold",
                "source_event_id": "evt-persisted",
                "effective_at": "2026-10-05T07:00:00-07:00",
                "expires_at": "2026-10-05T08:00:00-07:00",
                "resume_policy": "MANUAL",
                "reason_code": "HUMAN_PRIORITY",
                "human_reason": "Persisted hold projection.",
                "metadata": {},
            },
        }
        state = derive_project_work_state(
            registry,
            [],
            project_id="warp-propulsion-lab",
            now=datetime.fromisoformat("2026-10-05T08:01:00-07:00"),
        )
        self.assertEqual(state.state, "HOLD_EXPIRED_PENDING_HUMAN_RESUME")


if __name__ == "__main__":
    unittest.main()
