from datetime import datetime, timezone
import unittest

from org_agent_mesh.constants import PROTOCOL_VERSION
from org_agent_mesh.control_plane import AgentSession, require_active_session
from org_agent_mesh.message_bus import validate_message
from org_agent_mesh.project_scope import ProjectBinding, ProjectScopeError


def active_session(capabilities):
    binding = ProjectBinding(
        project_id="duo-open",
        repository_identity="boberino93-bit/duo-open",
        project_root=".",
        agent_id="agent-1",
        agent_instance_id="duo-open--agent-1-test",
        protocol_version=PROTOCOL_VERSION,
        capabilities=tuple(capabilities),
    )
    return AgentSession("agent-1").bind(binding).initialize().activate()


def message(role):
    return {
        "schema": "org-agent-mesh/message/v1",
        "protocol_version": PROTOCOL_VERSION,
        "id": "msg-1",
        "project_id": "duo-open",
        "destination_project_id": "duo-open",
        "timestamp_utc": "2026-10-05T16:00:00Z",
        "from_agent": "agent-1",
        "from_agent_instance_id": "duo-open--agent-1-test",
        "from_role": role,
        "to": ["manager"],
        "kind": "FINDING",
        "priority": "normal",
        "subject": "test",
        "summary": "test",
        "applies_to_state": None,
        "evidence": [],
        "artifacts": [],
        "reply_to": None,
        "supersedes": [],
        "requires_ack": False,
        "tags": [],
        "correlation_id": None,
        "causation_id": None,
        "idempotency_key": "msg-1",
        "expires_at_utc": None,
        "authority_conveyed": False,
    }


class SubordinateMutationBoundaryTests(unittest.TestCase):
    def test_legacy_subordinate_write_artifacts_grant_is_not_effective(self):
        session = active_session(["READ_SOURCE", "READ_ARTIFACTS", "WRITE_ARTIFACTS", "PUBLISH_MESSAGE"])
        with self.assertRaises(ProjectScopeError):
            require_active_session(
                session,
                "duo-open",
                operation="artifact write",
                capability="WRITE_ARTIFACTS",
            )

    def test_legacy_subordinate_claim_task_grant_is_not_effective(self):
        session = active_session(["READ_SOURCE", "CLAIM_TASK", "PUBLISH_MESSAGE"])
        with self.assertRaises(ProjectScopeError):
            require_active_session(
                session,
                "duo-open",
                operation="task claim",
                capability="CLAIM_TASK",
            )

    def test_subordinate_cannot_claim_primary_role_in_message(self):
        session = active_session(["READ_SOURCE", "PUBLISH_MESSAGE"])
        with self.assertRaises(ProjectScopeError):
            validate_message(
                message("PRIMARY"),
                expected_project_id="duo-open",
                sender_session=session,
                now=datetime(2026, 10, 5, 16, 0, tzinfo=timezone.utc),
            )

    def test_primary_class_binding_can_publish_as_primary(self):
        session = active_session([
            "READ_SOURCE",
            "WRITE_SOURCE",
            "READ_ARTIFACTS",
            "WRITE_ARTIFACTS",
            "WRITE_ACCEPTED_STATE",
            "PUBLISH_MESSAGE",
            "APPROVE_CHANGE",
        ])
        self.assertTrue(validate_message(
            message("PRIMARY"),
            expected_project_id="duo-open",
            sender_session=session,
            now=datetime(2026, 10, 5, 16, 0, tzinfo=timezone.utc),
        ))


if __name__ == "__main__":
    unittest.main()
