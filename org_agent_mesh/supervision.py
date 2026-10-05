from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import Callable, Optional
import time
import uuid

from .project_scope import require_project_id, require_resource_id


class AgentControlState(str, Enum):
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    REDIRECT_REQUESTED = "REDIRECT_REQUESTED"
    PAUSE_REQUESTED = "PAUSE_REQUESTED"
    PAUSED = "PAUSED"
    STOP_REQUESTED = "STOP_REQUESTED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SupervisoryAction(str, Enum):
    CONTINUE = "CONTINUE"
    REDIRECT = "REDIRECT"
    PAUSE = "PAUSE"
    STOP = "STOP"
    STOP_TREE = "STOP_TREE"


class ReasonCode(str, Enum):
    GOAL_MISALIGNMENT = "GOAL_MISALIGNMENT"
    INSTRUCTION_DRIFT = "INSTRUCTION_DRIFT"
    SCOPE_CREEP = "SCOPE_CREEP"
    REDUNDANT_WORK = "REDUNDANT_WORK"
    LOW_INFORMATION_GAIN = "LOW_INFORMATION_GAIN"
    CIRCULAR_WORK = "CIRCULAR_WORK"
    INVALID_ASSUMPTIONS = "INVALID_ASSUMPTIONS"
    SUPERSEDED = "SUPERSEDED"
    POOR_METHODOLOGY = "POOR_METHODOLOGY"
    EVIDENCE_QUALITY = "EVIDENCE_QUALITY"
    PROJECT_GOAL_CONFLICT = "PROJECT_GOAL_CONFLICT"
    ARCHITECTURE_CONFLICT = "ARCHITECTURE_CONFLICT"
    UNEXPECTED_RISK = "UNEXPECTED_RISK"
    DESTRUCTIVE_BEHAVIOR = "DESTRUCTIVE_BEHAVIOR"
    RESOURCE_IMBALANCE = "RESOURCE_IMBALANCE"
    BLOCKED_EXECUTION = "BLOCKED_EXECUTION"
    AGENT_CONFLICT = "AGENT_CONFLICT"
    PREMATURE_IMPLEMENTATION = "PREMATURE_IMPLEMENTATION"
    PREMATURE_RESEARCH = "PREMATURE_RESEARCH"
    QUALITY_DEGRADATION = "QUALITY_DEGRADATION"
    PROJECT_STATE_CHANGED = "PROJECT_STATE_CHANGED"
    USER_OVERRIDE = "USER_OVERRIDE"
    MASTER_DIRECTION = "MASTER_DIRECTION"
    OTHER = "OTHER"


TERMINAL_STATES = {
    AgentControlState.STOPPED,
    AgentControlState.COMPLETED,
    AgentControlState.FAILED,
}
PRIMARY_TYPES = {"primary", "project-primary", "project_manager"}


class AuthorityError(PermissionError):
    pass


class AgentRegistrationError(ValueError):
    pass


@dataclass
class AgentRecord:
    agent_id: str
    agent_type: str
    project_id: Optional[str] = None
    parent_agent_id: Optional[str] = None
    state: AgentControlState = AgentControlState.STARTING
    children: set[str] = field(default_factory=set)
    task_id: Optional[str] = None
    task_summary: str = ""
    allow_respawn: bool = True
    assignment_revision: int = 0
    redirect_instruction: Optional[str] = None
    roaming: bool = False
    chat_project: Optional[str] = None
    preserved_state: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.agent_id = require_resource_id(self.agent_id, field="agent_id")
        if not isinstance(self.agent_type, str) or not self.agent_type.strip():
            raise AgentRegistrationError("agent_type is required")
        self.agent_type = self.agent_type.strip().lower()
        if self.project_id is not None:
            self.project_id = require_project_id(self.project_id)
        if self.parent_agent_id is not None:
            self.parent_agent_id = require_resource_id(
                self.parent_agent_id, field="parent_agent_id"
            )
        if self.task_id is not None:
            self.task_id = require_resource_id(self.task_id, field="task_id")
        if self.agent_type == "master" and not self.roaming:
            raise AgentRegistrationError("master agent must be roaming")
        if self.roaming and self.project_id is not None:
            raise AgentRegistrationError("roaming agent cannot be project-bound")
        if self.roaming and self.chat_project is not None:
            raise AgentRegistrationError("roaming agent cannot have a ChatGPT Project")


