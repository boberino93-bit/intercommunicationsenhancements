"""IPG3 design-only new-project initializer.

The internal Artifactory/message-board plane is the first persistent home of a project.
GitHub is an external code repository binding that happens only after the internal
project namespace, identity, forums and bootstrap state exist.

The initializer is intentionally interruption-safe. Stable bootstrap records use
create-or-match semantics so a replacement agent can resume without duplicating state.
The ChatGPT runtime must supply an internal message-board backend and a GitHub connector
verifier. Missing authority boundaries fail closed; GitHub is never substituted for the
internal coordination plane.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from hashlib import sha256
from typing import Any, Protocol
import json
import re


class ProjectInitializationError(RuntimeError):
    pass


class InternalBoardBackend(Protocol):
    """Minimal adapter for the internal Artifactory/message-board namespace."""

    def directory_exists(self, path: str) -> bool: ...
    def create_directory(self, path: str) -> None: ...
    def object_exists(self, path: str) -> bool: ...
    def write_json(self, path: str, value: dict[str, Any], *, create_only: bool = False) -> None: ...
    def read_json(self, path: str) -> dict[str, Any]: ...


class GitHubRepositoryVerifier(Protocol):
    """Implemented by an environment able to call ChatGPT's GitHub integration."""

    def verify_public_and_connector_accessible(self, repository: str) -> dict[str, Any]: ...


@dataclass(frozen=True)
class GitHubBindingRequirement:
    must_be_public: bool = True
    must_be_connector_accessible: bool = True
    prompt: str = (
        "Please provide the GitHub repository for this project. It must be publicly "
        "shared and accessible through the GitHub integration connected to ChatGPT."
    )


@dataclass(frozen=True)
class ProjectIntent:
    display_name: str
    problem_statement: str
    requested_by: str = "human"


@dataclass(frozen=True)
class PrimaryBootstrapResult:
    """Structured result of the Primary's mandatory initial project assessment."""

    source_of_truth: tuple[str, ...]
    workstreams: tuple[str, ...]
    assistance_required: bool
    research_agents: int = 0
    manager_agents: int = 0
    rationale: str = ""


@dataclass
class InitResult:
    project_id: str
    board_root: str
    phase: str
    next_action: str
    prompt: str | None = None
    github_repository: str | None = None
    created_paths: tuple[str, ...] = field(default_factory=tuple)


PHASES = (
    "NEW",
    "BOARD_RESERVED",
    "BOARD_BOOTSTRAPPED",
    "WAITING_FOR_GITHUB",
    "GITHUB_VERIFIED",
    "BOUND",
    "PRIMARY_INITIALIZING",
    "COMPLETE",
)


def derive_project_id(display_name: str) -> str:
    """Create a stable canonical project ID for a *new* project."""
    original = display_name.strip()
    if not original:
        raise ProjectInitializationError("project display name is required")
    stem = re.sub(r"[^a-z0-9]+", "-", original.lower()).strip("-") or "project"
    stem = stem[:48].rstrip("-")
    digest = sha256(original.encode("utf-8")).hexdigest()[:8]
    return f"{stem}-{digest}"


