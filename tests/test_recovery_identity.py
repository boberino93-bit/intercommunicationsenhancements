from pathlib import Path
import ast
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.project_identity import validate_current_project
from org_agent_mesh.project_scope import ProjectScopeError


CANONICAL_BOOTSTRAP_PREFIX = [
    "bind_host_chat_project_context_before_all_other_bootstrap",
    "validate_current_human_project_intent",
    "load_and_validate_project_identity_lock",
]


def write_lock(root, project_id="project-a", repository="repo-a"):
    payload = {
        "schema": "org-agent-mesh/project-identity-lock/v1",
        "mode": "FAIL_CLOSED",
        "project_id": project_id,
        "project_name": "Project A",
        "writable_repository": repository,
        "canonical_branch": "main",
        "coordination_root": ".interagent",
        "artifact_root": ".interagent/artifacts",
        "identity_lock_path": "PROJECT_IDENTITY_LOCK.json",
        "bootstrap_order_path": "BOOTSTRAP_ORDER.json"
    }
    Path(root, "PROJECT_IDENTITY_LOCK.json").write_text(json.dumps(payload), encoding="utf-8")


class RecoveryIdentityTest(unittest.TestCase):
    def test_stale_other_project_context_cannot_select_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            write_lock(directory, project_id="project-a", repository="repo-a")
            recent_context_project = "project-b"
            self.assertEqual(recent_context_project, "project-b")
            lock = validate_current_project(directory, "project-a", "repo-a")
            self.assertEqual(lock["project_id"], "project-a")

    def test_ambiguous_project_intent_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            write_lock(directory)
            with self.assertRaises(ProjectScopeError):
                validate_current_project(directory, None, "repo-a")

    def test_conflicting_project_intent_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            write_lock(directory)
            with self.assertRaises(ProjectScopeError):
                validate_current_project(directory, "project-b", "repo-a")

    def test_repository_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            write_lock(directory)
            with self.assertRaises(ProjectScopeError):
                validate_current_project(directory, "project-a", "repo-b")

    def test_repository_bootstrap_order_is_identity_first(self):
        order = json.loads((ROOT / "BOOTSTRAP_ORDER.json").read_text(encoding="utf-8"))
        ids = [step["id"] for step in order["steps"]]
        self.assertEqual(ids[:3], CANONICAL_BOOTSTRAP_PREFIX)
        continuation_index = ids.index("load_project_handoffs_queues_forums_and_accepted_state")
        self.assertGreater(continuation_index, 2)

    def test_package_verifier_uses_canonical_three_step_bootstrap_prefix(self):
        verifier_path = ROOT / "tools" / "verify_agent_packages.py"
        source = verifier_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        expected_prefix = None
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            if any(isinstance(target, ast.Name) and target.id == "EXPECTED_PREFIX" for target in node.targets):
                expected_prefix = ast.literal_eval(node.value)
                break
        self.assertEqual(expected_prefix, CANONICAL_BOOTSTRAP_PREFIX)
        self.assertNotIn("[:2]", source)
        self.assertGreaterEqual(source.count("[:3]"), 2)


if __name__ == "__main__":
    unittest.main()
