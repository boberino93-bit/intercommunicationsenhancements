from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json


RECEIPT_SCHEMA = "org-agent-mesh/frontend-execution-receipt/v1"
RECEIPT_STATUS = "FRONTEND_EXECUTION_OBSERVED"


class FrontendExecutionReceiptError(ValueError):
    pass


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise FrontendExecutionReceiptError("timezone-aware datetime required")
    return value.astimezone(timezone.utc)


def _parse(value: str) -> datetime:
    try:
        return _utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
    except (TypeError, ValueError) as exc:
        raise FrontendExecutionReceiptError("invalid ISO-8601 timestamp") from exc


def _iso(value: datetime) -> str:
    return _utc(value).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class FrontendExecutionReceipt:
    schema: str
    receipt_id: str
    occurrence_id: str
    job_id: str
    binding_id: str
    frontend_automation_id: str
    scheduled_for: str
    observed_run_at: str
    observed_at: str
    execution_surface: str = "CHATGPT_FRONTEND_MAPPED"
    status: str = RECEIPT_STATUS
    authority_conveyed: bool = False
    mutation_authority_conveyed: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


def make_frontend_execution_receipt(
    *,
    occurrence_id: str,
    job_id: str,
    binding_id: str,
    frontend_automation_id: str,
    scheduled_for: datetime,
    observed_run_at: datetime,
    observed_at: datetime,
) -> FrontendExecutionReceipt:
    scheduled_for = _utc(scheduled_for)
    observed_run_at = _utc(observed_run_at)
    observed_at = _utc(observed_at)
    if observed_run_at < scheduled_for:
        raise FrontendExecutionReceiptError("observed run predates scheduled occurrence")
    if observed_run_at > observed_at:
        raise FrontendExecutionReceiptError("observed run cannot be in the future relative to observation")
    identity = "|".join(
        [
            occurrence_id,
            job_id,
            binding_id,
            frontend_automation_id,
            _iso(observed_run_at),
        ]
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
    return FrontendExecutionReceipt(
        schema=RECEIPT_SCHEMA,
        receipt_id=f"frontend-receipt-{digest}",
        occurrence_id=occurrence_id,
        job_id=job_id,
        binding_id=binding_id,
        frontend_automation_id=frontend_automation_id,
        scheduled_for=_iso(scheduled_for),
        observed_run_at=_iso(observed_run_at),
        observed_at=_iso(observed_at),
    )


def receipt_from_dict(value: dict) -> FrontendExecutionReceipt:
    required = {
        "schema",
        "receipt_id",
        "occurrence_id",
        "job_id",
        "binding_id",
        "frontend_automation_id",
        "scheduled_for",
        "observed_run_at",
        "observed_at",
        "execution_surface",
        "status",
        "authority_conveyed",
        "mutation_authority_conveyed",
    }
    missing = sorted(required - set(value))
    if missing:
        raise FrontendExecutionReceiptError(f"missing receipt fields: {', '.join(missing)}")
    receipt = FrontendExecutionReceipt(**{key: value[key] for key in required})
    if receipt.schema != RECEIPT_SCHEMA:
        raise FrontendExecutionReceiptError("unsupported receipt schema")
    if receipt.execution_surface != "CHATGPT_FRONTEND_MAPPED":
        raise FrontendExecutionReceiptError("receipt execution surface mismatch")
    if receipt.status != RECEIPT_STATUS:
        raise FrontendExecutionReceiptError("receipt status is not observed execution")
    if receipt.authority_conveyed or receipt.mutation_authority_conveyed:
        raise FrontendExecutionReceiptError("execution receipt may not convey authority")
    _parse(receipt.scheduled_for)
    _parse(receipt.observed_run_at)
    _parse(receipt.observed_at)
    return receipt


def verify_frontend_execution_receipt(
    receipt: FrontendExecutionReceipt,
    *,
    occurrence_id: str,
    job_id: str,
    binding_id: str,
    frontend_automation_id: str,
    scheduled_for: datetime,
    maximum_start_delay: timedelta = timedelta(minutes=30),
) -> bool:
    if receipt.schema != RECEIPT_SCHEMA or receipt.status != RECEIPT_STATUS:
        return False
    if receipt.execution_surface != "CHATGPT_FRONTEND_MAPPED":
        return False
    if receipt.authority_conveyed or receipt.mutation_authority_conveyed:
        return False
    if receipt.occurrence_id != occurrence_id:
        return False
    if receipt.job_id != job_id or receipt.binding_id != binding_id:
        return False
    if receipt.frontend_automation_id != frontend_automation_id:
        return False
    expected_scheduled_for = _utc(scheduled_for)
    if _parse(receipt.scheduled_for) != expected_scheduled_for:
        return False
    observed_run_at = _parse(receipt.observed_run_at)
    observed_at = _parse(receipt.observed_at)
    if observed_run_at < expected_scheduled_for:
        return False
    if observed_run_at - expected_scheduled_for > maximum_start_delay:
        return False
    if observed_run_at > observed_at:
        return False
    return True


def canonical_receipt_json(receipt: FrontendExecutionReceipt) -> str:
    return json.dumps(receipt.as_dict(), sort_keys=True, separators=(",", ":"))
