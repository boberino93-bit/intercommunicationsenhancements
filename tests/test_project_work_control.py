from datetime import datetime, timezone
from pathlib import Path
import json
import unittest

from org_agent_mesh.project_work_control import (
    ProjectWorkControlError,
    ProjectWorkState,
    filter_unheld_projects,
    resolve_project_work_state,
)

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 10, 5, 14, 0, tzinfo=timezone.utc)


def event(
    event_id: str,
    action: str,
    *,
    project_id: str = "warp-propulsion-lab",
    hold_order_id: str = "HOLD-1",
    issued_at: str = "2026-10-05T13:00:00Z",
    effective_at: str = "2026-10-05T13:00:00Z",
    expires_at: str | None = None,
    resume_policy: str = "MANUAL",
):
    return {
        "schema": "org-agent-mesh/project-work-control-event/v1",
        "event_id": event_id,
        "project_id": project_id,
        "action": action,
        "hold_order_id": hold_order_id,
        "issued_at": issued_at,
        "effective_at": effective_at,
        "expires_at": expires_at,
        "resume_policy": resume_policy,
        "reason_code": "HUMAN_PRIORITY",
        "human_reason": "bounded test hold",
        "metadata": {"source": "test"},
        "claimed_principal": "registered-human-principal",
        "authentication_ref": "external-proof:test",
        "authorization_case_id": "AUTH-test",
        "preserve_partial_state": True,
    }


