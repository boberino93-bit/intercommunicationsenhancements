from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

GENESIS_HASH = "0" * 64
CLAIM_SCHEMA = "org-agent-mesh/scheduler-mutation-claim/v1"
EVENT_SCHEMA = "org-agent-mesh/scheduler-mutation-event/v3"


class MutationJournalError(ValueError):
    pass


def _canonical_bytes(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _hash_without(value: dict, field: str) -> str:
    body = dict(value)
    body.pop(field, None)
    return hashlib.sha256(_canonical_bytes(body)).hexdigest()


def seal_claim(claim: dict) -> dict:
    value = dict(claim)
    value["schema"] = CLAIM_SCHEMA
    value.pop("claim_hash", None)
    value["claim_hash"] = _hash_without(value, "claim_hash")
    return value


def seal_event(event: dict) -> dict:
    value = dict(event)
    value["schema"] = EVENT_SCHEMA
    value.pop("event_hash", None)
    value["event_hash"] = _hash_without(value, "event_hash")
    return value


@dataclass(frozen=True)
class MutationJournalValidation:
    valid: bool
    event_count: int
    terminal_hash: str
    next_sequence: int


def validate_journal(*, claims: list[dict], events: list[dict]) -> MutationJournalValidation:
    """Validate one immutable claim and one immutable event for every sequence.

    The storage layer must enforce claim creation with create-if-absent semantics at a
    deterministic sequence path. Two writers racing for the same next sequence cannot
    both acquire that path; a stale claim without a matching event intentionally blocks
    automatic mutation until reconciled rather than being silently stolen.
    """
    claim_by_sequence: dict[int, dict] = {}
    event_by_sequence: dict[int, dict] = {}

    for claim in claims:
        sequence = claim.get("sequence")
        if not isinstance(sequence, int) or sequence < 1:
            raise MutationJournalError("claim sequence must be a positive integer")
        if sequence in claim_by_sequence:
            raise MutationJournalError("multiple claims for one mutation sequence")
        claim_by_sequence[sequence] = claim

    for event in events:
        sequence = event.get("sequence")
        if not isinstance(sequence, int) or sequence < 1:
            raise MutationJournalError("event sequence must be a positive integer")
        if sequence in event_by_sequence:
            raise MutationJournalError("multiple events for one mutation sequence")
        event_by_sequence[sequence] = event

    if set(claim_by_sequence) != set(event_by_sequence):
        raise MutationJournalError("claim/event sequence sets differ; journal is incomplete or forked")

    previous_hash = GENESIS_HASH
    expected = 1
    seen_event_ids: set[str] = set()
    for sequence in sorted(event_by_sequence):
        if sequence != expected:
            raise MutationJournalError("mutation journal sequence discontinuity")
        claim = claim_by_sequence[sequence]
        event = event_by_sequence[sequence]
        if claim.get("schema") != CLAIM_SCHEMA:
            raise MutationJournalError("unexpected mutation claim schema")
        if event.get("schema") != EVENT_SCHEMA:
            raise MutationJournalError("unexpected mutation event schema")
        event_id = event.get("event_id")
        if not isinstance(event_id, str) or not event_id:
            raise MutationJournalError("mutation event_id is required")
        if event_id in seen_event_ids:
            raise MutationJournalError("duplicate mutation event_id")
        seen_event_ids.add(event_id)
        if claim.get("event_id") != event_id:
            raise MutationJournalError("claim/event id mismatch")
        if claim.get("previous_event_hash") != previous_hash:
            raise MutationJournalError("claim previous-event hash discontinuity")
        if event.get("previous_event_hash") != previous_hash:
            raise MutationJournalError("event previous-event hash discontinuity")
        claimed_claim_hash = claim.get("claim_hash")
        if claimed_claim_hash != _hash_without(claim, "claim_hash"):
            raise MutationJournalError("mutation claim hash mismatch")
        if event.get("claim_hash") != claimed_claim_hash:
            raise MutationJournalError("event does not bind to acquired mutation claim")
        claimed_event_hash = event.get("event_hash")
        if claimed_event_hash != _hash_without(event, "event_hash"):
            raise MutationJournalError("mutation event hash mismatch")
        previous_hash = claimed_event_hash
        expected += 1

    return MutationJournalValidation(
        valid=True,
        event_count=len(event_by_sequence),
        terminal_hash=previous_hash,
        next_sequence=expected,
    )
