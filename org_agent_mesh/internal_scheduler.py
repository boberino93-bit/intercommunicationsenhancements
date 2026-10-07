from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Protocol
from urllib import error, request


TICKET_SCHEMA = "org-agent-mesh/scheduled-spawn-ticket/v1"
ALLOWED_ROLES = frozenset({"research", "manager"})


class InternalSchedulerError(ValueError):
    pass


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise InternalSchedulerError("timezone-aware datetime required")
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return _aware_utc(value).isoformat().replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return _aware_utc(parsed)


@dataclass(frozen=True)
class ScheduleJob:
    job_id: str
    enabled: bool
    minute_offsets: tuple[int, ...]
    grace_minutes: int
    launch_scope: str
    requested_roles: tuple[str, ...]
    max_workers_per_occurrence: int = 1

    @classmethod
    def from_dict(cls, value: dict) -> "ScheduleJob":
        schedule = value.get("schedule") or {}
        if schedule.get("type") != "HOURLY_MINUTE_OFFSETS":
            raise InternalSchedulerError("unsupported schedule type")
        offsets = tuple(sorted(set(schedule.get("minute_offsets") or [])))
        if not offsets or any(not isinstance(x, int) or x < 0 or x > 59 for x in offsets):
            raise InternalSchedulerError("minute_offsets must contain integers from 0 through 59")
        grace = schedule.get("grace_minutes", 10)
        if not isinstance(grace, int) or grace < 0 or grace > 59:
            raise InternalSchedulerError("grace_minutes must be an integer from 0 through 59")
        roles = tuple(value.get("requested_roles") or ())
        if not roles or not set(roles).issubset(ALLOWED_ROLES):
            raise InternalSchedulerError("requested_roles may contain only research and manager")
        if value.get("primary_prohibited") is not True:
            raise InternalSchedulerError("every scheduled job must explicitly prohibit PRIMARY")
        workers = value.get("max_workers_per_occurrence", 1)
        if workers != 1:
            raise InternalSchedulerError("v1 permits exactly one worker per occurrence")
        job_id = value.get("job_id")
        scope = value.get("launch_scope")
        if not isinstance(job_id, str) or not job_id.strip():
            raise InternalSchedulerError("job_id is required")
        if not isinstance(scope, str) or not scope.strip():
            raise InternalSchedulerError("launch_scope is required")
        return cls(
            job_id=job_id.strip(),
            enabled=bool(value.get("enabled")),
            minute_offsets=offsets,
            grace_minutes=grace,
            launch_scope=scope.strip(),
            requested_roles=roles,
            max_workers_per_occurrence=workers,
        )


@dataclass(frozen=True)
class SpawnTicket:
    schema: str
    ticket_id: str
    job_id: str
    occurrence_id: str
    scheduled_for: str
    observed_at: str
    launch_scope: str
    requested_roles: tuple[str, ...]
    max_workers: int
    status: str = "SPAWN_TICKET_PENDING"
    adapter_result: str | None = None
    host_start_receipt: str | None = None
    authority_conveyed: bool = False
    mutation_authority_conveyed: bool = False

    def as_dict(self) -> dict:
        value = asdict(self)
        value["requested_roles"] = list(self.requested_roles)
        return value


@dataclass(frozen=True)
class DispatchResult:
    status: str
    adapter_result: str
    host_start_receipt: str | None = None


class SpawnAdapter(Protocol):
    def dispatch(self, ticket: SpawnTicket) -> DispatchResult: ...


class WebhookSpawnAdapter:
    def __init__(self, endpoint: str | None = None, token: str | None = None, timeout_seconds: int = 20):
        self.endpoint = endpoint or os.getenv("ORG_AGENT_MESH_SPAWN_ENDPOINT")
        self.token = token or os.getenv("ORG_AGENT_MESH_SPAWN_TOKEN")
        self.timeout_seconds = timeout_seconds

    @property
    def configured(self) -> bool:
        return bool(self.endpoint and self.token and self.endpoint.startswith("https://"))

    def dispatch(self, ticket: SpawnTicket) -> DispatchResult:
        if not self.configured:
            return DispatchResult("SPAWN_ADAPTER_UNAVAILABLE", "SPAWN_ADAPTER_UNAVAILABLE")
        payload = json.dumps(ticket.as_dict(), sort_keys=True).encode("utf-8")
        req = request.Request(
            self.endpoint,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Idempotency-Key": ticket.occurrence_id,
            },
        )
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
                code = response.getcode()
        except (error.URLError, TimeoutError) as exc:
            return DispatchResult("SPAWN_ADAPTER_REJECTED", f"ADAPTER_TRANSPORT_ERROR:{type(exc).__name__}")
        if code < 200 or code >= 300:
            return DispatchResult("SPAWN_ADAPTER_REJECTED", f"HTTP_{code}")
        try:
            decoded = json.loads(body) if body else {}
        except json.JSONDecodeError:
            decoded = {}
        if decoded.get("accepted") is not True:
            return DispatchResult("SPAWN_ADAPTER_REJECTED", "ADAPTER_DID_NOT_ACCEPT")
        receipt = decoded.get("spawn_receipt")
        if not isinstance(receipt, str) or not receipt.strip():
            return DispatchResult(
                "DISPATCH_ACCEPTED_START_UNVERIFIED",
                "ADAPTER_ACCEPTED_WITHOUT_START_RECEIPT",
            )
        return DispatchResult("SESSION_STARTED_VERIFIED", "HOST_START_RECEIPT_VERIFIED", receipt.strip())