@dataclass(frozen=True)
class SupervisorIdentity:
    supervisor_id: str
    supervisor_type: str
    project_id: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "supervisor_id", require_resource_id(self.supervisor_id, field="supervisor_id")
        )
        if not isinstance(self.supervisor_type, str) or not self.supervisor_type.strip():
            raise AuthorityError("supervisor_type is required")
        object.__setattr__(self, "supervisor_type", self.supervisor_type.strip().lower())
        if self.project_id is not None:
            object.__setattr__(self, "project_id", require_project_id(self.project_id))


@dataclass(frozen=True)
class SupervisoryDecision:
    decision_id: str
    supervisor_id: str
    target_id: str
    action: SupervisoryAction
    reason_code: ReasonCode
    explanation: str
    timestamp: float = field(default_factory=time.time)


class AgentRegistry:
    """Machine-readable project/agent tree and intentional-stop state."""

    def __init__(self) -> None:
        self.agents: dict[str, AgentRecord] = {}
        self.decisions: list[SupervisoryDecision] = []
        self._lock = RLock()

    def register(self, record: AgentRecord) -> AgentRecord:
        with self._lock:
            if record.agent_id in self.agents:
                raise AgentRegistrationError(f"duplicate agent_id: {record.agent_id}")
            if record.parent_agent_id:
                parent = self.agents.get(record.parent_agent_id)
                if parent is None:
                    raise AgentRegistrationError("parent agent is not registered")
                if parent.state in {
                    AgentControlState.STOP_REQUESTED,
                    AgentControlState.STOPPING,
                    AgentControlState.STOPPED,
                } or not parent.allow_respawn:
                    raise AgentRegistrationError("parent is under intentional stop; child spawn denied")
                if (
                    parent.project_id is not None
                    and record.project_id is not None
                    and parent.project_id != record.project_id
                ):
                    raise AgentRegistrationError("child project differs from parent project")
                parent.children.add(record.agent_id)
            self.agents[record.agent_id] = record
            return record

    def get(self, agent_id: str) -> AgentRecord:
        return self.agents[require_resource_id(agent_id, field="agent_id")]

    def children_of(self, agent_id: str) -> list[AgentRecord]:
        agent = self.get(agent_id)
        return [self.agents[c] for c in sorted(agent.children) if c in self.agents]

    def checkpoint(self, agent_id: str, **state) -> None:
        with self._lock:
            self.get(agent_id).preserved_state.update(state)


class AuthorityService:
    """Lifecycle supervision authority only; source mutation remains capability/project gated."""

    def can_control(
        self, supervisor: SupervisorIdentity, target: AgentRecord
    ) -> bool:
        if supervisor.supervisor_id == target.agent_id:
            return False
        if supervisor.supervisor_type == "user":
            return True
        if supervisor.supervisor_type == "master":
            return True
        if supervisor.supervisor_type in PRIMARY_TYPES:
            return (
                supervisor.project_id is not None
                and target.project_id is not None
                and supervisor.project_id == target.project_id
                and target.agent_type != "master"
            )
        return False

    def require_control_authority(
        self, supervisor: SupervisorIdentity, target: AgentRecord
    ) -> None:
        if not self.can_control(supervisor, target):
            raise AuthorityError(
                f"{supervisor.supervisor_id} does not have lifecycle authority over {target.agent_id}"
            )


