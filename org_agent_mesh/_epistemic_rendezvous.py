from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ._epistemic_base import EpistemicError, PeerDisposition, ResearchMode


@dataclass(frozen=True)
class FirstPassSubmission:
    lane_id: str; mode: ResearchMode; result_digest: str; claim_refs: tuple[str,...]; evidence_refs: tuple[str,...]; submitted_at: str


class BlindedRendezvous:
    def __init__(self, rendezvous_id: str, required_lanes: Sequence[str], threshold: int | None=None):
        if not required_lanes: raise EpistemicError("required lanes missing")
        self.rendezvous_id=rendezvous_id; self.required_lanes=tuple(dict.fromkeys(required_lanes)); self.threshold=threshold or len(self.required_lanes)
        self._sealed: dict[str, FirstPassSubmission]={}; self.opened=False; self.peer_reviews: list[tuple[str,str,PeerDisposition]]=[]
    def submit(self, submission: FirstPassSubmission):
        if self.opened: raise EpistemicError("first pass already closed")
        if submission.lane_id not in self.required_lanes: raise EpistemicError("lane not assigned")
        prior=self._sealed.get(submission.lane_id)
        if prior and prior != submission: raise EpistemicError("sealed first pass is immutable")
        self._sealed[submission.lane_id]=submission
        return "IDEMPOTENT" if prior else "SEALED"
    def peer_material(self, lane_id: str):
        if not self.opened: return ()
        return tuple(v for k,v in self._sealed.items() if k != lane_id)
    def open(self, *, force_timeout: bool=False):
        if len(self._sealed) < self.threshold and not force_timeout: raise EpistemicError("rendezvous threshold not met")
        self.opened=True; return tuple(self._sealed.values())
    def classify_peer(self, reviewer_lane: str, target_lane: str, disposition: PeerDisposition):
        if not self.opened: raise EpistemicError("rendezvous not open")
        if reviewer_lane == target_lane: raise EpistemicError("self review not allowed")
        self.peer_reviews.append((reviewer_lane,target_lane,disposition))


