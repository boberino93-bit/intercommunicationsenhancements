from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.project_scope import ProjectScopeError
from org_agent_mesh.scheduled_tasks import ScheduledTaskRoute, ScheduledTaskRouteError


class ScheduledTaskRouteTest(unittest.TestCase):
    def test_dynamic_slack_route_requires_explicit_destination(self):
        route = ScheduledTaskRoute(
            project_id="intercommunicationsenhancements",
            task_id="nightly-digest",
            execution_scheduler="AUTOMATION",
            delivery_transport="SLACK",
            slack_destination_id="C123ABC",
            delivery_events=("COMPLETE", "FAILURE"),
        )
        self.assertTrue(route.event_enabled("COMPLETE"))

    def test_slack_route_without_destination_fails_closed(self):
        with self.assertRaises(ScheduledTaskRouteError):
            ScheduledTaskRoute(
                project_id="intercommunicationsenhancements",
                task_id="nightly-digest",
                delivery_transport="SLACK",
            )

    def test_static_slack_requires_slack_transport(self):
        with self.assertRaises(ScheduledTaskRouteError):
            ScheduledTaskRoute(
                project_id="intercommunicationsenhancements",
                task_id="static-reminder",
                execution_scheduler="NONE_STATIC_SLACK",
                delivery_transport="NONE",
            )

    def test_foreign_project_route_rejected(self):
        route = ScheduledTaskRoute(
            project_id="project-a",
            task_id="digest",
        )
        with self.assertRaises(ProjectScopeError):
            route.assert_project("project-b")

    def test_completion_requires_canonical_state_first(self):
        with self.assertRaises(ScheduledTaskRouteError):
            ScheduledTaskRoute(
                project_id="intercommunicationsenhancements",
                task_id="digest",
                canonical_state_required_before_completion_post=False,
            )


if __name__ == "__main__":
    unittest.main()
