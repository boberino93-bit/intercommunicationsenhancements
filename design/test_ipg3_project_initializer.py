import copy
import unittest

from ipg3_project_initializer import (
    ProjectInitializationError,
    ProjectInitializer,
    ProjectIntent,
    derive_project_id,
)


class FakeBoard:
    def __init__(self):
        self.directories = set()
        self.objects = {}
        self.events = {}

    def directory_exists(self, path):
        return path in self.directories

    def create_directory(self, path):
        self.directories.add(path)

    def object_exists(self, path):
        return path in self.objects

    def write_json(self, path, value, *, create_only=False):
        if create_only and path in self.objects:
            raise ProjectInitializationError(f"object already exists: {path}")
        self.objects[path] = copy.deepcopy(value)

    def read_json(self, path):
        return copy.deepcopy(self.objects[path])

    def append_event(self, path, value):
        self.events.setdefault(path, []).append(copy.deepcopy(value))


class FakeGitHub:
    def __init__(self, *, exists=True, public=True, connector_accessible=True, full_name="owner/repo"):
        self.result = {
            "exists": exists,
            "public": public,
            "connector_accessible": connector_accessible,
            "full_name": full_name,
            "html_url": f"https://github.com/{full_name}",
            "default_branch": "main",
        }
        self.calls = []

    def verify_public_and_connector_accessible(self, repository):
        self.calls.append(repository)
        return dict(self.result)


