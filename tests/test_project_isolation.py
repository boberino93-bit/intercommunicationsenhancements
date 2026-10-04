from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.constants import PROTOCOL_VERSION
from org_agent_mesh.control_plane import AgentSession
from org_agent_mesh.message_bus import append_message, validate_message
from org_agent_mesh.project_scope import ProjectBinding, ProjectScopeError, qualify, require_project_id, require_project_path, require_resource_id

BASE = {
    "schema": "org-agent-mesh/message/v2", "protocol_version": PROTOCOL_VERSION, "id": "m1",
    "project_id": "project-a", "destination_project_id": "project-a", "timestamp_utc": "2099-01-01T00:00:00Z",
    "from_agent": "worker", "from_agent_instance_id": "worker-1", "from_role": "SPECIALIST", "to": ["manager"],
    "kind": "FINDING", "priority": "normal", "subject": "s", "summary": "x", "applies_to_state": "v",
    "evidence": [], "artifacts": [], "reply_to": None, "supersedes": [], "requires_ack": False, "tags": [],
    "correlation_id": "c1", "causation_id": None, "idempotency_key": "idem-1", "expires_at_utc": None,
}


def sender_session():
    binding = ProjectBinding("project-a", "repo/project-a", "/work/project-a", "worker", "worker-1", PROTOCOL_VERSION, ("PUBLISH_MESSAGE",))
    return AgentSession("worker").bind(binding).initialize().activate()


class IsolationTest(unittest.TestCase):
    def test_internal_cross_project_message_is_rejected(self):
        with self.assertRaises(ProjectScopeError):
            validate_message(dict(BASE, destination_project_id="project-b"))

    def test_missing_project_identity_rejected(self):
        message = dict(BASE); del message["project_id"]
        with self.assertRaises(ValueError):
            validate_message(message)

    def test_binding_rejects_foreign_target(self):
        binding = ProjectBinding("project-a", "repo/project-a", "/tmp/a", "primary", "p-1", PROTOCOL_VERSION)
        with self.assertRaises(ProjectScopeError):
            binding.assert_target("project-b", "repository write")

    def test_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ProjectScopeError):
                require_project_path(directory, Path(directory).parent / "outside")

    def test_relative_project_path_resolves_under_root(self):
        with tempfile.TemporaryDirectory() as directory:
            expected = Path(directory).resolve() / "inside" / "file.txt"
            self.assertEqual(expected, require_project_path(directory, "inside/file.txt"))

    def test_idempotency_is_project_scoped_and_atomic_keyed(self):
        with tempfile.TemporaryDirectory() as directory:
            session = sender_session(); append_message(directory, BASE, sender_session=session)
            with self.assertRaises(FileExistsError):
                append_message(directory, dict(BASE, id="m2", timestamp_utc="2099-01-01T00:00:01Z"), sender_session=session)
            self.assertEqual(1, len(list(Path(directory).glob("*.json"))))

    def test_spoofed_sender_instance_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ProjectScopeError):
                append_message(directory, dict(BASE, from_agent_instance_id="forged-instance"), sender_session=sender_session())

    def test_lossy_identifier_inputs_are_rejected_not_sanitized(self):
        with self.assertRaises(ProjectScopeError):
            require_project_id("project/a")
        with self.assertRaises(ValueError):
            require_resource_id("task/001")
        self.assertNotEqual(qualify("project-a", "task-001"), qualify("project-b", "task-001"))


if __name__ == "__main__":
    unittest.main()