def _canonical_digest(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(encoded).hexdigest()


def _fingerprint_intent(intent: ProjectIntent) -> str:
    return _canonical_digest(
        {
            "display_name": intent.display_name.strip(),
            "problem_statement": intent.problem_statement.strip(),
            "requested_by": intent.requested_by,
        }
    )


def _require_phase(value: str) -> None:
    if value not in PHASES:
        raise ProjectInitializationError(f"invalid initialization phase: {value}")


def _validate_primary_bootstrap(result: PrimaryBootstrapResult) -> None:
    if not result.source_of_truth or any(not value.strip() for value in result.source_of_truth):
        raise ProjectInitializationError("Primary bootstrap requires at least one source-of-truth reference")
    if not result.workstreams or any(not value.strip() for value in result.workstreams):
        raise ProjectInitializationError("Primary bootstrap requires at least one workstream")
    if result.research_agents < 0 or result.manager_agents < 0:
        raise ProjectInitializationError("agent counts cannot be negative")
    if not result.rationale.strip():
        raise ProjectInitializationError("Primary bootstrap requires an allocation/assistance rationale")
    if result.assistance_required:
        if result.research_agents < 1:
            raise ProjectInitializationError("assistance_required requires at least one Research agent")
        if result.manager_agents > result.research_agents:
            raise ProjectInitializationError("Manager count cannot exceed Research count")
    elif result.research_agents != 0 or result.manager_agents != 0:
        raise ProjectInitializationError("no-assistance bootstrap must allocate zero Research/Manager agents")


class ProjectInitializer:
    """Three-stage initializer: internal board -> GitHub binding -> Primary bootstrap."""

    REQUIRED_DIRECTORIES = (
        "bootstrap",
        "identity",
        "forums",
        "forums/primary",
        "forums/managers",
        "forums/research",
        "queues",
        "handoffs",
        "evidence",
        "audit",
        "swarm",
        "artifacts",
    )

    def __init__(
        self,
        board: InternalBoardBackend | None,
        github: GitHubRepositoryVerifier | None = None,
        *,
        projects_root: str = "projects",
    ):
        if board is None:
            raise ProjectInitializationError(
                "internal Artifactory/message-board backend is unavailable; initialization must fail closed"
            )
        self.board = board
        self.github = github
        self.projects_root = projects_root.strip("/") or "projects"

    def _root(self, project_id: str) -> str:
        return f"{self.projects_root}/{project_id}"

    def _state_path(self, project_id: str) -> str:
        return f"{self._root(project_id)}/bootstrap/initialization.json"

    def _write_create_or_match(self, path: str, value: dict[str, Any]) -> None:
        if self.board.object_exists(path):
            if self.board.read_json(path) != value:
                raise ProjectInitializationError(f"existing bootstrap object conflicts with expected value: {path}")
            return
        self.board.write_json(path, value, create_only=True)

    def begin(self, intent: ProjectIntent) -> InitResult:
        """Create or safely resume the internal project namespace.

        This method MUST NOT require or contact GitHub. It stops at WAITING_FOR_GITHUB.
        """
        if not intent.problem_statement.strip():
            raise ProjectInitializationError("problem statement is required")
        project_id = derive_project_id(intent.display_name)
        root = self._root(project_id)
        fingerprint = _fingerprint_intent(intent)
        created: list[str] = []

        if self.board.directory_exists(root):
            state_path = self._state_path(project_id)
            if not self.board.object_exists(state_path):
                raise ProjectInitializationError(
                    "project namespace exists without initialization state; refusing ambiguous takeover"
                )
            state = self.board.read_json(state_path)
            if state.get("intent_fingerprint") != fingerprint:
                raise ProjectInitializationError(
                    "project namespace collision: existing project intent does not match requested initialization"
                )
            return self.resume(project_id)

        self.board.create_directory(root)
        created.append(root)
        for suffix in self.REQUIRED_DIRECTORIES:
            path = f"{root}/{suffix}"
            self.board.create_directory(path)
            created.append(path)

        state = {
            "schema": "org-agent-mesh/project-initialization/v1-draft",
            "project_id": project_id,
            "display_name": intent.display_name.strip(),
            "problem_statement": intent.problem_statement.strip(),
            "requested_by": intent.requested_by,
            "intent_fingerprint": fingerprint,
            "phase": "WAITING_FOR_GITHUB",
            "github_repository": None,
            "revision": 1,
        }
        self._write_create_or_match(self._state_path(project_id), state)
        self._write_create_or_match(
            f"{root}/identity/project.json",
            {
                "schema": "org-agent-mesh/project-identity-seed/v1-draft",
                "project_id": project_id,
                "display_name": intent.display_name.strip(),
                "authority_state": "UNBOUND_EXTERNAL_REPOSITORY",
            },
        )
        self._write_create_or_match(
            f"{root}/forums/index.json",
            {
                "schema": "org-agent-mesh/internal-forum-index/v1-draft",
                "project_id": project_id,
                "forums": {
                    "primary": f"{root}/forums/primary",
                    "managers": f"{root}/forums/managers",
                    "research": f"{root}/forums/research",
                },
            },
        )
        self._write_create_or_match(
            f"{root}/swarm/state.json",
            {
                "schema": "org-agent-mesh/swarm-bootstrap-state/v1-draft",
                "project_id": project_id,
                "status": "NOT_ALLOCATED",
                "research_agents": 0,
                "manager_agents": 0,
                "revision": 0,
            },
        )
        self._write_create_or_match(
            f"{root}/audit/project-internal-namespace-initialized.json",
            {
                "event": "PROJECT_INTERNAL_NAMESPACE_INITIALIZED",
                "project_id": project_id,
                "phase": "WAITING_FOR_GITHUB",
                "revision": 1,
            },
        )
        self._write_create_or_match(
            f"{root}/forums/primary/project-bootstrap.json",
            {
                "kind": "PROJECT_BOOTSTRAP",
                "project_id": project_id,
                "message": "Internal project namespace initialized. Awaiting validated public GitHub repository binding.",
            },
        )
        return InitResult(
            project_id=project_id,
            board_root=root,
            phase="WAITING_FOR_GITHUB",
            next_action="PROVIDE_GITHUB_REPOSITORY",
            prompt=GitHubBindingRequirement().prompt,
            created_paths=tuple(created),
        )

    def bind_github(self, project_id: str, repository: str) -> InitResult:
        """Verify a public connector-accessible GitHub repo and persist the binding.

        Binding reaches BOUND, not COMPLETE. The Primary must still perform the mandatory
        initial project assessment and persist it with complete_primary_bootstrap().
        """
        if self.github is None:
            raise ProjectInitializationError(
                "GitHub verifier is unavailable; cannot prove public connector accessibility"
            )
        state_path = self._state_path(project_id)
        if not self.board.object_exists(state_path):
            raise ProjectInitializationError("internal project namespace must exist before GitHub binding")
        state = self.board.read_json(state_path)
        phase = state.get("phase")
        _require_phase(phase)

        if phase in {"BOUND", "PRIMARY_INITIALIZING", "COMPLETE"}:
            if state.get("github_repository") != repository:
                raise ProjectInitializationError("project is already bound to a different GitHub repository")
            return InitResult(
                project_id=project_id,
                board_root=self._root(project_id),
                phase=phase,
                next_action=("EXECUTE_PROJECT_WORK" if phase == "COMPLETE" else "COMPLETE_PRIMARY_BOOTSTRAP"),
                github_repository=repository,
            )
        if phase != "WAITING_FOR_GITHUB":
            raise ProjectInitializationError(f"GitHub binding is not permitted from phase {phase}")

        verification = self.github.verify_public_and_connector_accessible(repository)
        if not verification.get("exists"):
            raise ProjectInitializationError("GitHub repository could not be resolved")
        if not verification.get("public"):
            raise ProjectInitializationError("GitHub repository must be public")
        if not verification.get("connector_accessible"):
            raise ProjectInitializationError(
                "GitHub repository is not accessible through the connected ChatGPT GitHub integration"
            )
        canonical = verification.get("full_name") or repository
        root = self._root(project_id)
        self._write_create_or_match(
            f"{root}/identity/github-binding.json",
            {
                "schema": "org-agent-mesh/github-binding/v1-draft",
                "project_id": project_id,
                "repository": canonical,
                "html_url": verification.get("html_url"),
                "default_branch": verification.get("default_branch"),
                "public": True,
                "connector_accessible": True,
            },
        )
        self._write_create_or_match(
            f"{root}/handoffs/primary-bootstrap.json",
            {
                "schema": "org-agent-mesh/primary-bootstrap-handoff/v1-draft",
                "project_id": project_id,
                "github_repository": canonical,
                "internal_board_root": root,
                "instructions": [
                    "Validate project identity and GitHub binding before mutation.",
                    "Treat the internal board as canonical coordination state.",
                    "Perform source-of-truth discovery and initial problem decomposition.",
                    "Perform assistance-need assessment using adaptive swarm regulation.",
                    "Persist the structured Primary bootstrap result before project initialization is COMPLETE.",
                ],
            },
        )
        self._write_create_or_match(
            f"{root}/audit/github-repository-bound.json",
            {
                "event": "GITHUB_REPOSITORY_BOUND",
                "project_id": project_id,
                "repository": canonical,
                "target_revision": int(state.get("revision", 0)) + 1,
            },
        )
        self._write_create_or_match(
            f"{root}/forums/primary/primary-bootstrap-ready.json",
            {
                "kind": "PRIMARY_BOOTSTRAP_READY",
                "project_id": project_id,
                "repository": canonical,
                "message": "GitHub binding verified. Primary must complete initial project assessment before initialization is complete.",
            },
        )
        next_state = dict(state)
        next_state.update(
            {
                "phase": "BOUND",
                "github_repository": canonical,
                "revision": int(state.get("revision", 0)) + 1,
            }
        )
        self.board.write_json(state_path, next_state)
        return InitResult(
            project_id=project_id,
            board_root=root,
            phase="BOUND",
            next_action="COMPLETE_PRIMARY_BOOTSTRAP",
            github_repository=canonical,
        )

    def complete_primary_bootstrap(self, project_id: str, result: PrimaryBootstrapResult) -> InitResult:
        """Persist initial Primary assessment and finish project initialization."""
        _validate_primary_bootstrap(result)
        state_path = self._state_path(project_id)
        if not self.board.object_exists(state_path):
            raise ProjectInitializationError("unknown project initialization")
        state = self.board.read_json(state_path)
        phase = state.get("phase")
        _require_phase(phase)
        if phase not in {"BOUND", "PRIMARY_INITIALIZING", "COMPLETE"}:
            raise ProjectInitializationError(f"Primary bootstrap is not permitted from phase {phase}")
        repository = state.get("github_repository")
        if not repository:
            raise ProjectInitializationError("Primary bootstrap requires a bound GitHub repository")

        root = self._root(project_id)
        result_payload = {
            "source_of_truth": list(result.source_of_truth),
            "workstreams": list(result.workstreams),
            "assistance_required": result.assistance_required,
            "research_agents": result.research_agents,
            "manager_agents": result.manager_agents,
            "rationale": result.rationale.strip(),
        }
        result_fingerprint = _canonical_digest(result_payload)
        record = {
            "schema": "org-agent-mesh/primary-initialization-result/v1-draft",
            "project_id": project_id,
            "github_repository": repository,
            **result_payload,
            "result_fingerprint": result_fingerprint,
        }

        result_path = f"{root}/bootstrap/primary-initialization.json"
        if phase == "COMPLETE":
            if not self.board.object_exists(result_path) or self.board.read_json(result_path) != record:
                raise ProjectInitializationError("completed project bootstrap does not match supplied result")
            return InitResult(
                project_id=project_id,
                board_root=root,
                phase="COMPLETE",
                next_action="EXECUTE_PROJECT_WORK",
                github_repository=repository,
            )

        self._write_create_or_match(result_path, record)
        self._write_create_or_match(
            f"{root}/swarm/initial-assessment.json",
            {
                "schema": "org-agent-mesh/initial-swarm-assessment/v1-draft",
                "project_id": project_id,
                "assistance_required": result.assistance_required,
                "research_agents": result.research_agents,
                "manager_agents": result.manager_agents,
                "rationale": result.rationale.strip(),
                "source_result_fingerprint": result_fingerprint,
            },
        )
        self._write_create_or_match(
            f"{root}/audit/project-initialization-complete.json",
            {
                "event": "PROJECT_INITIALIZATION_COMPLETE",
                "project_id": project_id,
                "repository": repository,
                "result_fingerprint": result_fingerprint,
                "target_revision": int(state.get("revision", 0)) + 1,
            },
        )
        self._write_create_or_match(
            f"{root}/forums/primary/project-initialization-complete.json",
            {
                "kind": "PROJECT_INITIALIZATION_COMPLETE",
                "project_id": project_id,
                "repository": repository,
                "message": "Initial source-of-truth, workstream and assistance assessment persisted. Project work may begin.",
            },
        )
        next_state = dict(state)
        next_state.update({"phase": "COMPLETE", "revision": int(state.get("revision", 0)) + 1})
        self.board.write_json(state_path, next_state)
        return InitResult(
            project_id=project_id,
            board_root=root,
            phase="COMPLETE",
            next_action="EXECUTE_PROJECT_WORK",
            github_repository=repository,
        )

    def resume(self, project_id: str) -> InitResult:
        state_path = self._state_path(project_id)
        if not self.board.object_exists(state_path):
            raise ProjectInitializationError("unknown project initialization")
        state = self.board.read_json(state_path)
        phase = state.get("phase")
        _require_phase(phase)
        if phase == "WAITING_FOR_GITHUB":
            next_action = "PROVIDE_GITHUB_REPOSITORY"
            prompt = GitHubBindingRequirement().prompt
        elif phase in {"BOUND", "PRIMARY_INITIALIZING"}:
            next_action = "COMPLETE_PRIMARY_BOOTSTRAP"
            prompt = None
        elif phase == "COMPLETE":
            next_action = "EXECUTE_PROJECT_WORK"
            prompt = None
        else:
            raise ProjectInitializationError(f"initialization cannot safely resume from phase {phase}")
        return InitResult(
            project_id=project_id,
            board_root=self._root(project_id),
            phase=phase,
            next_action=next_action,
            prompt=prompt,
            github_repository=state.get("github_repository"),
        )
