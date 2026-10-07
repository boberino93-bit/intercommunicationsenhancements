from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

GENESIS_HASH = "0" * 64
LEDGER_SCHEMA = "org-agent-mesh/scheduler-mutation-ledger-event/v2"


class MutationLedgerError(ValueError):
    pass


def _canonical_bytes(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_event_hash(event_without_hash: dict) -> str:
    return hashlib.sha256(_canonical_bytes(event_without_hash)).hexdigest()


def seal_event(event: dict, *, sequence: int, previous_event_hash: str) -> dict:
    if not isinstance(sequence, int) or sequence < 1:
        raise MutationLedgerError("sequence must be a positive integer")
    if len(previous_event_hash) != 64:
        raise MutationLedgerError("previous_event_hash must be a SHA-256 hex digest")
    sealed = dict(event)
    sealed["schema"] = LEDGER_SCHEMA
    sealed["sequence"] = sequence
    sealed["previous_event_hash"] = previous_event_hash
    sealed.pop("event_hash", None)
    sealed["event_hash"] = compute_event_hash(sealed)
    return sealed


@dataclass(frozen=True)
class LedgerValidation:
    valid: bool
    event_count: int
    terminal_hash: str


def validate_ledger(events: list[dict] | tuple[dict, ...]) -> LedgerValidation:
    previous = GENESIS_HASH
    expected_sequence = 1
    seen_event_ids: set[str] = set()

    for event in events:
        if event.get("schema") != LEDGER_SCHEMA:
            raise MutationLedgerError("unexpected mutation ledger schema")
        if event.get("sequence") != expected_sequence:
            raise MutationLedgerError("mutation ledger sequence discontinuity")
        event_id = event.get("event_id")
        if not isinstance(event_id, str) or not event_id:
            raise MutationLedgerError("mutation ledger event_id is required")
        if event_id in seen_event_ids:
            raise MutationLedgerError("duplicate mutation ledger event_id")
        seen_event_ids.add(event_id)
        if event.get("previous_event_hash") != previous:
            raise MutationLedgerError("mutation ledger hash-chain discontinuity")
        claimed = event.get("event_hash")
        if not isinstance(claimed, str) or len(claimed) != 64:
            raise MutationLedgerError("mutation ledger event_hash is invalid")
        body = dict(event)
        body.pop("event_hash")
        actual = compute_event_hash(body)
        if claimed != actual:
            raise MutationLedgerError("mutation ledger event hash mismatch")
        previous = claimed
        expected_sequence += 1

    return LedgerValidation(valid=True, event_count=len(events), terminal_hash=previous)


def parse_jsonl(text: str) -> list[dict]:
    events: list[dict] = []
    for index, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise MutationLedgerError(f"invalid JSON on ledger line {index}") from exc
        if not isinstance(value, dict):
            raise MutationLedgerError(f"ledger line {index} must contain an object")
        events.append(value)
    return events
