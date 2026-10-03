from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.message_bus import append_message, validate_message
from org_agent_mesh.project_scope import ProjectBinding, ProjectScopeError, require_project_path

BASE = {
    "schema": "org-agent-mesh/message/v2",
    "protocol_version": "2.1.0-alpha.1",
    "id": "m1",
    "project_id": "project-a",
    "destination_project_id": "project-a",
    "timestamp_utc": "2099-01-01T00:00:00Z",
    "from_agent": "worker",
    "from_agent_instance_id": "worker-1",
    "from_role": "SPECIALIST",
    "to": ["manager"],
    "kind": "FINDING",
    "priority": "normal",
    "subject": "s",
    "summary": "x",
    "applies_to_state": "v",
    "evidence": [],
    "artifacts": [],
    "reply_to": None,
    "supersedes": [],
    "requires_ack": False,
    "tags": [],
    "correlation_id": "c1",
    "causation_id": None,
    "idempotency_key": "idem-1",
    "expires_at_utc": None
}


class IsolationTest(unittest.TestCase):
    def test_internal_cross_project_message_is_rejected(self):
        with self.assertRaises(ProjectScopeError):
            validate_message(dict(BASE, destination_project_id="project-b"))

    def test_missing_project_identity_rejected(self):
        message = dict(BASE)
        del message["project_id"]
        with self.assertRaises(ValueError):
            validate_message(message)

    def test_binding_rejects_foreign_target(self):
        binding = ProjectBinding("project-a", "repo-a", "/tmp/a", "primary", "p-1", "2.1.0-alpha.1")
        with self.assertRaises(ProjectScopeError):
            binding.assert_target("project-b", "repository write")

    def test_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ProjectScopeError):
                require_project_path(directory, Path(directory).parent / "outside")

    def test_idempotency_is_project_scoped(self):
        with tempfile.TemporaryDirectory() as directory:
            append_message(directory, BASE)
            with self.assertRaises(FileExistsError):
                append_message(directory, dict(BASE, id="m2", timestamp_utc="2099-01-01T00:00:01Z"))


if __name__ == "__main__":
    unittest.main()