class ProjectWorkControlTests(unittest.TestCase):
    def test_registry_starts_active_and_is_hold_aware(self):
        control = json.loads((ROOT / "governance" / "PROJECT_WORK_CONTROL.json").read_text())
        self.assertEqual(control["status"], "ACTIVE_CONTROL_PLANE")
        self.assertFalse(control["rules"]["hold_is_cancellation"])
        self.assertFalse(control["rules"]["hold_is_failure"])
        self.assertTrue(control["rules"]["active_agents_checkpoint_then_stop_project_work"])
        self.assertTrue(control["rules"]["scheduled_tasks_must_check_before_project_selection"])
        self.assertTrue(control["rules"]["global_agents_may_continue_other_unheld_projects"])
        self.assertEqual(control["rules"]["expired_manual_hold_state"], "HOLD_EXPIRED_PENDING_HUMAN_RESUME")
        for project in control["projects"].values():
            self.assertEqual(project["state"], "ACTIVE")
            self.assertIsNone(project["active_hold"])

    def test_event_schema_supports_hold_extend_resume(self):
        schema = json.loads((ROOT / "schemas" / "project_work_control_event.schema.json").read_text())
        actions = set(schema["properties"]["action"]["enum"])
        self.assertEqual(actions, {"HOLD", "EXTEND_HOLD", "RESUME"})
        self.assertIn("authentication_ref", schema["required"])
        self.assertIn("authorization_case_id", schema["required"])
        self.assertEqual(schema["properties"]["preserve_partial_state"]["const"], True)

    def test_live_and_future_bootstraps_load_work_control(self):
        live = json.loads((ROOT / "AGENT_BOOTSTRAP.json").read_text())
        template = json.loads((ROOT / "templates" / "new-project" / "AGENT_BOOTSTRAP.template.json").read_text())
        for bootstrap in (live, template):
            work = bootstrap["project_work_control"]
            self.assertTrue(work["required_on_startup"])
            self.assertTrue(work["required_between_bounded_units"])
            self.assertFalse(work["hold_is_cancellation"])
            self.assertTrue(work["hold_blocks_bound_project_work"])
            self.assertTrue(bootstrap["rules"]["resume_interrupted_assignment_automatically"])
            self.assertTrue(bootstrap["rules"]["pending_human_response_blocks_only_dependent_branch"])

    def test_protocol_requires_checkpoint_then_stop(self):
        text = (ROOT / "protocols" / "project_work_holds.md").read_text()
        self.assertIn("HOLD is **not** cancellation", text)
        self.assertIn("checkpoint", text.lower())
        self.assertIn("PROJECT_HOLD_ACTIVE", text)
        self.assertIn("AUTO_AT_EXPIRY", text)

    def test_authorization_package_never_replaces_single_use_gate(self):
        core = json.loads((ROOT / "governance" / "MUTATION_AUTHORIZATION_POLICY.json").read_text())
        package = json.loads((ROOT / "governance" / "AUTHORIZATION_PACKAGE_POLICY.json").read_text())
        self.assertEqual(core["valid_authorization_sources"], ["CURRENT_HUMAN_SINGLE_USE_AUTHORIZATION_CASE"])
        self.assertTrue(core["authorization_case"]["single_use"])
        self.assertTrue(package["package_requirements"]["child_single_use"])
        self.assertEqual(package["forbidden"][0], "OPEN_ENDED_FUTURE_WRITES")
        self.assertIn("ADDING_NEW_CHILDREN_AFTER_HUMAN_APPROVAL", package["forbidden"])

    def test_hold_blocks_new_work_respawn_and_mutation(self):
        decision = resolve_project_work_state("warp-propulsion-lab", [event("e1", "HOLD")], now=NOW)
        self.assertEqual(decision.state, ProjectWorkState.HOLD)
        self.assertFalse(decision.allow_new_work)
        self.assertFalse(decision.allow_respawn)
        self.assertFalse(decision.allow_mutation)
        self.assertEqual(decision.reason, "PROJECT_HOLD_ACTIVE")

    def test_matching_resume_reactivates_hold(self):
        events = [
            event("e1", "HOLD"),
            event("e2", "RESUME", issued_at="2026-10-05T13:30:00Z"),
        ]
        self.assertEqual(
            resolve_project_work_state("warp-propulsion-lab", events, now=NOW).state,
            ProjectWorkState.ACTIVE,
        )

    def test_unrelated_resume_cannot_clear_hold(self):
        events = [
            event("e1", "HOLD"),
            event("e2", "RESUME", hold_order_id="OTHER", issued_at="2026-10-05T13:30:00Z"),
        ]
        self.assertEqual(
            resolve_project_work_state("warp-propulsion-lab", events, now=NOW).state,
            ProjectWorkState.HOLD,
        )

    def test_manual_expiry_requires_authenticated_resume(self):
        decision = resolve_project_work_state(
            "warp-propulsion-lab",
            [event("e1", "HOLD", expires_at="2026-10-05T13:30:00Z", resume_policy="MANUAL")],
            now=NOW,
        )
        self.assertEqual(decision.state, ProjectWorkState.HOLD_EXPIRED_PENDING_HUMAN_RESUME)
        self.assertFalse(decision.allow_new_work)

    def test_auto_expiry_reactivates_only_when_explicitly_selected(self):
        decision = resolve_project_work_state(
            "warp-propulsion-lab",
            [event("e1", "HOLD", expires_at="2026-10-05T13:30:00Z", resume_policy="AUTO_AT_EXPIRY")],
            now=NOW,
        )
        self.assertEqual(decision.state, ProjectWorkState.ACTIVE)
        self.assertEqual(decision.reason, "AUTO_RESUMED_AT_HOLD_EXPIRY")

    def test_extend_updates_expiry(self):
        events = [
            event("e1", "HOLD", expires_at="2026-10-05T13:30:00Z"),
            event("e2", "EXTEND_HOLD", issued_at="2026-10-05T13:20:00Z", expires_at="2026-10-05T15:00:00Z"),
        ]
        decision = resolve_project_work_state("warp-propulsion-lab", events, now=NOW)
        self.assertEqual(decision.state, ProjectWorkState.HOLD)
        self.assertEqual(decision.active_hold.expires_at.hour, 15)

    def test_future_hold_does_not_apply_early(self):
        decision = resolve_project_work_state(
            "warp-propulsion-lab",
            [event("e1", "HOLD", effective_at="2026-10-05T15:00:00Z")],
            now=NOW,
        )
        self.assertEqual(decision.state, ProjectWorkState.ACTIVE)

    def test_filter_unheld_projects_reallocates_portfolio_capacity(self):
        events = [event("e1", "HOLD", project_id="warp-propulsion-lab")]
        self.assertEqual(
            filter_unheld_projects(["duo-open", "warp-propulsion-lab", "xrp-thesis"], events, now=NOW),
            ["duo-open", "xrp-thesis"],
        )

    def test_invalid_hold_event_is_rejected(self):
        bad = event("e1", "HOLD")
        bad["preserve_partial_state"] = False
        with self.assertRaises(ProjectWorkControlError):
            resolve_project_work_state("warp-propulsion-lab", [bad], now=NOW)


if __name__ == "__main__":
    unittest.main()
