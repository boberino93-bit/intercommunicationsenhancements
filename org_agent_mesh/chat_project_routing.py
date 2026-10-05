from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional, Protocol

from .project_scope import require_project_id, require_resource_id


DEFAULT_CHAT_PROJECT_MAPPING = {
    "intercommunicationsenhancements": "Intercommunication enhancements",
    "duo-open": "Duo Screen",
    "benefitflow": "Benefitflow",
    "fold7-power-lab": "Samsung power bootstrap",
    "warp-propulsion-lab": "Warp-Propulsion-lab",
    "ai-behaviour-control-lab": "Ai Behavior Control Lab",
}


class ChatProjectAdapter(Protocol):
    """Host adapter; implement with a supported ChatGPT Project API or UI automation."""

    def supports_direct_create(self) -> bool: ...
    def create_conversation(self, *, title: str, project: Optional[str]) -> str: ...
    def move_conversation(self, *, conversation_id: str, project: str) -> None: ...
    def detect_project(self, *, conversation_id: str) -> Optional[str]: ...


@dataclass(frozen=True)
class ProjectAssignmentResult:
    status: str
    agent_id: str
    conversation_id: Optional[str]
    expected_project: Optional[str]
    detected_project: Optional[str]
    method: str
    message: str


class ChatProjectRouter:
    """Fail-closed ChatGPT sidebar Project placement with post-action verification."""

    def __init__(
        self,
        adapter: ChatProjectAdapter,
        mapping: Mapping[str, str] | None = None,
        *,
        max_move_attempts: int = 3,
    ):
        self.adapter = adapter
        self.mapping = dict(mapping or DEFAULT_CHAT_PROJECT_MAPPING)
        if max_move_attempts < 1:
            raise ValueError("max_move_attempts must be >= 1")
        self.max_move_attempts = max_move_attempts

    def assign(
        self,
        *,
        agent_id: str,
        agent_type: str,
        project_id: Optional[str],
        title: str,
        roaming: bool = False,
        conversation_id: Optional[str] = None,
    ) -> ProjectAssignmentResult:
        agent_id = require_resource_id(agent_id, field="agent_id")
        agent_type = agent_type.strip().lower()

        if roaming or agent_type == "master":
            if project_id is not None:
                return ProjectAssignmentResult(
                    "FAIL", agent_id, conversation_id, None, None, "none",
                    "roaming/master agent must not be project-bound",
                )
            if conversation_id is None:
                conversation_id = self.adapter.create_conversation(title=title, project=None)
            detected = self.adapter.detect_project(conversation_id=conversation_id)
            if detected is not None:
                return ProjectAssignmentResult(
                    "FAIL", agent_id, conversation_id, None, detected, "verify",
                    "Master/global conversation is unexpectedly attached to a project",
                )
            return ProjectAssignmentResult(
                "SKIPPED", agent_id, conversation_id, None, None, "global",
                "Global roaming agent; no ChatGPT Project assignment",
            )

        if project_id is None:
            return ProjectAssignmentResult(
                "FAIL", agent_id, conversation_id, None, None, "none",
                "No configured project_id; conversation left unchanged",
            )
        project_id = require_project_id(project_id)
        expected = self.mapping.get(project_id)
        if expected is None:
            return ProjectAssignmentResult(
                "FAIL", agent_id, conversation_id, None, None, "none",
                "No configured ChatGPT Project mapping; conversation left unchanged",
            )

        if conversation_id is not None:
            detected = self.adapter.detect_project(conversation_id=conversation_id)
            if detected == expected:
                return ProjectAssignmentResult(
                    "OK", agent_id, conversation_id, expected, detected, "already-assigned",
                    "Conversation already belongs to the expected project",
                )

        if conversation_id is None and self.adapter.supports_direct_create():
            conversation_id = self.adapter.create_conversation(title=title, project=expected)
            detected = self.adapter.detect_project(conversation_id=conversation_id)
            if detected == expected:
                return ProjectAssignmentResult(
                    "OK", agent_id, conversation_id, expected, detected, "direct-create",
                    "ChatGPT Project assignment verified",
                )
            return ProjectAssignmentResult(
                "FAIL", agent_id, conversation_id, expected, detected, "direct-create",
                "Direct create returned but project verification failed",
            )

        if conversation_id is None:
            conversation_id = self.adapter.create_conversation(title=title, project=None)

        detected = self.adapter.detect_project(conversation_id=conversation_id)
        for _ in range(self.max_move_attempts):
            if detected == expected:
                return ProjectAssignmentResult(
                    "OK", agent_id, conversation_id, expected, detected, "move",
                    "ChatGPT Project assignment verified",
                )
            self.adapter.move_conversation(conversation_id=conversation_id, project=expected)
            detected = self.adapter.detect_project(conversation_id=conversation_id)

        return ProjectAssignmentResult(
            "FAIL", agent_id, conversation_id, expected, detected, "move",
            "Project placement could not be verified after bounded retries",
        )
