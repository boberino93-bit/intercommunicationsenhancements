from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Iterable, Mapping

SCHEMA = "org-agent-mesh/live-operations-snapshot/v1"

ROLE_STATES = {
    "STARTING",
    "RUNNING",
    "REDIRECT_REQUESTED",
    "WAITING_UPSTREAM",
    "WAITING_MANAGER",
    "WAITING_PRIMARY",
    "BLOCKED",
    "PAUSE_REQUESTED",
    "PAUSED",
    "STOP_REQUESTED",
    "STOPPING",
    "STOPPED",
    "COMPLETED",
    "FAILED",
    "IDLE_READY",
    "UNKNOWN",
}
EXECUTING_STATES = {"STARTING", "RUNNING", "REDIRECT_REQUESTED", "STOPPING"}
WAITING_STATES = {
    "WAITING_UPSTREAM",
    "WAITING_MANAGER",
    "WAITING_PRIMARY",
    "BLOCKED",
    "PAUSE_REQUESTED",
    "PAUSED",
}
TERMINAL_STATES = {"STOPPED", "COMPLETED", "FAILED", "IDLE_READY"}


class OperationsViewError(ValueError):
    pass


def _utc_now(now=None) -> datetime:
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None or value.utcoffset() is None:
        raise OperationsViewError("now must be timezone-aware")
    return value.astimezone(timezone.utc)


