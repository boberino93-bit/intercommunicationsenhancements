from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.project_scope import ProjectScopeError
from org_agent_mesh.scheduled_tasks import ScheduledTaskRoute, ScheduledTaskRouteError


CONTRACT = {
    "schema": "org-agent-mesh/local-agent-bootstrap/v1",
    "routing_contract_version": "1.3.0",
    "mode": "FAIL_CLOSED",
    "project_id": "intercommunicationsenhancements",
    "repository": {
        "full_name": "boberino93-bit/intercommunicationsenhancements",
        "id": 1403662737,
    },
    "forum": {
        "authority": "INTERNAL_ARTIFACTORY",
        "namespace": "intercommunicationsenhancements::messages",
    },
    "artifact_namespace": "intercommunicationsenhancements::artifacts",
    "authorized_roles": ["primary", "manager", "research"],
}


def dynamic_route(**kwargs):
    values = dict(
        project_id="intercommunicationsenhancements",
        task_id="nightly-digest",
        role_id="primary",
        routing_contract_version="1.3.0",
        forum_namespace="intercommunicationsenhancements::messages",
        artifact_namespace="intercommunicationsenhancements::artifacts",
        repository_identity="boberino93-bit/intercommunicationsenhancements",
        repository_id=1403662737,
    )
    values.update(kwargs)
    return ScheduledTaskRoute(**values)


class ScheduledTaskRouteTest(unittest.TestCase):
    def test_dynamic_slack_route_requires_explicit_destination(self):
        route = dynamic_route(
            delivery_transport="SLACK",
            slack_destination_id="C123ABC",
            delivery_events=("COMPLETE", "FAILURE"),
        )
        self.assertTrue(route.event_enabled("COMPLETE"))

    def test_dynamic_route_requires_project_context(self):
        with self.assertRaises(ScheduledTaskRouteError):
            ScheduledTaskRoute(
                project_id="intercommunicationsenhancements",
                task_id="nightly-digest",
            )

    def test_slack_route_without_destination_fails_closed(self):
        with self.assertRaises(ScheduledTaskRouteError):
            dynamic_route(delivery_transport="SLACK")

    def test_static_slack_requires_static_context_binding(self):
        with self.assertRaises(ScheduledTaskRouteError):
            ScheduledTaskRoute(
                project_id="intercommunicationsenhancements",
                task_id="static-reminder",
                execution_scheduler="NONE_STATIC_SLACK",
                delivery_transport="SLACK",
                slack_destination_id="C123ABC",
            )

    def test_static_slack_route_does_not_launch_agent(self):
        route = ScheduledTaskRoute(
            project_id="intercommunicationsenhancements",
            task_id="static-reminder",
            execution_scheduler="NONE_STATIC_SLACK",
            context_binding="STATIC_MESSAGE_ONLY",
            delivery_transport="SLACK",
            slack_destination_id="C123ABC",
        )
        with self.assertRaises(ScheduledTaskRouteError):
            route.build_launch_context()

    def test_foreign_project_route_rejected(self):
        route = dynamic_route()
        with self.assertRaises(ProjectScopeError):
            route.assert_project("project-b")

    def test_completion_requires_canonical_state_first(self):
        with self.assertRaises(ScheduledTaskRouteError):
            dynamic_route(canonical_state_required_before_completion_post=False)

    def test_route_can_be_captured_from_project_contract(self):
        route = ScheduledTaskRoute.from_project_contract(
            CONTRACT,
            task_id="nightly-digest",
            role_id="primary",
        )
        self.assertEqual(route.project_id, CONTRACT["project_id"])
        self.assertEqual(route.repository_identity, CONTRACT["repository"]["full_name"])
        self.assertTrue(route.build_launch_context().assert_matches_project_contract(CONTRACT))

    def test_launch_context_conflict_fails_closed(self):
        route = ScheduledTaskRoute.from_project_contract(CONTRACT, task_id="nightly-digest")
        context = route.build_launch_context(occurrence_id="run-001")
        foreign = json.loads(json.dumps(CONTRACT))
        foreign["project_id"] = "different-project"
        with self.assertRaises(ProjectScopeError):
            context.assert_matches_project_contract(foreign)

    def test_scheduler_prompt_embeds_machine_readable_project_context(self):
        route = ScheduledTaskRoute.from_project_contract(CONTRACT, task_id="nightly-digest")
        prompt = route.render_scheduler_prompt(
            "Review the current queue and continue approved work.",
            occurrence_id="run-001",
        )
        self.assertIn("ORG_AGENT_MESH_PROJECT_LAUNCH_CONTEXT", prompt)
        self.assertIn('"project_id":"intercommunicationsenhancements"', prompt)
        self.assertIn('"occurrence_id":"run-001"', prompt)
        self.assertIn("LAUNCH_CONTEXT_MISMATCH", prompt)

    def test_stagger_offset_is_stable_and_bounded(self):
        route = ScheduledTaskRoute.from_project_contract(CONTRACT, task_id="nightly-digest")
        first = route.recommended_initial_offset_seconds(window_seconds=300)
        second = route.recommended_initial_offset_seconds(window_seconds=300)
        self.assertEqual(first, second)
        self.assertGreaterEqual(first, 0)
        self.assertLess(first, 300)


if __name__ == "__main__":
    unittest.main()
