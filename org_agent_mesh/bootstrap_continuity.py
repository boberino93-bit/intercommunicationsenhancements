from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import uuid
from typing import Iterable, Mapping, Sequence, Any

OPEN_NAME_PROMPT = "What is your name?"
CLAIM_STATUS = "CLAIMED_NOT_AUTHENTICATED"
NO_AUTHORITY = "NONE"


class ContinuityRestorationError(ValueError):
    pass


def _utc_iso(now: datetime | None = None) -> str:
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ContinuityRestorationError("timezone_required")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class RestorationAttestation:
    project_id: str
    result: str
    loaded_source_ids: tuple[str, ...]
    missing_required_source_ids: tuple[str, ...]
    conflict_source_ids: tuple[str, ...]
    orientation_present: bool
    native_memory_used: bool
    authority: str
    mutation_authority: bool
    created_at_utc: str


def restore_project_continuity(
    project_id: str,
    external_records: Sequence[Mapping[str, Any]],
    *,
    required_source_ids: Iterable[str] = (),
    orientation_context: Mapping[str, Any] | None = None,
    now: datetime | None = None,
) -> RestorationAttestation:
    if not isinstance(project_id, str) or not project_id.strip():
        raise ContinuityRestorationError("project_id_required")

    required = tuple(dict.fromkeys(str(item) for item in required_source_ids))
    loaded: list[str] = []
    conflicts: list[str] = []

    for record in external_records:
        source_id = str(record.get("source_id") or "")
        record_project = str(record.get("project_id") or "")
        source_class = str(record.get("source_class") or "")
        if not source_id:
            raise ContinuityRestorationError("source_id_required")
        if source_class not in {
            "EXTERNAL_CANONICAL",
            "EXTERNAL_CORROBORATING",
            "EXTERNAL_ORIENTATION",
        }:
            raise ContinuityRestorationError("native_or_unknown_memory_source_denied")
        if record_project != project_id:
            conflicts.append(source_id)
            continue
        loaded.append(source_id)

    missing = tuple(item for item in required if item not in loaded)

    if conflicts:
        result = "IDENTITY_CONFLICT"
    elif missing:
        result = "CANONICAL_SOURCE_MISSING"
    elif required and all(item in loaded for item in required):
        result = "RESTORED_VERIFIED"
    elif loaded:
        result = "RESTORED_PARTIAL"
    elif orientation_context:
        result = "ORIENTATION_ONLY"
    else:
        result = "CANONICAL_SOURCE_MISSING"

    return RestorationAttestation(
        project_id=project_id,
        result=result,
        loaded_source_ids=tuple(loaded),
        missing_required_source_ids=missing,
        conflict_source_ids=tuple(conflicts),
        orientation_present=bool(orientation_context),
        native_memory_used=False,
        authority=NO_AUTHORITY,
        mutation_authority=False,
        created_at_utc=_utc_iso(now),
    )


@dataclass(frozen=True)
class SpeakerClaim:
    claimed_name: str
    status: str
    reason: str
    claimed_at_utc: str
    authority: str
    authentication_effect: str
    authorization_effect: str


class SpeakerClaimAuditTable:
    """Append-only, hash-chained JSONL speaker-claim history.

    The active speaker claim is intentionally not stored here as authority.
    This table is evidentiary/audit context only.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _read_last_hash(self) -> str | None:
        if not self.path.exists():
            return None
        last = None
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    last = json.loads(line)
        return None if last is None else str(last["event_hash"])

    def append(
        self,
        *,
        project_id: str,
        session_id: str,
        claimed_name: str,
        reason: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        name = str(claimed_name).strip()
        if not name:
            raise ValueError("claimed_name_required")
        if not project_id or not session_id:
            raise ValueError("project_id_and_session_id_required")

        previous_hash = self._read_last_hash()
        event = {
            "event_id": f"speaker-{uuid.uuid4().hex}",
            "project_id": str(project_id),
            "session_id": str(session_id),
            "timestamp_utc": _utc_iso(now),
            "claimed_name": name,
            "claim_status": CLAIM_STATUS,
            "reason": str(reason),
            "voice_signal_is_identity_proof": False,
            "authentication_effect": "NONE",
            "authorization_effect": "NONE",
            "mutation_authority": False,
            "previous_event_hash": previous_hash,
        }
        canonical = json.dumps(event, sort_keys=True, separators=(",", ":")).encode("utf-8")
        event["event_hash"] = hashlib.sha256(canonical).hexdigest()

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
        return event


class SpeakerIdentitySession:
    """Mutable active speaker binding; immutable audit history lives separately."""

    def __init__(self) -> None:
        self.active_claim: SpeakerClaim | None = None
        self._pending_reason = "STARTUP"

    @property
    def prompt(self) -> str:
        return OPEN_NAME_PROMPT

    def startup_prompt(self) -> str:
        self.active_claim = None
        self._pending_reason = "STARTUP"
        return OPEN_NAME_PROMPT

    def signal_possible_speaker_change(
        self,
        *,
        vocal_modulation_changed: bool = False,
        speaker_change_suspected: bool = False,
    ) -> str | None:
        if not (vocal_modulation_changed or speaker_change_suspected):
            return None
        self.active_claim = None
        if vocal_modulation_changed and speaker_change_suspected:
            self._pending_reason = "VOCAL_MODULATION_OR_SPEAKER_CHANGE"
        elif vocal_modulation_changed:
            self._pending_reason = "VOCAL_MODULATION_CHANGE"
        else:
            self._pending_reason = "SPEAKER_CHANGE_SUSPECTED"
        return OPEN_NAME_PROMPT

    def bind_claim(
        self,
        claimed_name: str,
        *,
        project_id: str,
        session_id: str,
        audit_table: SpeakerClaimAuditTable,
        now: datetime | None = None,
    ) -> SpeakerClaim:
        name = str(claimed_name).strip()
        if not name:
            raise ValueError("claimed_name_required")
        timestamp = _utc_iso(now)
        reason = self._pending_reason
        audit_table.append(
            project_id=project_id,
            session_id=session_id,
            claimed_name=name,
            reason=reason,
            now=now,
        )
        claim = SpeakerClaim(
            claimed_name=name,
            status=CLAIM_STATUS,
            reason=reason,
            claimed_at_utc=timestamp,
            authority=NO_AUTHORITY,
            authentication_effect="NONE",
            authorization_effect="NONE",
        )
        self.active_claim = claim
        self._pending_reason = "MANUAL_REBIND"
        return claim
