from __future__ import annotations

from dataclasses import dataclass

class HandoffError(ValueError):
    pass

@dataclass(frozen=True)
class WarmHandoff:
    handoff_id: str
    outgoing_agent_id: str
    outgoing_session_id: str
    project_id: str
    role: str
    work_unit: str
    checkpoint_ref: str
    persistence_state: str
    protocol_version: str
    computational_state: str
    next_action: str
    lease_id: str | None = None
    ownership_epoch: int | None = None
    fence_digest: str | None = None
    unresolved_questions: tuple[str, ...] = ()
    known_risks: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    explicitly_not_authorized: tuple[str, ...] = ()
    authority_conveyed: bool = False

    def __post_init__(self) -> None:
        for name in ("handoff_id", "outgoing_agent_id", "outgoing_session_id", "project_id", "role", "work_unit", "checkpoint_ref", "persistence_state", "protocol_version", "computational_state", "next_action"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise HandoffError(f"{name} is required")
        if self.ownership_epoch is not None and self.ownership_epoch < 0:
            raise HandoffError("ownership_epoch must be non-negative")
        if self.authority_conveyed is not False:
            raise HandoffError("handoff cannot convey authority")

    def successor_may_continue(self, *, accepted_project_id: str, accepted_work_unit: str, canonical_ownership_acquired: bool) -> bool:
        if accepted_project_id != self.project_id or accepted_work_unit != self.work_unit:
            raise HandoffError("HANDOFF_BINDING_MISMATCH")
        if not canonical_ownership_acquired:
            raise HandoffError("HANDOFF_DOES_NOT_TRANSFER_OWNERSHIP")
        return True
