from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import json
import re
from typing import Iterable


SCHEMA = "intercommunications/swarm-stage-checkpoint/v1"
CHECKPOINT_ISSUE_REPOSITORY = "boberino93-bit/intercommunicationsenhancements"
CHECKPOINT_ISSUE_NUMBER = 25

STAGES = ("RESEARCHER_1", "MANAGER", "PRIMARY")
STAGE_STATES = {
    "RESEARCHER_1": {"RESEARCH_PROGRESS", "RESEARCH_HANDOFF_READY"},
    "MANAGER": {"MANAGER_PROGRESS", "MANAGER_HANDOFF_READY"},
    "PRIMARY": {"PRIMARY_PROGRESS", "PRIMARY_PROPOSAL_READY"},
}
COMMON_STATES = {
    "CHECKPOINT_IO_BLOCKED",
    "UPSTREAM_NOT_READY",
    "INTENTIONAL_STOP",
    "INTEGRITY_QUARANTINE",
}
TRIGGERS = ("SCHEDULED", "USER_INTERACTIVE", "RECOVERY", "RETRY")
_CYCLE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:00:00[+-]\d{2}:\d{2}$")


class CheckpointError(ValueError):
    pass


class CheckpointConflictError(CheckpointError):
    pass


def _unique_tuple(values: Iterable[str] | None, *, field_name: str) -> tuple[str, ...]:
    items = tuple(values or ())
    if any(not isinstance(item, str) or not item.strip() for item in items):
        raise CheckpointError(f"{field_name} entries must be non-empty strings")
    if len(items) != len(set(items)):
        raise CheckpointError(f"{field_name} entries must be unique")
    return items


