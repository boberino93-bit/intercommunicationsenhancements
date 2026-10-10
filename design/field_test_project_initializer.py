"""End-to-end synthetic campaign for the Artifactory-first new-project initializer."""

from test_ipg3_project_initializer import FakeBoard, FakeGitHub, good_primary_result
from ipg3_project_initializer import ProjectInitializationError, ProjectInitializer, ProjectIntent


def assert_true(value, message):
    if not value:
        raise SystemExit(message)


def main():
    board = FakeBoard()
    intent = ProjectIntent(
        display_name="Fold Power Lab",
        problem_statement="Investigate Samsung foldable device power-management behavior.",
    )

    # 1. Internal namespace is created without touching GitHub.
    no_github = ProjectInitializer(board, None)
    first = no_github.begin(intent)
    assert_true(first.phase == "WAITING_FOR_GITHUB", "expected WAITING_FOR_GITHUB after internal bootstrap")
    directory_count = len(board.directories)
    object_count = len(board.objects)

    # 2. Simulate interruption and fresh-agent resume. No duplicate state is allowed.
    replacement_agent = ProjectInitializer(board, None)
    resumed = replacement_agent.begin(intent)
    assert_true(resumed.project_id == first.project_id, "replacement agent changed project identity")
    assert_true(len(board.directories) == directory_count, "resume duplicated internal directories")
    assert_true(len(board.objects) == object_count, "resume duplicated bootstrap objects")

    # 3. A private repository must fail without damaging the internal bootstrap state.
    private = ProjectInitializer(board, FakeGitHub(public=False, full_name="owner/private"))
    try:
        private.bind_github(first.project_id, "owner/private")
    except ProjectInitializationError:
        pass
    else:
        raise SystemExit("private GitHub repository was incorrectly accepted")
    state_path = f"{first.board_root}/bootstrap/initialization.json"
    assert_true(board.read_json(state_path)["phase"] == "WAITING_FOR_GITHUB", "private rejection changed phase")

    # 4. Public-but-connector-inaccessible must also fail closed.
    inaccessible = ProjectInitializer(
        board,
        FakeGitHub(public=True, connector_accessible=False, full_name="owner/public-but-unavailable"),
    )
    try:
        inaccessible.bind_github(first.project_id, "owner/public-but-unavailable")
    except ProjectInitializationError:
        pass
    else:
        raise SystemExit("connector-inaccessible repository was incorrectly accepted")
    assert_true(board.read_json(state_path)["phase"] == "WAITING_FOR_GITHUB", "connector rejection changed phase")

    # 5. Public + connector-accessible reaches BOUND and creates Primary handoff.
    valid = ProjectInitializer(board, FakeGitHub(full_name="owner/fold-power-lab"))
    bound = valid.bind_github(first.project_id, "owner/fold-power-lab")
    assert_true(bound.phase == "BOUND", "valid GitHub binding did not reach BOUND")
    assert_true(bound.next_action == "COMPLETE_PRIMARY_BOOTSTRAP", "binding skipped Primary bootstrap requirement")
    assert_true(
        board.object_exists(f"{first.board_root}/handoffs/primary-bootstrap.json"),
        "Primary bootstrap handoff was not created",
    )

    # 6. The Primary's initial source/workstream/swarm assessment is mandatory for COMPLETE.
    complete = valid.complete_primary_bootstrap(first.project_id, good_primary_result())
    assert_true(complete.phase == "COMPLETE", "Primary bootstrap did not complete initialization")
    assert_true(complete.next_action == "EXECUTE_PROJECT_WORK", "completed initializer has wrong next action")
    assert_true(
        board.object_exists(f"{first.board_root}/bootstrap/primary-initialization.json"),
        "structured Primary initialization result was not persisted",
    )
    assert_true(
        board.object_exists(f"{first.board_root}/swarm/initial-assessment.json"),
        "initial swarm assessment was not persisted",
    )

    # 7. Same-repo/result replay is idempotent; different-repo replay fails.
    final_object_count = len(board.objects)
    same_repo = valid.bind_github(first.project_id, "owner/fold-power-lab")
    same_result = valid.complete_primary_bootstrap(first.project_id, good_primary_result())
    assert_true(same_repo.phase == "COMPLETE", "same-repo replay did not resume COMPLETE state")
    assert_true(same_result.phase == "COMPLETE", "same Primary result replay did not remain COMPLETE")
    assert_true(len(board.objects) == final_object_count, "replay created duplicate bootstrap objects")
    try:
        valid.bind_github(first.project_id, "owner/other")
    except ProjectInitializationError:
        pass
    else:
        raise SystemExit("completed project was silently rebound to another repository")

    print("PROJECT INITIALIZER FIELD TEST PASS")
    print("- internal board created before GitHub interaction")
    print("- interrupted agent resumed without duplicate state")
    print("- private repository rejected")
    print("- connector-inaccessible repository rejected")
    print("- public connector-accessible repository reached BOUND")
    print("- Primary source/workstream/swarm assessment required before COMPLETE")
    print("- full initialization completed and persisted")
    print("- completed bootstrap remained replay-safe and non-rebindable")


if __name__ == "__main__":
    main()
