import unittest
from datetime import datetime, timezone

from org_agent_mesh.operations_view import (
    OperationsViewError,
    build_live_operations_snapshot,
    render_operations_markdown,
)


NOW = datetime(2026, 10, 5, 12, 20, tzinfo=timezone.utc)


class OperationsViewTests(unittest.TestCase):
    def project(self, project_id, *, state=None, observed="2026-10-05T12:10:00Z",
                repo="abc", coordinated="abc", coord_time="2026-10-05T12:11:00Z",
                normalized=True, blockers=None):
        roles = []
        if state:
            roles.append({
                "agent_id": f"{project_id}-manager-1",
                "role": "MANAGER",
                "state": state,
                "observed_at_utc": observed,
            })
        return {
            "project_id": project_id,
            "repository_identity": f"boberino93-bit/{project_id}",
            "registered": True,
            "normalized": normalized,
            "repository_revision": repo,
            "repository_observed_at_utc": "2026-10-05T12:15:00Z",
            "coordination_repository_revision": coordinated,
            "coordination_observed_at_utc": coord_time,
            "coordination_checkpoint_ref": f"/{project_id}/messages/checkpoint.json",
            "roles": roles,
            "blockers": blockers or [],
        }

    def test_classifies_execution_waiting_idle_and_drift(self):
        projects = [
            self.project("alpha", state="RUNNING"),
            self.project("beta", state="WAITING_PRIMARY"),
            self.project("gamma"),
            self.project(
                "delta",
                repo="new",
                coordinated="old",
                coord_time="2026-10-05T11:50:00Z",
            ),
        ]
        snapshot = build_live_operations_snapshot(
            projects, now=NOW, stale_after_seconds=1800, drift_grace_seconds=900
        )
        self.assertEqual(snapshot["summary"]["registered_projects"], 4)
        self.assertEqual(snapshot["summary"]["executing_projects"], 1)
        self.assertEqual(snapshot["summary"]["waiting_projects"], 1)
        self.assertEqual(snapshot["summary"]["idle_ready_projects"], 2)
        self.assertEqual(snapshot["summary"]["active_agents"], 2)
        self.assertEqual(snapshot["summary"]["executing_agents"], 1)
        self.assertEqual(snapshot["summary"]["waiting_for_primary"], 1)
        self.assertEqual(snapshot["summary"]["source_ahead_projects"], 1)
        delta = next(p for p in snapshot["projects"] if p["project_id"] == "delta")
        self.assertEqual(
            delta["source_coordination"]["state"], "SOURCE_AHEAD_OF_COORDINATION"
        )

    def test_unattributed_activity_is_visible_without_inventing_agents(self):
        project = self.project("alpha")
        project["unattributed_activity"] = True
        snapshot = build_live_operations_snapshot([project], now=NOW)
        self.assertEqual(snapshot["projects"][0]["status"], "ACTIVITY_UNATTRIBUTED")
        self.assertEqual(snapshot["summary"]["active_agents"], 0)
        self.assertEqual(snapshot["summary"]["unattributed_activity_projects"], 1)

    def test_stale_active_role_takes_precedence(self):
        project = self.project(
            "alpha",
            state="RUNNING",
            observed="2026-10-05T11:00:00Z",
        )
        snapshot = build_live_operations_snapshot(
            [project], now=NOW, stale_after_seconds=1200
        )
        self.assertEqual(snapshot["projects"][0]["status"], "STALE")
        self.assertEqual(snapshot["summary"]["active_agents"], 0)
        self.assertEqual(snapshot["summary"]["stale_projects"], 1)

    def test_pending_reconciliation_grace(self):
        project = self.project(
            "alpha",
            repo="new",
            coordinated="old",
            coord_time="2026-10-05T12:14:00Z",
        )
        snapshot = build_live_operations_snapshot(
            [project], now=NOW, drift_grace_seconds=600
        )
        self.assertEqual(
            snapshot["projects"][0]["source_coordination"]["state"],
            "PENDING_RECONCILIATION",
        )

    def test_does_not_treat_source_as_authority(self):
        snapshot = build_live_operations_snapshot([self.project("alpha")], now=NOW)
        self.assertEqual(
            snapshot["semantics"]["coordination_truth"],
            "PROJECT_LOCAL_AGENTBUS_AND_DURABLE_STATE",
        )
        self.assertEqual(
            snapshot["semantics"]["github_role"],
            "SOURCE_VERSION_CONTROL_NOT_COORDINATION_AUTHORITY",
        )

    def test_duplicate_agent_ids_fail(self):
        project = self.project("alpha", state="RUNNING")
        project["roles"].append(dict(project["roles"][0]))
        with self.assertRaises(OperationsViewError):
            build_live_operations_snapshot([project], now=NOW)

    def test_markdown_render(self):
        snapshot = build_live_operations_snapshot(
            [self.project("alpha", state="RUNNING")], now=NOW
        )
        rendered = render_operations_markdown(snapshot)
        self.assertIn("Live swarm operations", rendered)
        self.assertIn("`alpha`", rendered)
        self.assertIn("MANAGER:RUNNING", rendered)


if __name__ == "__main__":
    unittest.main()