def cycle_id_from_time(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise CheckpointError("cycle time must be offset-aware")
    floored = value.replace(minute=0, second=0, microsecond=0)
    return floored.isoformat(timespec="seconds")


@dataclass(frozen=True)
class StageCheckpoint:
    checkpoint_id: str
    cycle_id: str
    stage: str
    run_id: str
    sequence: int
    state: str
    phase: str
    trigger: str
    created_at: str
    source_revisions: dict[str, str] = field(default_factory=dict)
    upstream_checkpoint_ids: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    summary: str = ""
    blockers: tuple[str, ...] = ()
    unfinished_work: tuple[str, ...] = ()
    next_action: str = ""
    recovery_of_cycle_id: str | None = None

    def __post_init__(self):
        if not isinstance(self.checkpoint_id, str) or not self.checkpoint_id.strip():
            raise CheckpointError("checkpoint_id is required")
        if not isinstance(self.cycle_id, str) or not _CYCLE_RE.fullmatch(self.cycle_id):
            raise CheckpointError("cycle_id must be an offset-aware local hour floor")
        if self.stage not in STAGES:
            raise CheckpointError("unsupported stage")
        if not isinstance(self.run_id, str) or not self.run_id.strip():
            raise CheckpointError("run_id is required")
        if not isinstance(self.sequence, int) or self.sequence < 0:
            raise CheckpointError("sequence must be a non-negative integer")
        allowed_states = STAGE_STATES[self.stage] | COMMON_STATES
        if self.state not in allowed_states:
            raise CheckpointError(f"state {self.state!r} is not valid for stage {self.stage}")
        if not isinstance(self.phase, str) or not self.phase.strip():
            raise CheckpointError("phase is required")
        if self.trigger not in TRIGGERS:
            raise CheckpointError("unsupported trigger")
        try:
            created = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
        except (TypeError, ValueError) as exc:
            raise CheckpointError("created_at must be ISO-8601") from exc
        if created.tzinfo is None or created.utcoffset() is None:
            raise CheckpointError("created_at must be offset-aware")
        if not isinstance(self.source_revisions, dict):
            raise CheckpointError("source_revisions must be an object")
        for key, value in self.source_revisions.items():
            if not isinstance(key, str) or not key.strip() or not isinstance(value, str) or not value.strip():
                raise CheckpointError("source_revisions keys and values must be non-empty strings")
        object.__setattr__(self, "upstream_checkpoint_ids", _unique_tuple(self.upstream_checkpoint_ids, field_name="upstream_checkpoint_ids"))
        object.__setattr__(self, "evidence_refs", _unique_tuple(self.evidence_refs, field_name="evidence_refs"))
        object.__setattr__(self, "blockers", _unique_tuple(self.blockers, field_name="blockers"))
        object.__setattr__(self, "unfinished_work", _unique_tuple(self.unfinished_work, field_name="unfinished_work"))
        if not isinstance(self.summary, str):
            raise CheckpointError("summary must be a string")
        if not isinstance(self.next_action, str):
            raise CheckpointError("next_action must be a string")
        if self.trigger == "USER_INTERACTIVE" and not self.recovery_of_cycle_id:
            raise CheckpointError("interactive recovery checkpoints require recovery_of_cycle_id")
        if self.recovery_of_cycle_id is not None and not _CYCLE_RE.fullmatch(self.recovery_of_cycle_id):
            raise CheckpointError("recovery_of_cycle_id must be an offset-aware local hour floor")

    @property
    def stream_key(self) -> tuple[str, str, str]:
        return (self.cycle_id, self.stage, self.run_id)

    def as_dict(self) -> dict:
        payload = {
            "schema": SCHEMA,
            "checkpoint_id": self.checkpoint_id,
            "cycle_id": self.cycle_id,
            "stage": self.stage,
            "run_id": self.run_id,
            "sequence": self.sequence,
            "state": self.state,
            "phase": self.phase,
            "trigger": self.trigger,
            "created_at": self.created_at,
            "source_revisions": dict(self.source_revisions),
            "upstream_checkpoint_ids": list(self.upstream_checkpoint_ids),
            "evidence_refs": list(self.evidence_refs),
            "summary": self.summary,
            "blockers": list(self.blockers),
            "unfinished_work": list(self.unfinished_work),
            "next_action": self.next_action,
        }
        if self.recovery_of_cycle_id is not None:
            payload["recovery_of_cycle_id"] = self.recovery_of_cycle_id
        return payload

    def canonical_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def render_issue_comment(self) -> str:
        return "SWARM_STAGE_CHECKPOINT\n```json\n" + json.dumps(self.as_dict(), sort_keys=True, indent=2) + "\n```"

    @classmethod
    def from_dict(cls, payload: dict) -> "StageCheckpoint":
        if not isinstance(payload, dict):
            raise CheckpointError("checkpoint payload must be an object")
        if payload.get("schema") != SCHEMA:
            raise CheckpointError("unsupported checkpoint schema")
        return cls(
            checkpoint_id=payload.get("checkpoint_id"),
            cycle_id=payload.get("cycle_id"),
            stage=payload.get("stage"),
            run_id=payload.get("run_id"),
            sequence=payload.get("sequence"),
            state=payload.get("state"),
            phase=payload.get("phase"),
            trigger=payload.get("trigger"),
            created_at=payload.get("created_at"),
            source_revisions=payload.get("source_revisions") or {},
            upstream_checkpoint_ids=tuple(payload.get("upstream_checkpoint_ids") or ()),
            evidence_refs=tuple(payload.get("evidence_refs") or ()),
            summary=payload.get("summary") or "",
            blockers=tuple(payload.get("blockers") or ()),
            unfinished_work=tuple(payload.get("unfinished_work") or ()),
            next_action=payload.get("next_action") or "",
            recovery_of_cycle_id=payload.get("recovery_of_cycle_id"),
        )


def validate_no_sequence_conflicts(checkpoints: Iterable[StageCheckpoint]) -> bool:
    seen: dict[tuple[str, str, str, int], str] = {}
    for checkpoint in checkpoints:
        key = (*checkpoint.stream_key, checkpoint.sequence)
        previous = seen.get(key)
        if previous is not None and previous != checkpoint.canonical_json():
            raise CheckpointConflictError(
                f"conflicting checkpoint reuse for cycle/stage/run/sequence {key}"
            )
        seen[key] = checkpoint.canonical_json()
    return True


def latest_for_cycle(
    checkpoints: Iterable[StageCheckpoint],
    *,
    cycle_id: str,
    stage: str,
    accepted_states: set[str] | None = None,
) -> StageCheckpoint | None:
    if stage not in STAGES:
        raise CheckpointError("unsupported stage")
    if not _CYCLE_RE.fullmatch(cycle_id):
        raise CheckpointError("invalid cycle_id")
    items = list(checkpoints)
    validate_no_sequence_conflicts(items)
    candidates = [
        cp
        for cp in items
        if cp.cycle_id == cycle_id
        and cp.stage == stage
        and (accepted_states is None or cp.state in accepted_states)
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda cp: (cp.sequence, cp.created_at, cp.checkpoint_id))


def accepted_upstream_states(downstream_stage: str) -> tuple[str, set[str]]:
    if downstream_stage == "MANAGER":
        return "RESEARCHER_1", {"RESEARCH_PROGRESS", "RESEARCH_HANDOFF_READY"}
    if downstream_stage == "PRIMARY":
        return "MANAGER", {"MANAGER_PROGRESS", "MANAGER_HANDOFF_READY"}
    raise CheckpointError("Researcher has no scheduled upstream stage in this serial pipeline")
