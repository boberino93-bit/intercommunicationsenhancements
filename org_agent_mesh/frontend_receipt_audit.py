from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

from .frontend_execution_receipts import (
    FrontendExecutionReceiptError,
    receipt_from_dict,
    verify_frontend_execution_receipt,
)


MESSAGE_SCHEMA = "org-agent-mesh/scheduler-frontend-receipt-message/v1"
MESSAGE_TYPE = "SCHEDULER_FRONTEND_EXECUTION_RECEIPT"
DEFAULT_RECEIPT_PREFIX = "scheduler-frontend-receipt__"
DEFAULT_PROJECT_ID = "intercommunicationsenhancements"
DEFAULT_REPOSITORY = "boberino93-bit/intercommunicationsenhancements"
DEFAULT_PUBLISHER_ID = "6ac63d38cc688191b9de4213ca40f951"


class FrontendReceiptAuditError(ValueError):
    pass


def _parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise FrontendReceiptAuditError("invalid receipt timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise FrontendReceiptAuditError("receipt timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _expected_occurrence_id(job_id: str, scheduled_for: datetime) -> str:
    return f"{job_id}:{scheduled_for.strftime('%Y%m%dT%H%MZ')}"


def _canonical_digest(value: dict) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class ReceiptMessage:
    schema: str
    message_type: str
    project_id: str
    repository: str
    publisher_frontend_automation_id: str
    authority_conveyed: bool
    mutation_authority_conveyed: bool
    receipt: dict


@dataclass(frozen=True)
class AuditedReceipt:
    path: str
    receipt_id: str
    occurrence_id: str
    job_id: str
    binding_id: str
    frontend_automation_id: str
    scheduled_for: str
    observed_run_at: str
    publisher_frontend_automation_id: str
    publisher_mode: str
    digest: str


def _load_message(path: Path) -> ReceiptMessage:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FrontendReceiptAuditError(f"unreadable receipt message: {path}") from exc
    required = {
        "schema",
        "message_type",
        "project_id",
        "repository",
        "publisher_frontend_automation_id",
        "authority_conveyed",
        "mutation_authority_conveyed",
        "receipt",
    }
    if set(value) != required:
        raise FrontendReceiptAuditError("receipt message fields do not match closed schema")
    if value["schema"] != MESSAGE_SCHEMA or value["message_type"] != MESSAGE_TYPE:
        raise FrontendReceiptAuditError("unsupported receipt message schema or type")
    if value["authority_conveyed"] is not False or value["mutation_authority_conveyed"] is not False:
        raise FrontendReceiptAuditError("receipt message may not convey authority")
    if not isinstance(value["receipt"], dict):
        raise FrontendReceiptAuditError("receipt payload must be an object")
    return ReceiptMessage(**value)


def audit_receipt_directory(
    *,
    bindings: dict,
    receipt_dir: Path,
    expected_project_id: str,
    expected_repository: str,
    expected_publisher_frontend_automation_id: str,
    maximum_start_delay: timedelta = timedelta(minutes=30),
) -> dict:
    binding_by_id = {
        item["binding_id"]: item
        for item in bindings.get("bindings", [])
        if item.get("backend_job_id") is not None
    }
    accepted: list[AuditedReceipt] = []
    rejected: list[dict] = []
    seen_receipt_ids: dict[str, str] = {}

    paths = []
    if receipt_dir.exists():
        paths = sorted(
            path
            for path in receipt_dir.iterdir()
            if path.is_file() and path.name.startswith(DEFAULT_RECEIPT_PREFIX) and path.suffix == ".json"
        )

    for path in paths:
        try:
            message = _load_message(path)
            if message.project_id != expected_project_id or message.repository != expected_repository:
                raise FrontendReceiptAuditError("receipt message project or repository mismatch")
            receipt = receipt_from_dict(message.receipt)
            binding = binding_by_id.get(receipt.binding_id)
            if binding is None:
                raise FrontendReceiptAuditError("receipt references undeclared binding")
            if binding.get("backend_job_id") != receipt.job_id:
                raise FrontendReceiptAuditError("receipt job does not match declared binding")
            if binding.get("frontend_automation_id") != receipt.frontend_automation_id:
                raise FrontendReceiptAuditError("receipt frontend identity does not match declared binding")

            publisher_is_reconciler = (
                message.publisher_frontend_automation_id == expected_publisher_frontend_automation_id
            )
            publisher_is_exact_self = (
                message.publisher_frontend_automation_id == receipt.frontend_automation_id
            )
            if not (publisher_is_reconciler or publisher_is_exact_self):
                raise FrontendReceiptAuditError("receipt message publisher identity mismatch")
            publisher_mode = "DECLARED_RECONCILER" if publisher_is_reconciler else "EXACT_SELF"

            scheduled_for = _parse_time(receipt.scheduled_for)
            expected_occurrence_id = _expected_occurrence_id(receipt.job_id, scheduled_for)
            if not verify_frontend_execution_receipt(
                receipt,
                occurrence_id=expected_occurrence_id,
                job_id=receipt.job_id,
                binding_id=receipt.binding_id,
                frontend_automation_id=receipt.frontend_automation_id,
                scheduled_for=scheduled_for,
                maximum_start_delay=maximum_start_delay,
            ):
                raise FrontendReceiptAuditError("receipt failed exact identity/timing verification")
            digest = _canonical_digest(message.receipt)
            prior_digest = seen_receipt_ids.get(receipt.receipt_id)
            if prior_digest is not None:
                if prior_digest != digest:
                    raise FrontendReceiptAuditError("receipt id reused with conflicting payload")
                continue
            seen_receipt_ids[receipt.receipt_id] = digest
            accepted.append(
                AuditedReceipt(
                    path=str(path),
                    receipt_id=receipt.receipt_id,
                    occurrence_id=receipt.occurrence_id,
                    job_id=receipt.job_id,
                    binding_id=receipt.binding_id,
                    frontend_automation_id=receipt.frontend_automation_id,
                    scheduled_for=receipt.scheduled_for,
                    observed_run_at=receipt.observed_run_at,
                    publisher_frontend_automation_id=message.publisher_frontend_automation_id,
                    publisher_mode=publisher_mode,
                    digest=digest,
                )
            )
        except (FrontendReceiptAuditError, FrontendExecutionReceiptError) as exc:
            rejected.append({"path": str(path), "reason": str(exc)})

    latest_by_job: dict[str, dict] = {}
    for item in accepted:
        previous = latest_by_job.get(item.job_id)
        if previous is None or _parse_time(item.observed_run_at) > _parse_time(previous["observed_run_at"]):
            latest_by_job[item.job_id] = asdict(item)

    return {
        "schema": "org-agent-mesh/frontend-receipt-audit/v1",
        "receipt_directory": str(receipt_dir),
        "accepted_receipt_count": len(accepted),
        "rejected_receipt_count": len(rejected),
        "self_published_receipt_count": sum(1 for item in accepted if item.publisher_mode == "EXACT_SELF"),
        "reconciler_published_receipt_count": sum(
            1 for item in accepted if item.publisher_mode == "DECLARED_RECONCILER"
        ),
        "accepted_receipts": [asdict(item) for item in accepted],
        "rejected_receipts": rejected,
        "latest_verified_by_job": latest_by_job,
        "authority_conveyed": False,
        "mutation_authority_conveyed": False,
    }


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit append-only mapped frontend execution receipts")
    parser.add_argument("--bindings", default="governance/SCHEDULER_FRONTEND_BINDINGS.json")
    parser.add_argument("--receipt-dir", default="agentbus-backup/coordination-messages")
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    parser.add_argument("--publisher-id", default=DEFAULT_PUBLISHER_ID)
    parser.add_argument("--out", default="scheduler-out/frontend-receipt-audit.json")
    args = parser.parse_args(argv)

    bindings = json.loads(Path(args.bindings).read_text(encoding="utf-8"))
    audit = audit_receipt_directory(
        bindings=bindings,
        receipt_dir=Path(args.receipt_dir),
        expected_project_id=args.project_id,
        expected_repository=args.repository,
        expected_publisher_frontend_automation_id=args.publisher_id,
    )
    _write_json(Path(args.out), audit)
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
