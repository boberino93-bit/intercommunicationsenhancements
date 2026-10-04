"""IPG3 design-only new-project initializer.

The internal Artifactory/message-board plane is the first persistent home of a project.
GitHub is an external code repository binding that happens only after the internal
project namespace, identity, forums, audit trail and bootstrap state exist.

This module intentionally depends on injected backends. The ChatGPT runtime must supply
an internal message-board backend and a GitHub connector verifier. If either authority
boundary is unavailable, the initializer fails closed rather than silently substituting
another storage plane.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
    def append_event(self, path: str, value: dict[str, Any]) -> None: ...


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


def _fingerprint_intent(intent: ProjectIntent) -> str:
    encoded = json.dumps(
        {
            "display_name": intent.display_name.strip(),
            "problem_statement": intent.problem_statement.strip(),
            "requested_by": intent.requested_by,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_phase(value: str) -> None:
    if value not in PHASES:
        raise ProjectInitializationError(f"invalid initialization phase: {value}")


class ProjectInitializer:
    """Two-stage initializer: create internal project state, then bind GitHub."""

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

    def begin(self, intent: ProjectIntent) -> InitResult:
        """Create or safely resume the internal project namespace.

        This method MUST NOT require a GitHub repository. It stops at WAITING_FOR_GITHUB.
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
            phase = state.get("phase")
            _require_phase(phase)
            if phase in {"WAITING_FOR_GITHUB", "GITHUB_VERIFIED", "BOUND", "COMPLETE"}:
                return InitResult(
                    project_id=project_id,
                    board_root=root,
                    phase=phase,
                    next_action=("PROVIDE_GITHUB_REPOSITORY" if phase == "WAITING_FOR_GITHUB" else "RESUME_BINDING"),
                    prompt=(GitHubBindingRequirement().prompt if phase == "WAITING_FOR_GITHUB" else None),
                    github_repository=state.get("github_repository"),
                )
            raise ProjectInitializationError(f"project initialization is incomplete at unsupported resume phase {phase}")

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
        self.board.write_json(self._state_path(project_id), state, create_only=True)
        self.board.write_json(
            f"{root}/identity/project.json",
            {
                "schema": "org-agent-mesh/project-identity-seed/v1-draft",
                "project_id": project_id,
                "display_name": intent.display_name.strip(),
                "authority_state": "UNBOUND_EXTERNAL_REPOSITORY",
            },
            create_only=True,
        )
        self.board.write_json(
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
            create_only=True,
        )
        self.board.write_json(
            f"{root}/swarm/state.json",
            {
                "schema": "org-agent-mesh/swarm-bootstrap-state/v1-draft",
                "project_id": project_id,
                "status": "NOT_ALLOCATED",
                "research_agents": 0,
                "manager_agents": 0,
                "revision": 0,
            },
            create_only=True,
        )
        self.board.append_event(
            f"{root}/audit/events",
            {
                "event": "PROJECT_INTERNAL_NAMESPACE_INITIALIZED",
                "project_id": project_id,
                "phase": "WAITING_FOR_GITHUB",
                "revision": 1,
            },
        )
        self.board.append_event(
            f"{root}/forums/primary/events",
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
        """Verify a public connector-accessible GitHub repo and complete the binding."""
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

        if phase == "COMPLETE":
            if state.get("github_repository") != repository:
                raise ProjectInitializationError("project is already bound to a different GitHub repository")
            return InitResult(
                project_id=project_id,
                board_root=self._root(project_id),
                phase="COMPLETE",
                next_action="START_PRIMARY_EXECUTION",
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
        self.board.write_json(
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
            create_only=True,
        )
        next_state = dict(state)
        next_state.update(
            {
                "phase": "COMPLETE",
                "github_repository": canonical,
                "revision": int(state.get("revision", 0)) + 1,
            }
        )
        self.board.write_json(state_path, next_state)
        self.board.write_json(
            f"{root}/handoffs/primary-bootstrap.json",
            {
                "schema": "org-agent-mesh/primary-bootstrap-handoff/v1-draft",
                "project_id": project_id,
                "github_repository": canonical,
                "internal_board_root": root,
                "instructions": [
                    "Validate project identity and GitHub binding before mutation.",
                    "Treat the internal board as canonical coordination state.",
                    "Perform initial problem decomposition and assistance-need assessment.",
                    "Use adaptive swarm regulation before requesting research/manager allocation.",
                    "Persist decisions, evidence, handoffs and swarm state under this project namespace only.",
                ],
            },
            create_only=True,
        )
        self.board.append_event(
            f"{root}/audit/events",
            {
                "event": "GITHUB_REPOSITORY_BOUND",
                "project_id": project_id,
                "repository": canonical,
                "revision": next_state["revision"],
            },
        )
        self.board.append_event(
            f"{root}/forums/primary/events",
            {
                "kind": "PRIMARY_BOOTSTRAP_READY",
                "project_id": project_id,
                "repository": canonical,
                "message": "GitHub binding verified. Primary may continue project initialization under normal authority rules.",
            },
        )
        return InitResult(
            project_id=project_id,
            board_root=root,
            phase="COMPLETE",
            next_action="START_PRIMARY_EXECUTION",
            github_repository=canonical,
        )

    def resume(self, project_id: str) -> InitResult:
        state_path = self._state_path(project_id)
        if not self.board.object_exists(state_path):
            raise ProjectInitializationError("unknown project initialization")
        state = self.board.read_json(state_path)
        phase = state.get("phase")
        _require_phase(phase)
        return InitResult(
            project_id=project_id,
            board_root=self._root(project_id),
            phase=phase,
            next_action=("PROVIDE_GITHUB_REPOSITORY" if phase == "WAITING_FOR_GITHUB" else "START_PRIMARY_EXECUTION"),
            prompt=(GitHubBindingRequirement().prompt if phase == "WAITING_FOR_GITHUB" else None),
            github_repository=state.get("github_repository"),
        )
