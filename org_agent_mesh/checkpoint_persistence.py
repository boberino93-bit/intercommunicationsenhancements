from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable

from .checkpoint_bus import StageCheckpoint
from .dual_persistence import DualPersistenceReceipt, PersistenceBarrierError

READY_STATES = frozenset({"RESEARCH_HANDOFF_READY", "MANAGER_HANDOFF_READY", "PRIMARY_PROPOSAL_READY"})


class CheckpointPersistenceError(ValueError):
    pass


def checkpoint_digest(checkpoint: StageCheckpoint) -> str:
    return "sha256:" + sha256(checkpoint.canonical_json().encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PersistedCheckpoint:
    checkpoint: StageCheckpoint
    receipt: DualPersistenceReceipt

    def __post_init__(self) -> None:
        if self.receipt.project_id != self.checkpoint.project_id:
            raise CheckpointPersistenceError("PERSISTENCE_PROJECT_MISMATCH")
        if self.receipt.record_id != self.checkpoint.checkpoint_id:
            raise CheckpointPersistenceError("PERSISTENCE_RECORD_ID_MISMATCH")
        if self.receipt.content_digest != checkpoint_digest(self.checkpoint):
            raise CheckpointPersistenceError("PERSISTENCE_CONTENT_DIGEST_MISMATCH")

    def require_ready(self) -> bool:
        if self.checkpoint.state not in READY_STATES:
            raise CheckpointPersistenceError("CHECKPOINT_NOT_READY_STATE")
        try:
            self.receipt.require_confirmed_binding(
                project_id=self.checkpoint.project_id,
                record_id=self.checkpoint.checkpoint_id,
                content_digest=checkpoint_digest(self.checkpoint),
            )
        except PersistenceBarrierError as exc:
            raise CheckpointPersistenceError(str(exc)) from exc
        return True


def latest_persisted_ready_for_cycle(
    checkpoints: Iterable[PersistedCheckpoint],
    *,
    project_id: str,
    cycle_id: str,
    stage: str,
) -> PersistedCheckpoint | None:
    candidates: list[PersistedCheckpoint] = []
    for item in checkpoints:
        cp = item.checkpoint
        if cp.project_id != project_id or cp.cycle_id != cycle_id or cp.stage != stage:
            continue
        if cp.state not in READY_STATES:
            continue
        try:
            item.require_ready()
        except CheckpointPersistenceError:
            continue
        candidates.append(item)
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item.checkpoint.sequence, item.checkpoint.created_at, item.checkpoint.checkpoint_id))
