from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

UTC = timezone.utc


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return parsed.astimezone(UTC)


def _occurrence_id(job_id: str, scheduled_for: datetime) -> str:
    return f"{job_id}:{scheduled_for.strftime('%Y%m%dT%H%MZ')}"


def _health_evidence_deadline_minutes(job: dict, policy: dict) -> int:
    job_grace = int(job.get("schedule", {}).get("grace_minutes", 0))
    receipt_window = int(policy.get("receipt_acceptance_window_minutes", 0))
    persistence_grace = int(policy.get("receipt_persistence_grace_minutes", 0))
    configured_deadline = int(policy.get("health_evidence_deadline_minutes", 0))
    minimum_deadline = max(job_grace, receipt_window + persistence_grace)
    if configured_deadline < minimum_deadline:
        raise ValueError(
            "health evidence deadline must cover job grace and receipt acceptance plus persistence grace"
        )
    return configured_deadline


def _mature_occurrences(
    job: dict,
    *,
    observed_at: datetime,
    count: int,
    evidence_deadline_minutes: int,
) -> list[datetime]:
    schedule = job["schedule"]
    if schedule.get("type") != "HOURLY_MINUTE_OFFSETS":
        raise ValueError("unsupported schedule type for health qualification")
    offsets = schedule.get("minute_offsets", [])
    if len(offsets) != 1:
        raise ValueError("health qualification requires exactly one hourly minute offset")
    minute = int(offsets[0])
    cutoff = observed_at.astimezone(UTC) - timedelta(minutes=evidence_deadline_minutes)
    anchor = cutoff.replace(minute=minute, second=0, microsecond=0)
    if anchor > cutoff:
        anchor -= timedelta(hours=1)
    return [anchor - timedelta(hours=i) for i in range(count)]


def evaluate_scheduler_health(
    *,
    registry: dict,
    bindings: dict,
    receipt_audit: dict,
    policy: dict,
    observed_at: datetime,
) -> dict:
    required = int(policy["required_consecutive_verified_occurrences"])
    if required < 1:
        raise ValueError("required_consecutive_verified_occurrences must be positive")

    binding_by_job = {
        item["backend_job_id"]: item
        for item in bindings.get("bindings", [])
        if item.get("backend_job_id") is not None
    }
    verified_occurrences = {
        item["occurrence_id"] for item in receipt_audit.get("accepted_receipts", [])
    }

    lanes = []
    for job in registry.get("jobs", []):
        if not job.get("enabled") or job.get("execution_surface") != "CHATGPT_FRONTEND_MAPPED":
            continue
        job_id = job["job_id"]
        binding = binding_by_job.get(job_id)
        if binding is None:
            lanes.append({
                "job_id": job_id,
                "state": "UNQUALIFIED",
                "reason": "MISSING_DECLARED_FRONTEND_BINDING",
                "healthy": False,
            })
            continue
        try:
            evidence_deadline = _health_evidence_deadline_minutes(job, policy)
            mature = _mature_occurrences(
                job,
                observed_at=observed_at,
                count=required,
                evidence_deadline_minutes=evidence_deadline,
            )
        except ValueError as exc:
            lanes.append({
                "job_id": job_id,
                "binding_id": binding.get("binding_id"),
                "frontend_automation_id": binding.get("frontend_automation_id"),
                "state": "UNQUALIFIED",
                "reason": str(exc),
                "healthy": False,
            })
            continue

        expected_ids = [_occurrence_id(job_id, value) for value in mature]
        verified_flags = [value in verified_occurrences for value in expected_ids]
        consecutive = 0
        for flag in verified_flags:
            if not flag:
                break
            consecutive += 1
        missing = [value for value, flag in zip(expected_ids, verified_flags) if not flag]
        if consecutive == required:
            state = "HEALTHY"
            reason = "SUSTAINED_CONSECUTIVE_EXECUTION_VERIFIED"
            healthy = True
        elif verified_flags and verified_flags[0]:
            state = "RECOVERING"
            reason = "LATEST_MATURE_OCCURRENCE_VERIFIED_BUT_SUSTAINED_HEALTH_NOT_YET_QUALIFIED"
            healthy = False
        else:
            state = "DEGRADED_MISSING_EXECUTION_EVIDENCE"
            reason = "LATEST_MATURE_OCCURRENCE_HAS_NO_VERIFIED_EXECUTION_RECEIPT"
            healthy = False

        lanes.append({
            "job_id": job_id,
            "binding_id": binding.get("binding_id"),
            "frontend_automation_id": binding.get("frontend_automation_id"),
            "state": state,
            "reason": reason,
            "healthy": healthy,
            "required_consecutive_verified_occurrences": required,
            "verified_consecutive_occurrences": consecutive,
            "health_evidence_deadline_minutes": evidence_deadline,
            "latest_mature_occurrence_id": expected_ids[0],
            "evaluated_occurrence_ids": expected_ids,
            "missing_occurrence_ids": missing,
        })

    unhealthy = [lane for lane in lanes if not lane["healthy"]]
    return {
        "schema": "org-agent-mesh/scheduler-health-report/v1",
        "observed_at": observed_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "required_consecutive_verified_occurrences": required,
        "receipt_acceptance_window_minutes": int(policy.get("receipt_acceptance_window_minutes", 0)),
        "receipt_persistence_grace_minutes": int(policy.get("receipt_persistence_grace_minutes", 0)),
        "health_evidence_deadline_minutes": int(policy.get("health_evidence_deadline_minutes", 0)),
        "lane_count": len(lanes),
        "healthy_lane_count": len(lanes) - len(unhealthy),
        "unhealthy_lane_count": len(unhealthy),
        "overall_state": "HEALTHY" if not unhealthy else "DEGRADED",
        "lanes": lanes,
        "common_mode_note": "ChatGPT bridge and Slot 1 share the same provider failure domain; this report detects failures but does not claim independent frontend actuation.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Qualify mapped frontend scheduler health from exact execution receipts")
    parser.add_argument("--registry", default="governance/INTERNAL_SPAWN_SCHEDULES.json")
    parser.add_argument("--bindings", default="governance/SCHEDULER_FRONTEND_BINDINGS.json")
    parser.add_argument("--receipt-audit", default="scheduler-out/frontend-receipt-audit.json")
    parser.add_argument("--policy", default="governance/SCHEDULER_HEALTH_POLICY.json")
    parser.add_argument("--out", default="scheduler-out/frontend-health.json")
    parser.add_argument("--observed-at", default=None)
    args = parser.parse_args(argv)

    observed_at = _parse_time(args.observed_at) if args.observed_at else datetime.now(UTC)
    report = evaluate_scheduler_health(
        registry=json.loads(Path(args.registry).read_text(encoding="utf-8")),
        bindings=json.loads(Path(args.bindings).read_text(encoding="utf-8")),
        receipt_audit=json.loads(Path(args.receipt_audit).read_text(encoding="utf-8")),
        policy=json.loads(Path(args.policy).read_text(encoding="utf-8")),
        observed_at=observed_at,
    )
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["overall_state"] == "HEALTHY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
