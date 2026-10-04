from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.scheduled_launch_context import (
    ScheduledLaunchContextParseError,
    parse_project_launch_context,
)
from org_agent_mesh.scheduled_tasks import ScheduledTaskRoute


CONTRACT = {
    "schema": "org-agent-mesh/local-agent-bootstrap/v1",
    "routing_contract_version": "1.4.0",
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


class ScheduledLaunchContextParserTests(unittest.TestCase):
    def _prompt(self):
        route = ScheduledTaskRoute.from_project_contract(
            CONTRACT,
            task_id="scheduled-regression-review",
            role_id="primary",
        )
        return route.render_scheduler_prompt(
            "Continue the project regression review.",
            occurrence_id="run-001",
        )

    def test_rendered_context_round_trips_and_matches_local_contract(self):
        context = parse_project_launch_context(self._prompt())
        self.assertEqual(context.project_id, "intercommunicationsenhancements")
        self.assertEqual(context.occurrence_id, "run-001")
        self.assertTrue(context.assert_matches_project_contract(CONTRACT))

    def test_duplicate_context_blocks_fail_closed(self):
        prompt = self._prompt()
        duplicate = prompt + "\n" + prompt
        with self.assertRaises(ScheduledLaunchContextParseError):
            parse_project_launch_context(duplicate)

    def test_tampered_payload_fails_fingerprint_check(self):
        prompt = self._prompt()
        tampered = prompt.replace(
            '"task_id":"scheduled-regression-review"',
            '"task_id":"scheduled-regression-review-tampered"',
            1,
        )
        with self.assertRaises(ScheduledLaunchContextParseError):
            parse_project_launch_context(tampered)

    def test_unknown_fields_fail_closed(self):
        prompt = self._prompt()
        begin = "ORG_AGENT_MESH_PROJECT_LAUNCH_CONTEXT\n"
        end = "\nEND_ORG_AGENT_MESH_PROJECT_LAUNCH_CONTEXT"
        raw = prompt.split(begin, 1)[1].split(end, 1)[0]
        payload = json.loads(raw)
        payload["unexpected_authority"] = "ALLOW"
        modified = prompt.replace(raw, json.dumps(payload, sort_keys=True, separators=(",", ":")), 1)
        with self.assertRaises(ScheduledLaunchContextParseError):
            parse_project_launch_context(modified)

    def test_missing_context_block_fails_closed(self):
        with self.assertRaises(ScheduledLaunchContextParseError):
            parse_project_launch_context("Continue the project regression review.")


if __name__ == "__main__":
    unittest.main()
