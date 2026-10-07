from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json

UTC = timezone.utc
CLAIM_SCHEMA = "org-agent-mesh/scheduler-occurrence-claim/v1"


class OccurrenceClaimError(ValueError):
    pass


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise OccurrenceClaimError("timezone-aware datetime required")
    return value.astimezone(UTC)


def _parse(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise OccurrenceClaimError("invalid occurrence claim timestamp") from exc
    return _utc(parsed)


def _iso(value: datetime) -> str:
    return _utc(value).isoformat().replace("+00:00", "Z")


def _canonical_hash(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def occurrence_claim_key(occurrence_id: str) -> str:
    if not isinstance(occurrence_id, str) or not occurrence_id:
        raise OccurrenceClaimError("occurrence_id is required")
    return hashlib.sha256(occurrence_id.encode("utf-8")).hexdigest()


def occurrence_claim_path(occurrence_id: str) -> str:
    return f"scheduler-occurrence-claims/{occurrence_claim_key(occurrence_id)}.json"


@dataclass(frozen=True)
class OccurrenceClaim:
    schema: str
    claim_id: str
    occurrence_id: str
    job_id: str
    binding_id: str
    frontend_automation_id: str
    receipt_id: str
    scheduled_for: str
    claimed_at: str
    execution_surface: str
    authority_conveyed: bool
    mutation_authority_conveyed: bool
    claim_hash: str

    def as_dict(self) -> dict:
        return {
            "schema": self.schema,
            "claim_id": self.claim_id,
            "occurrence_id": self.occurrence_id,
            "job_id": self.job_id,
            "binding_id": self.binding_id,
            "frontend_automation_id": self.frontend_automation_id,
            "receipt_id": self.receipt_id,
            "scheduled_for": self.scheduled_for,
            "claimed_at": self.claimed_at,
            "execution_surface": self.execution_surface,
            "authority_conveyed": self.authority_conveyed,
            "mutation_authority_conveyed": self.mutation_authority_conveyed,
            "claim_hash": self.claim_hash,
        }


@dataclass(frozen=True)
class OccurrenceOwnershipDecision:
    may_enter_project_work: bool
    disposition: str
    reason: str


def make_occurrence_claim(
    *,
    occurrence_id: str,
    job_id: str,
    binding_id: str,
    frontend_automation_id: str,
    receipt_id: str,
    scheduled_for: datetime,
    claimed_at: datetime,
    maximum_claim_delay: timedelta = timedelta(minutes=30),
) -> OccurrenceClaim:
    scheduled = _utc(scheduled_for)
    claimed = _utc(claimed_at)
    expected_occurrence = f"{job_id}:{scheduled.strftime('%Y%m%dT%H%MZ')}"
    if occurrence_id != expected_occurrence:
        raise OccurrenceClaimError("occurrence_id does not match job and scheduled_for")
    if claimed < scheduled:
        raise OccurrenceClaimError("occurrence claim predates schedule")
    if claimed - scheduled > maximum_claim_delay:
        raise OccurrenceClaimError("occurrence claim exceeds maximum claim delay")
    for name, value in {
        "job_id": job_id,
        "binding_id": binding_id,
        "frontend_automation_id": frontend_automation_id,
        "receipt_id": receipt_id,
    }.items():
        if not isinstance(value, str) or not value:
            raise OccurrenceClaimError(f"{name} is required")

    claim_id = f"occurrence-claim-{hashlib.sha256((occurrence_id + '|' + receipt_id).encode('utf-8')).hexdigest()[:24]}"
    body = {
        "schema": CLAIM_SCHEMA,
        "claim_id": claim_id,
        "occurrence_id": occurrence_id,
        "job_id": job_id,
        "binding_id": binding_id,
        "frontend_automation_id": frontend_automation_id,
        "receipt_id": receipt_id,
        "scheduled_for": _iso(scheduled),
        "claimed_at": _iso(claimed),
        "execution_surface": "CHATGPT_FRONTEND_MAPPED",
        "authority_conveyed": False,
        "mutation_authority_conveyed": False,
    }
    return OccurrenceClaim(**body, claim_hash=_canonical_hash(body))


def claim_from_dict(value: dict) -> OccurrenceClaim:
    required = {
        "schema",
        "claim_id",
        "occurrence_id",
        "job_id",
        "binding_id",
        "frontend_automation_id",
        "receipt_id",
        "scheduled_for",
        "claimed_at",
        "execution_surface",
        "authority_conveyed",
        "mutation_authority_conveyed",
        "claim_hash",
    }
    if set(value) != required:
        raise OccurrenceClaimError("occurrence claim fields do not match closed schema")
    claim = OccurrenceClaim(**value)
    if claim.schema != CLAIM_SCHEMA:
        raise OccurrenceClaimError("unsupported occurrence claim schema")
    if claim.execution_surface != "CHATGPT_FRONTEND_MAPPED":
        raise OccurrenceClaimError("occurrence claim execution surface mismatch")
    if claim.authority_conveyed or claim.mutation_authority_conveyed:
        raise OccurrenceClaimError("occurrence claim may not convey authority")
    scheduled = _parse(claim.scheduled_for)
    claimed_at = _parse(claim.claimed_at)
    expected_occurrence = f"{claim.job_id}:{scheduled.strftime('%Y%m%dT%H%MZ')}"
    if claim.occurrence_id != expected_occurrence:
        raise OccurrenceClaimError("occurrence claim identity mismatch")
    if claimed_at < scheduled:
        raise OccurrenceClaimError("occurrence claim predates schedule")
    body = claim.as_dict()
    body.pop("claim_hash")
    if _canonical_hash(body) != claim.claim_hash:
        raise OccurrenceClaimError("occurrence claim hash mismatch")
    return claim


def decide_occurrence_ownership(
    *,
    proposed_claim: OccurrenceClaim,
    existing_claim: OccurrenceClaim | None,
) -> OccurrenceOwnershipDecision:
    """Decide whether one frontend invocation owns the bounded occurrence work unit.

    The storage layer is authoritative for acquisition: the deterministic path must be
    created with create-if-absent semantics. This function supports preflight/readback
    decisions and safe retry after an ambiguous create response.
    """
    if existing_claim is None:
        return OccurrenceOwnershipDecision(
            may_enter_project_work=False,
            disposition="CLAIM_CREATE_REQUIRED",
            reason="NO_EXISTING_OCCURRENCE_OWNER_CREATE_DETERMINISTIC_CLAIM_FIRST",
        )
    if existing_claim.occurrence_id != proposed_claim.occurrence_id:
        raise OccurrenceClaimError("deterministic claim path contains wrong occurrence")
    if existing_claim.claim_id == proposed_claim.claim_id and existing_claim.claim_hash == proposed_claim.claim_hash:
        return OccurrenceOwnershipDecision(
            may_enter_project_work=True,
            disposition="CLAIM_OWNED_BY_THIS_INVOCATION",
            reason="EXACT_OCCURRENCE_CLAIM_READBACK_MATCHED",
        )
    return OccurrenceOwnershipDecision(
        may_enter_project_work=False,
        disposition="DUPLICATE_OCCURRENCE_NOOP",
        reason="OCCURRENCE_ALREADY_CLAIMED_BY_DIFFERENT_EXECUTION_RECEIPT",
    )