def _parse_utc(value, *, field: str) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise OperationsViewError(f"{field} must be null or a non-empty ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise OperationsViewError(f"{field} must be valid ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise OperationsViewError(f"{field} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _nonempty(value, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OperationsViewError(f"{field} must be a non-empty string")
    return value.strip()


def _role_observation(raw: Mapping, *, now: datetime, stale_after_seconds: int) -> dict:
    if not isinstance(raw, Mapping):
        raise OperationsViewError("role observation must be an object")
    agent_id = _nonempty(raw.get("agent_id"), field="agent_id")
    role = _nonempty(raw.get("role"), field="role").upper()
    if role not in {"PRIMARY", "MANAGER", "RESEARCH", "MASTER"}:
        raise OperationsViewError(f"unsupported role {role!r}")
    state = _nonempty(raw.get("state"), field="state").upper()
    if state not in ROLE_STATES:
        raise OperationsViewError(f"unsupported role state {state!r}")
    observed_at = _parse_utc(raw.get("observed_at_utc"), field="observed_at_utc")
    if observed_at is None:
        raise OperationsViewError("observed_at_utc is required")
    age_seconds = max(0.0, (now - observed_at).total_seconds())
    stale = state not in TERMINAL_STATES and age_seconds > stale_after_seconds
    return {
        "agent_id": agent_id,
        "role": role,
        "state": state,
        "observed_at_utc": _iso(observed_at),
        "age_seconds": round(age_seconds, 3),
        "stale": stale,
        "task_id": raw.get("task_id"),
        "checkpoint_ref": raw.get("checkpoint_ref"),
    }


def _source_coordination_state(raw: Mapping, *, now: datetime, drift_grace_seconds: int) -> dict:
    repo_revision = raw.get("repository_revision")
    coordinated_revision = raw.get("coordination_repository_revision")
    repo_time = _parse_utc(raw.get("repository_observed_at_utc"), field="repository_observed_at_utc")
    coord_time = _parse_utc(raw.get("coordination_observed_at_utc"), field="coordination_observed_at_utc")

    if repo_revision is not None:
        repo_revision = _nonempty(repo_revision, field="repository_revision")
    if coordinated_revision is not None:
        coordinated_revision = _nonempty(
            coordinated_revision, field="coordination_repository_revision"
        )

    if not repo_revision or not coordinated_revision:
        state = "UNKNOWN"
    elif repo_revision == coordinated_revision:
        state = "IN_SYNC"
    elif repo_time is None or coord_time is None:
        state = "REVISION_MISMATCH"
    elif repo_time <= coord_time:
        state = "COORDINATION_REVISION_MISMATCH"
    else:
        coordination_age = max(0.0, (now - coord_time).total_seconds())
        state = (
            "PENDING_RECONCILIATION"
            if coordination_age <= drift_grace_seconds
            else "SOURCE_AHEAD_OF_COORDINATION"
        )

    return {
        "state": state,
        "repository_revision": repo_revision,
        "coordination_repository_revision": coordinated_revision,
        "repository_observed_at_utc": _iso(repo_time) if repo_time else None,
        "coordination_observed_at_utc": _iso(coord_time) if coord_time else None,
        "coordination_checkpoint_ref": raw.get("coordination_checkpoint_ref"),
    }


def _project_observation(
    raw: Mapping,
    *,
    now: datetime,
    stale_after_seconds: int,
    drift_grace_seconds: int,
) -> dict:
    if not isinstance(raw, Mapping):
        raise OperationsViewError("project observation must be an object")
    project_id = _nonempty(raw.get("project_id"), field="project_id")
    repository_identity = _nonempty(
        raw.get("repository_identity"), field="repository_identity"
    )
    registered = raw.get("registered")
    normalized = raw.get("normalized")
    if not isinstance(registered, bool) or not isinstance(normalized, bool):
        raise OperationsViewError("registered and normalized must be booleans")

    roles_raw = raw.get("roles", [])
    if not isinstance(roles_raw, list):
        raise OperationsViewError("roles must be a list")
    roles = [
        _role_observation(item, now=now, stale_after_seconds=stale_after_seconds)
        for item in roles_raw
    ]
    agent_ids = [item["agent_id"] for item in roles]
    if len(agent_ids) != len(set(agent_ids)):
        raise OperationsViewError(f"duplicate agent_id in project {project_id!r}")

    blockers = raw.get("blockers", [])
    if not isinstance(blockers, list) or not all(
        isinstance(item, str) and item.strip() for item in blockers
    ):
        raise OperationsViewError("blockers must be a list of non-empty strings")

    source = _source_coordination_state(
        raw, now=now, drift_grace_seconds=drift_grace_seconds
    )
    fresh = [role for role in roles if not role["stale"]]
    stale_active = [role for role in roles if role["stale"]]
    executing = [role for role in fresh if role["state"] in EXECUTING_STATES]
    waiting = [role for role in fresh if role["state"] in WAITING_STATES]

    unattributed_activity = raw.get("unattributed_activity", False)
    if not isinstance(unattributed_activity, bool):
        raise OperationsViewError("unattributed_activity must be boolean")

    if stale_active:
        status = "STALE"
    elif executing:
        status = "EXECUTING"
    elif blockers:
        status = "BLOCKED"
    elif waiting:
        status = "WAITING"
    elif unattributed_activity:
        status = "ACTIVITY_UNATTRIBUTED"
    elif registered and normalized:
        status = "IDLE_READY"
    elif registered:
        status = "REGISTERED_UNVERIFIED"
    else:
        status = "UNKNOWN"

    return {
        "project_id": project_id,
        "repository_identity": repository_identity,
        "registered": registered,
        "normalized": normalized,
        "status": status,
        "source_coordination": source,
        "roles": roles,
        "blockers": blockers,
        "unattributed_activity": unattributed_activity,
    }


def build_live_operations_snapshot(
    projects: Iterable[Mapping],
    *,
    now=None,
    stale_after_seconds: int = 1800,
    drift_grace_seconds: int = 900,
) -> dict:
    """Build a read-only derived view of current multi-project swarm operations.

    Inputs are observations only. This function never grants authority, mutates
    canonical project state, or treats GitHub as coordination truth.
    """
    if not isinstance(stale_after_seconds, int) or stale_after_seconds <= 0:
        raise OperationsViewError("stale_after_seconds must be a positive integer")
    if not isinstance(drift_grace_seconds, int) or drift_grace_seconds < 0:
        raise OperationsViewError("drift_grace_seconds must be a non-negative integer")

    current = _utc_now(now)
    if isinstance(projects, Mapping):
        raise OperationsViewError("projects must be an iterable of project objects")
    normalized = [
        _project_observation(
            item,
            now=current,
            stale_after_seconds=stale_after_seconds,
            drift_grace_seconds=drift_grace_seconds,
        )
        for item in projects
    ]

    ids = [item["project_id"] for item in normalized]
    if len(ids) != len(set(ids)):
        raise OperationsViewError("project_id values must be unique")
    repositories = [item["repository_identity"] for item in normalized]
    if len(repositories) != len(set(repositories)):
        raise OperationsViewError("repository_identity values must be unique")

    status_counts = Counter(item["status"] for item in normalized)
    source_counts = Counter(item["source_coordination"]["state"] for item in normalized)

    fresh_roles = [
        role
        for project in normalized
        for role in project["roles"]
        if not role["stale"]
    ]
    active_roles = [
        role
        for role in fresh_roles
        if role["state"] not in TERMINAL_STATES and role["state"] != "UNKNOWN"
    ]
    executing_roles = [role for role in fresh_roles if role["state"] in EXECUTING_STATES]

    return {
        "schema": SCHEMA,
        "generated_at_utc": _iso(current),
        "semantics": {
            "authority": "READ_ONLY_DERIVED_VIEW",
            "coordination_truth": "PROJECT_LOCAL_AGENTBUS_AND_DURABLE_STATE",
            "github_role": "SOURCE_VERSION_CONTROL_NOT_COORDINATION_AUTHORITY",
            "stale_after_seconds": stale_after_seconds,
            "drift_grace_seconds": drift_grace_seconds,
        },
        "summary": {
            "registered_projects": sum(1 for p in normalized if p["registered"]),
            "normalized_projects": sum(1 for p in normalized if p["normalized"]),
            "executing_projects": status_counts["EXECUTING"],
            "waiting_projects": status_counts["WAITING"] + status_counts["BLOCKED"],
            "idle_ready_projects": status_counts["IDLE_READY"],
            "stale_projects": status_counts["STALE"],
            "unattributed_activity_projects": status_counts["ACTIVITY_UNATTRIBUTED"],
            "active_agents": len(active_roles),
            "executing_agents": len(executing_roles),
            "waiting_for_manager": sum(
                1 for role in fresh_roles if role["state"] == "WAITING_MANAGER"
            ),
            "waiting_for_primary": sum(
                1 for role in fresh_roles if role["state"] == "WAITING_PRIMARY"
            ),
            "source_ahead_projects": source_counts["SOURCE_AHEAD_OF_COORDINATION"],
            "pending_reconciliation_projects": source_counts["PENDING_RECONCILIATION"],
        },
        "projects": sorted(normalized, key=lambda item: item["project_id"]),
    }


def render_operations_markdown(snapshot: Mapping) -> str:
    if snapshot.get("schema") != SCHEMA:
        raise OperationsViewError("unsupported operations snapshot schema")
    summary = snapshot["summary"]
    lines = [
        "# Live swarm operations",
        "",
        f"Generated: `{snapshot['generated_at_utc']}`",
        "",
        (
            f"Registered **{summary['registered_projects']}** · "
            f"Executing **{summary['executing_projects']}** · "
            f"Waiting/blocked **{summary['waiting_projects']}** · "
            f"Idle/ready **{summary['idle_ready_projects']}** · "
            f"Stale **{summary['stale_projects']}**"
        ),
        (
            f"Active agents **{summary['active_agents']}** · "
            f"Executing agents **{summary['executing_agents']}** · "
            f"Waiting Manager **{summary['waiting_for_manager']}** · "
            f"Waiting Primary **{summary['waiting_for_primary']}**"
        ),
        "",
        "| Project | Status | Source ↔ coordination | Active roles |",
        "|---|---|---|---|",
    ]
    for project in snapshot["projects"]:
        active = [
            f"{role['role']}:{role['state']}"
            for role in project["roles"]
            if not role["stale"]
            and role["state"] not in TERMINAL_STATES
            and role["state"] != "UNKNOWN"
        ]
        lines.append(
            f"| `{project['project_id']}` | {project['status']} | "
            f"{project['source_coordination']['state']} | "
            f"{', '.join(active) if active else '—'} |"
        )
    return "\n".join(lines) + "\n"
