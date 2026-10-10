import copy
import unittest

from ipg3_project_initializer import (
    PrimaryBootstrapResult,
    ProjectInitializationError,
    ProjectInitializer,
    ProjectIntent,
    derive_project_id,
)


class FakeBoard:
    def __init__(self):
        self.directories = set()
        self.objects = {}

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


def good_primary_result(*, assistance=True):
    return PrimaryBootstrapResult(
        source_of_truth=("device behavior", "Android/Samsung power-management documentation"),
        workstreams=("architecture", "configuration surface", "modification feasibility"),
        assistance_required=assistance,
        research_agents=3 if assistance else 0,
        manager_agents=0,
        rationale=(
            "Three parallel technical fronts warrant targeted independent research."
            if assistance
            else "The initial problem is sufficiently narrow for Primary-local work."
        ),
    )


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
        self.assertIn(f"{root}/forums/primary/project-bootstrap.json", self.board.objects)
        self.assertNotIn(f"{root}/identity/github-binding.json", self.board.objects)
        self.assertEqual(self.github.calls, [])

    def test_begin_is_resume_safe_after_interruption(self):
        first = self.initializer.begin(self.intent)
        directory_count = len(self.board.directories)
        object_count = len(self.board.objects)
        second = self.initializer.begin(self.intent)
        self.assertEqual(first.project_id, second.project_id)
        self.assertEqual(second.phase, "WAITING_FOR_GITHUB")
        self.assertEqual(directory_count, len(self.board.directories))
        self.assertEqual(object_count, len(self.board.objects))

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

    def test_successful_binding_reaches_bound_not_complete(self):
        begin = self.initializer.begin(self.intent)
        bound = self.initializer.bind_github(begin.project_id, "owner/repo")
        self.assertEqual(bound.phase, "BOUND")
        self.assertEqual(bound.next_action, "COMPLETE_PRIMARY_BOOTSTRAP")
        self.assertEqual(bound.github_repository, "owner/repo")
        root = begin.board_root
        self.assertIn(f"{root}/identity/github-binding.json", self.board.objects)
        self.assertIn(f"{root}/handoffs/primary-bootstrap.json", self.board.objects)
        state = self.board.read_json(f"{root}/bootstrap/initialization.json")
        self.assertEqual(state["phase"], "BOUND")
        self.assertEqual(state["revision"], 2)

    def test_primary_bootstrap_cannot_complete_before_github_binding(self):
        begin = self.initializer.begin(self.intent)
        with self.assertRaises(ProjectInitializationError):
            self.initializer.complete_primary_bootstrap(begin.project_id, good_primary_result())

    def test_primary_bootstrap_requires_real_assessment(self):
        begin = self.initializer.begin(self.intent)
        self.initializer.bind_github(begin.project_id, "owner/repo")
        bad = PrimaryBootstrapResult(
            source_of_truth=(),
            workstreams=("one",),
            assistance_required=False,
            rationale="missing source of truth",
        )
        with self.assertRaises(ProjectInitializationError):
            self.initializer.complete_primary_bootstrap(begin.project_id, bad)

    def test_no_assistance_decision_cannot_allocate_agents(self):
        begin = self.initializer.begin(self.intent)
        self.initializer.bind_github(begin.project_id, "owner/repo")
        bad = PrimaryBootstrapResult(
            source_of_truth=("source",),
            workstreams=("one",),
            assistance_required=False,
            research_agents=1,
            manager_agents=0,
            rationale="contradictory allocation",
        )
        with self.assertRaises(ProjectInitializationError):
            self.initializer.complete_primary_bootstrap(begin.project_id, bad)

    def test_assistance_decision_requires_research_capacity(self):
        begin = self.initializer.begin(self.intent)
        self.initializer.bind_github(begin.project_id, "owner/repo")
        bad = PrimaryBootstrapResult(
            source_of_truth=("source",),
            workstreams=("one",),
            assistance_required=True,
            research_agents=0,
            manager_agents=0,
            rationale="assistance requested with no capacity",
        )
        with self.assertRaises(ProjectInitializationError):
            self.initializer.complete_primary_bootstrap(begin.project_id, bad)

    def test_primary_bootstrap_completes_full_initialization(self):
        begin = self.initializer.begin(self.intent)
        self.initializer.bind_github(begin.project_id, "owner/repo")
        complete = self.initializer.complete_primary_bootstrap(begin.project_id, good_primary_result())
        self.assertEqual(complete.phase, "COMPLETE")
        self.assertEqual(complete.next_action, "EXECUTE_PROJECT_WORK")
        root = begin.board_root
        self.assertIn(f"{root}/bootstrap/primary-initialization.json", self.board.objects)
        self.assertIn(f"{root}/swarm/initial-assessment.json", self.board.objects)
        state = self.board.read_json(f"{root}/bootstrap/initialization.json")
        self.assertEqual(state["phase"], "COMPLETE")
        self.assertEqual(state["revision"], 3)

    def test_repeat_binding_same_repo_is_idempotent_while_bound(self):
        begin = self.initializer.begin(self.intent)
        first = self.initializer.bind_github(begin.project_id, "owner/repo")
        object_count = len(self.board.objects)
        again = self.initializer.bind_github(begin.project_id, "owner/repo")
        self.assertEqual(first.phase, "BOUND")
        self.assertEqual(again.phase, "BOUND")
        self.assertEqual(object_count, len(self.board.objects))

    def test_repeat_primary_completion_same_result_is_idempotent(self):
        begin = self.initializer.begin(self.intent)
        self.initializer.bind_github(begin.project_id, "owner/repo")
        result = good_primary_result()
        self.initializer.complete_primary_bootstrap(begin.project_id, result)
        object_count = len(self.board.objects)
        again = self.initializer.complete_primary_bootstrap(begin.project_id, result)
        self.assertEqual(again.phase, "COMPLETE")
        self.assertEqual(object_count, len(self.board.objects))

    def test_completed_primary_bootstrap_cannot_be_rewritten(self):
        begin = self.initializer.begin(self.intent)
        self.initializer.bind_github(begin.project_id, "owner/repo")
        self.initializer.complete_primary_bootstrap(begin.project_id, good_primary_result())
        changed = PrimaryBootstrapResult(
            source_of_truth=("different",),
            workstreams=("different",),
            assistance_required=False,
            rationale="different result",
        )
        with self.assertRaises(ProjectInitializationError):
            self.initializer.complete_primary_bootstrap(begin.project_id, changed)

    def test_crash_after_bootstrap_records_before_state_update_is_recoverable(self):
        begin = self.initializer.begin(self.intent)
        self.initializer.bind_github(begin.project_id, "owner/repo")
        result = good_primary_result()
        self.initializer.complete_primary_bootstrap(begin.project_id, result)
        state_path = f"{begin.board_root}/bootstrap/initialization.json"
        state = self.board.read_json(state_path)
        state["phase"] = "BOUND"
        state["revision"] = 2
        self.board.write_json(state_path, state)
        recovered = self.initializer.complete_primary_bootstrap(begin.project_id, result)
        self.assertEqual(recovered.phase, "COMPLETE")
        self.assertEqual(self.board.read_json(state_path)["revision"], 3)

    def test_rebinding_project_to_different_repo_is_rejected(self):
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

    def test_resume_returns_correct_next_action_across_phases(self):
        begin = self.initializer.begin(self.intent)
        waiting = self.initializer.resume(begin.project_id)
        self.assertEqual(waiting.next_action, "PROVIDE_GITHUB_REPOSITORY")
        self.initializer.bind_github(begin.project_id, "owner/repo")
        bound = self.initializer.resume(begin.project_id)
        self.assertEqual(bound.next_action, "COMPLETE_PRIMARY_BOOTSTRAP")
        self.initializer.complete_primary_bootstrap(begin.project_id, good_primary_result())
        finished = self.initializer.resume(begin.project_id)
        self.assertEqual(finished.next_action, "EXECUTE_PROJECT_WORK")


if __name__ == "__main__":
    unittest.main()