class Supervisor:
    def __init__(self, registry: AgentRegistry, authority: AuthorityService | None = None):
        self.registry = registry
        self.authority = authority or AuthorityService()

    def act(
        self,
        supervisor: SupervisorIdentity,
        target_id: str,
        action: SupervisoryAction,
        reason_code: ReasonCode,
        explanation: str,
        redirect_instruction: Optional[str] = None,
    ) -> SupervisoryDecision:
        target = self.registry.get(target_id)
        self.authority.require_control_authority(supervisor, target)

        if not isinstance(explanation, str) or not explanation.strip():
            raise ValueError("supervisory explanation is required")
        if action == SupervisoryAction.REDIRECT and not (
            isinstance(redirect_instruction, str) and redirect_instruction.strip()
        ):
            raise ValueError("REDIRECT requires redirect_instruction")

        decision = SupervisoryDecision(
            decision_id=str(uuid.uuid4()),
            supervisor_id=supervisor.supervisor_id,
            target_id=target.agent_id,
            action=action,
            reason_code=reason_code,
            explanation=explanation.strip(),
        )
        self.registry.decisions.append(decision)

        if action == SupervisoryAction.CONTINUE:
            if target.state in {AgentControlState.PAUSE_REQUESTED, AgentControlState.PAUSED}:
                target.state = AgentControlState.RUNNING
            return decision
        if action == SupervisoryAction.REDIRECT:
            target.redirect_instruction = redirect_instruction.strip()
            target.assignment_revision += 1
            target.state = AgentControlState.REDIRECT_REQUESTED
            return decision
        if action == SupervisoryAction.PAUSE:
            if target.state not in TERMINAL_STATES:
                target.state = AgentControlState.PAUSE_REQUESTED
            return decision
        if action == SupervisoryAction.STOP:
            self._mark_stop(target)
            return decision
        if action == SupervisoryAction.STOP_TREE:
            self._stop_tree(target.agent_id)
            return decision
        raise ValueError(f"unsupported action: {action}")

    @staticmethod
    def _mark_stop(target: AgentRecord) -> None:
        target.allow_respawn = False
        if target.state not in TERMINAL_STATES:
            target.state = AgentControlState.STOP_REQUESTED

    def _stop_tree(self, agent_id: str) -> None:
        target = self.registry.get(agent_id)
        self._mark_stop(target)
        for child in self.registry.children_of(agent_id):
            self._stop_tree(child.agent_id)


class CooperativeAgentRuntime:
    """Base runtime that checks authoritative control state between bounded work units."""

    def __init__(
        self,
        record: AgentRecord,
        *,
        perform_next_bounded_unit: Callable[[], None],
        has_more_work: Callable[[], bool],
        persist_partial_state: Callable[[], Optional[dict]],
        reconfigure_task: Callable[[str], None],
        release_resources: Callable[[], None] | None = None,
        pause_poll_seconds: float = 0.05,
    ):
        self.record = record
        self._perform_next_bounded_unit = perform_next_bounded_unit
        self._has_more_work = has_more_work
        self._persist_partial_state = persist_partial_state
        self._reconfigure_task = reconfigure_task
        self._release_resources = release_resources or (lambda: None)
        self._pause_poll_seconds = pause_poll_seconds

    def _preserve(self) -> None:
        snapshot = self._persist_partial_state()
        if isinstance(snapshot, dict):
            self.record.preserved_state.update(snapshot)

    def run(self) -> None:
        self.record.state = AgentControlState.RUNNING
        try:
            while self._has_more_work():
                state = self.record.state
                if state == AgentControlState.STOP_REQUESTED:
                    self.record.state = AgentControlState.STOPPING
                    self._preserve()
                    self._release_resources()
                    self.record.state = AgentControlState.STOPPED
                    return
                if state == AgentControlState.PAUSE_REQUESTED:
                    self._preserve()
                    self.record.state = AgentControlState.PAUSED
                    while self.record.state == AgentControlState.PAUSED:
                        time.sleep(self._pause_poll_seconds)
                    continue
                if state == AgentControlState.REDIRECT_REQUESTED:
                    instruction = self.record.redirect_instruction
                    self._preserve()
                    self._reconfigure_task(instruction or "")
                    self.record.redirect_instruction = None
                    self.record.state = AgentControlState.RUNNING
                    continue
                self._perform_next_bounded_unit()
            self.record.state = AgentControlState.COMPLETED
        except Exception:
            self._preserve()
            self.record.state = AgentControlState.FAILED
            raise


def may_spawn_replacement(
    previous: AgentRecord,
    *,
    new_task_revision: int,
    authorization_source: str | None = None,
) -> bool:
    """Prevent a timer/scheduler from blindly resurrecting intentionally stopped work."""
    if previous.allow_respawn:
        return True
    source = (authorization_source or "").strip().upper()
    if source == "USER":
        return True
    if source in {"MASTER", "PRIMARY"} and new_task_revision > previous.assignment_revision:
        return True
    return False
