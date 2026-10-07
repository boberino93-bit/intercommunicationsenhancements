from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Mapping

SCHEMA = "org-agent-mesh/project-glance-index/v1"
LOCAL_SCHEMA = "org-agent-mesh/project-glance/v1"
ALLOWED_STATUS = {"EXECUTING", "WAITING", "BLOCKED", "IDLE_READY", "PAUSED", "STALE", "UNKNOWN"}


class ProjectGlanceError(ValueError):
    pass


def _parse_time(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ProjectGlanceError("observed_at_utc must be a non-empty ISO-8601 string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ProjectGlanceError("observed_at_utc must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _now(value=None) -> datetime:
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise ProjectGlanceError("now must be timezone-aware")
    return current.astimezone(timezone.utc)


def _nonempty(value, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProjectGlanceError(f"{field} must be a non-empty string")
    return value.strip()


def normalize_project_glance(raw: Mapping, *, now=None, stale_seconds: int = 3600) -> dict:
    if not isinstance(raw, Mapping):
        raise ProjectGlanceError("project glance must be an object")
    if stale_seconds <= 0:
        raise ProjectGlanceError("stale_seconds must be positive")
    project_id = _nonempty(raw.get("project_id"), "project_id")
    repository = _nonempty(raw.get("repository"), "repository")
    status = _nonempty(raw.get("status"), "status").upper()
    if status not in ALLOWED_STATUS:
        raise ProjectGlanceError(f"unsupported status {status!r}")
    current_focus = _nonempty(raw.get("current_focus"), "current_focus")
    next_action = _nonempty(raw.get("next_action"), "next_action")
    last_material_change = _nonempty(raw.get("last_material_change"), "last_material_change")
    observed_at = _parse_time(raw.get("observed_at_utc"))
    blockers = raw.get("blockers", [])
    evidence_refs = raw.get("evidence_refs", [])
    if not isinstance(blockers, list) or not all(isinstance(x, str) and x.strip() for x in blockers):
        raise ProjectGlanceError("blockers must be a list of non-empty strings")
    if not isinstance(evidence_refs, list) or not all(isinstance(x, str) and x.strip() for x in evidence_refs):
        raise ProjectGlanceError("evidence_refs must be a list of non-empty strings")
    age_seconds = max(0, int((_now(now) - observed_at).total_seconds()))
    freshness = "FRESH" if age_seconds <= stale_seconds else "STALE"
    effective_status = status if freshness == "FRESH" else "STALE"
    return {
        "project_id": project_id,
        "repository": repository,
        "observed_at_utc": observed_at.isoformat().replace("+00:00", "Z"),
        "status": effective_status,
        "reported_status": status,
        "current_focus": current_focus,
        "blockers": list(blockers),
        "blocker_summary": blockers[0] if blockers else "none",
        "next_action": next_action,
        "last_material_change": last_material_change,
        "evidence_refs": list(evidence_refs),
        "freshness": freshness,
        "age_seconds": age_seconds,
    }


def build_project_glance_index(projects: Iterable[Mapping], *, now=None, stale_seconds: int = 3600) -> dict:
    current = _now(now)
    normalized = [normalize_project_glance(item, now=current, stale_seconds=stale_seconds) for item in projects]
    ids = [item["project_id"] for item in normalized]
    repos = [item["repository"] for item in normalized]
    if len(ids) != len(set(ids)):
        raise ProjectGlanceError("project_id values must be unique")
    if len(repos) != len(set(repos)):
        raise ProjectGlanceError("repository values must be unique")
    return {
        "schema": SCHEMA,
        "generated_at_utc": current.isoformat().replace("+00:00", "Z"),
        "authority": "READ_ONLY_DERIVED_CACHE",
        "summary": {
            "projects": len(normalized),
            "executing": sum(1 for p in normalized if p["status"] == "EXECUTING"),
            "waiting": sum(1 for p in normalized if p["status"] == "WAITING"),
            "blocked": sum(1 for p in normalized if p["status"] == "BLOCKED"),
            "idle_ready": sum(1 for p in normalized if p["status"] == "IDLE_READY"),
            "paused": sum(1 for p in normalized if p["status"] == "PAUSED"),
            "stale": sum(1 for p in normalized if p["status"] == "STALE"),
        },
        "projects": sorted(normalized, key=lambda item: item["project_id"]),
    }


def render_project_glance(snapshot: Mapping) -> str:
    if snapshot.get("schema") != SCHEMA:
        raise ProjectGlanceError("unsupported project glance index schema")
    summary = snapshot["summary"]
    lines = [
        f"Projects {summary['projects']} · executing {summary['executing']} · blocked {summary['blocked']} · stale {summary['stale']}",
        "",
        "| Project | State | Focus | Blocker | Next | Freshness |",
        "|---|---|---|---|---|---|",
    ]
    for p in snapshot["projects"]:
        lines.append(
            f"| `{p['project_id']}` | {p['status']} | {p['current_focus']} | "
            f"{p['blocker_summary']} | {p['next_action']} | {p['freshness']} |"
        )
    return "\n".join(lines) + "\n"