def due_boundary(job: ScheduleJob, now: datetime) -> datetime | None:
    now = _aware_utc(now)
    candidates: list[datetime] = []
    for hour_delta in (0, -1):
        hour = (now + timedelta(hours=hour_delta)).replace(minute=0, second=0, microsecond=0)
        for minute in job.minute_offsets:
            boundary = hour + timedelta(minutes=minute)
            if boundary <= now:
                candidates.append(boundary)
    if not candidates:
        return None
    latest = max(candidates)
    if now - latest > timedelta(minutes=job.grace_minutes):
        return None
    return latest


def make_ticket(job: ScheduleJob, scheduled_for: datetime, observed_at: datetime) -> SpawnTicket:
    scheduled_for = _aware_utc(scheduled_for)
    observed_at = _aware_utc(observed_at)
    occurrence_id = f"{job.job_id}:{scheduled_for.strftime('%Y%m%dT%H%MZ')}"
    digest = hashlib.sha256(occurrence_id.encode("utf-8")).hexdigest()[:24]
    return SpawnTicket(
        schema=TICKET_SCHEMA,
        ticket_id=f"spawn-{digest}",
        job_id=job.job_id,
        occurrence_id=occurrence_id,
        scheduled_for=_iso(scheduled_for),
        observed_at=_iso(observed_at),
        launch_scope=job.launch_scope,
        requested_roles=job.requested_roles,
        max_workers=1,
    )


def evaluate_registry(registry: dict, now: datetime, max_tickets: int = 3) -> list[SpawnTicket]:
    if registry.get("catch_up_policy") != "COALESCE_TO_LATEST":
        raise InternalSchedulerError("registry must use COALESCE_TO_LATEST")
    tickets: list[SpawnTicket] = []
    seen_occurrences: set[str] = set()
    for raw in registry.get("jobs") or []:
        job = ScheduleJob.from_dict(raw)
        if not job.enabled:
            continue
        boundary = due_boundary(job, now)
        if boundary is None:
            continue
        ticket = make_ticket(job, boundary, now)
        if ticket.occurrence_id in seen_occurrences:
            continue
        seen_occurrences.add(ticket.occurrence_id)
        tickets.append(ticket)
        if len(tickets) >= max_tickets:
            break
    return tickets


def dispatch_ticket(ticket: SpawnTicket, adapter: SpawnAdapter) -> SpawnTicket:
    result = adapter.dispatch(ticket)
    return replace(
        ticket,
        status=result.status,
        adapter_result=result.adapter_result,
        host_start_receipt=result.host_start_receipt,
    )


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, indent=2, sort_keys=True) + "\n"
    try:
        path.write_text(encoded, encoding="utf-8", errors="strict", newline="\n")
    except TypeError:
        path.write_text(encoded, encoding="utf-8")


def run_once(registry_path: Path, policy_path: Path, out_dir: Path, now: datetime, dispatch: bool) -> list[SpawnTicket]:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    if policy.get("service", {}).get("enabled") is not True:
        return []
    delegated = policy.get("delegated_spawn_authority") or {}
    if delegated.get("primary_allowed") is not False or delegated.get("master_allowed") is not False:
        raise InternalSchedulerError("scheduler policy must prohibit PRIMARY and MASTER")
    max_tickets = int(delegated.get("max_tickets_per_scheduler_invocation", 3))
    tickets = evaluate_registry(registry, now, max_tickets=max_tickets)
    adapter = WebhookSpawnAdapter()
    emitted: list[SpawnTicket] = []
    for ticket in tickets:
        final = dispatch_ticket(ticket, adapter) if dispatch else ticket
        emitted.append(final)
        _write_json(out_dir / f"{final.ticket_id}.json", final.as_dict())
    summary = {
        "schema": "org-agent-mesh/internal-scheduler-run/v1",
        "observed_at": _iso(now),
        "due_ticket_count": len(emitted),
        "dispatch_requested": dispatch,
        "results": [ticket.as_dict() for ticket in emitted],
    }
    _write_json(out_dir / "run-summary.json", summary)
    return emitted


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate and optionally dispatch governed spawn schedules")
    parser.add_argument("--registry", default="governance/INTERNAL_SPAWN_SCHEDULES.json")
    parser.add_argument("--policy", default="governance/INTERNAL_SPAWN_SCHEDULER_POLICY.json")
    parser.add_argument("--out-dir", default="scheduler-out")
    parser.add_argument("--now", default=None, help="ISO-8601 time; defaults to current UTC")
    parser.add_argument("--dispatch", action="store_true")
    args = parser.parse_args(argv)
    now = _parse_time(args.now) if args.now else datetime.now(timezone.utc)
    run_once(Path(args.registry), Path(args.policy), Path(args.out_dir), now, args.dispatch)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