class ProjectInitializerTests(unittest.TestCase):
    def setUp(self):
        self.board = FakeBoard()
        self.github = FakeGitHub()
        self.initializer = ProjectInitializer(self.board, self.github)
        self.intent = ProjectIntent(
            display_name="Fold Power Lab",
            problem_statement="Investigate Samsung foldable device power-management behavior.",
        )

    def test_requires_internal_board_backend(self):
        with self.assertRaises(ProjectInitializationError):
            ProjectInitializer(None)

    def test_begin_creates_internal_namespace_before_github(self):
        result = self.initializer.begin(self.intent)
        self.assertEqual(result.phase, "WAITING_FOR_GITHUB")
        self.assertEqual(result.next_action, "PROVIDE_GITHUB_REPOSITORY")
        self.assertIn("publicly", result.prompt)
        self.assertIn("GitHub integration", result.prompt)
        root = result.board_root
        self.assertIn(root, self.board.directories)
        self.assertIn(f"{root}/forums/primary", self.board.directories)
        self.assertIn(f"{root}/forums/managers", self.board.directories)
        self.assertIn(f"{root}/forums/research", self.board.directories)
        self.assertIn(f"{root}/bootstrap/initialization.json", self.board.objects)
        self.assertNotIn(f"{root}/identity/github-binding.json", self.board.objects)
        self.assertEqual(self.github.calls, [])

    def test_begin_is_resume_safe_after_interruption(self):
        first = self.initializer.begin(self.intent)
        directory_count = len(self.board.directories)
        object_count = len(self.board.objects)
        event_count = sum(len(v) for v in self.board.events.values())
        second = self.initializer.begin(self.intent)
        self.assertEqual(first.project_id, second.project_id)
        self.assertEqual(second.phase, "WAITING_FOR_GITHUB")
        self.assertEqual(directory_count, len(self.board.directories))
        self.assertEqual(object_count, len(self.board.objects))
        self.assertEqual(event_count, sum(len(v) for v in self.board.events.values()))

    def test_namespace_collision_with_different_intent_fails_closed(self):
        self.initializer.begin(self.intent)
        changed = ProjectIntent(
            display_name="Fold Power Lab",
            problem_statement="A materially different project using the same display name.",
        )
        with self.assertRaises(ProjectInitializationError):
            self.initializer.begin(changed)

    def test_existing_namespace_without_state_cannot_be_taken_over(self):
        project_id = derive_project_id(self.intent.display_name)
        self.board.create_directory(f"projects/{project_id}")
        with self.assertRaises(ProjectInitializationError):
            self.initializer.begin(self.intent)

    def test_github_binding_requires_internal_namespace(self):
        with self.assertRaises(ProjectInitializationError):
            self.initializer.bind_github("missing-project", "owner/repo")

    def test_private_github_repository_is_rejected(self):
        begin = self.initializer.begin(self.intent)
        initializer = ProjectInitializer(self.board, FakeGitHub(public=False))
        with self.assertRaises(ProjectInitializationError):
            initializer.bind_github(begin.project_id, "owner/private")
        self.assertFalse(self.board.object_exists(f"{begin.board_root}/identity/github-binding.json"))

    def test_connector_inaccessible_repository_is_rejected(self):
        begin = self.initializer.begin(self.intent)
        initializer = ProjectInitializer(self.board, FakeGitHub(connector_accessible=False))
        with self.assertRaises(ProjectInitializationError):
            initializer.bind_github(begin.project_id, "owner/repo")
        state = self.board.read_json(f"{begin.board_root}/bootstrap/initialization.json")
        self.assertEqual(state["phase"], "WAITING_FOR_GITHUB")

    def test_unresolvable_repository_is_rejected(self):
        begin = self.initializer.begin(self.intent)
        initializer = ProjectInitializer(self.board, FakeGitHub(exists=False))
        with self.assertRaises(ProjectInitializationError):
            initializer.bind_github(begin.project_id, "owner/missing")

    def test_successful_binding_completes_bootstrap(self):
        begin = self.initializer.begin(self.intent)
        complete = self.initializer.bind_github(begin.project_id, "owner/repo")
        self.assertEqual(complete.phase, "COMPLETE")
        self.assertEqual(complete.next_action, "START_PRIMARY_EXECUTION")
        self.assertEqual(complete.github_repository, "owner/repo")
        root = begin.board_root
        self.assertIn(f"{root}/identity/github-binding.json", self.board.objects)
        self.assertIn(f"{root}/handoffs/primary-bootstrap.json", self.board.objects)
        state = self.board.read_json(f"{root}/bootstrap/initialization.json")
        self.assertEqual(state["phase"], "COMPLETE")
        self.assertEqual(state["revision"], 2)
        self.assertEqual(state["github_repository"], "owner/repo")

    def test_repeat_binding_same_repo_is_idempotent(self):
        begin = self.initializer.begin(self.intent)
        self.initializer.bind_github(begin.project_id, "owner/repo")
        events_before = sum(len(v) for v in self.board.events.values())
        again = self.initializer.bind_github(begin.project_id, "owner/repo")
        self.assertEqual(again.phase, "COMPLETE")
        self.assertEqual(events_before, sum(len(v) for v in self.board.events.values()))

    def test_rebinding_complete_project_to_different_repo_is_rejected(self):
        begin = self.initializer.begin(self.intent)
        self.initializer.bind_github(begin.project_id, "owner/repo")
        with self.assertRaises(ProjectInitializationError):
            self.initializer.bind_github(begin.project_id, "owner/other")

    def test_missing_github_verifier_fails_closed_at_binding_only(self):
        initializer = ProjectInitializer(self.board, None)
        begin = initializer.begin(self.intent)
        self.assertEqual(begin.phase, "WAITING_FOR_GITHUB")
        with self.assertRaises(ProjectInitializationError):
            initializer.bind_github(begin.project_id, "owner/repo")

    def test_resume_returns_correct_next_action(self):
        begin = self.initializer.begin(self.intent)
        waiting = self.initializer.resume(begin.project_id)
        self.assertEqual(waiting.next_action, "PROVIDE_GITHUB_REPOSITORY")
        self.initializer.bind_github(begin.project_id, "owner/repo")
        finished = self.initializer.resume(begin.project_id)
        self.assertEqual(finished.next_action, "START_PRIMARY_EXECUTION")


if __name__ == "__main__":
    unittest.main()
