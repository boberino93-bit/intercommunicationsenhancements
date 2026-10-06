from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Mapping, Sequence

from .capacity import CAPACITY_STATES, signal_is_stale

EXPECTED_PROJECTS = (
    "ai-behaviour-control-lab",
    "benefitflow",
    "duo-open",
    "fold7-power-lab",
    "intercommunicationsenhancements",
    "warp-propulsion-lab",
    "xrp-thesis",
)

PROJECT_ALIASES = {"xrpthesis": "xrp-thesis"}
STAGE15_CAPACITY_STATES = {"GREEN"}
DEFAULT_MAX_CAPACITY_AGE_SECONDS = 900
DEFAULT_MAX_OPERATIONS_AGE_SECONDS = 1800
DEFAULT_MAX_PERSISTENCE_AGE_SECONDS = 1800
DEFAULT_MAX_FUTURE_SKEW_SECONDS = 5


class Stage15PreflightError(ValueError):
    pass


def _parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise Stage15PreflightError("TIMESTAMP_REQUIRED")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise Stage15PreflightError("TIMESTAMP_TIMEZONE_REQUIRED")
    return parsed.astimezone(timezone.utc)


def canonical_project_id(project_id: str) -> str:
    value = str(project_id or "").strip()
    if not value:
        raise Stage15PreflightError("PROJECT_ID_REQUIRED")
    return PROJECT_ALIASES.get(value, value)


def _timestamp_from_observation(observation: Mapping[str, object]) -> str:
    for key in ("measured_at_utc", "observed_at_utc", "generated_at_utc", "timestamp_utc"):
        value = observation.get(key)
        if isinstance(value, str) and value:
            return value
    raise Stage15PreflightError("OPERATIONS_TIMESTAMP_REQUIRED")


def validate_capacity_signal(
    signal: Mapping[str, object],
    *,
    expected_project_id: str,
    expected_repository_identity: str,
    now_utc: str,
    max_age_seconds: int = DEFAULT_MAX_CAPACITY_AGE_SECONDS,
    max_future_skew_seconds: int = DEFAULT_MAX_FUTURE_SKEW_SECONDS,
) -> dict[str, object]:
    if signal.get("schema") != "org-agent-mesh/capacity-signal/v1":
        raise Stage15PreflightError("CAPACITY_SCHEMA_MISMATCH")
    if signal.get("project_id") != expected_project_id:
        raise Stage15PreflightError("CAPACITY_PROJECT_MISMATCH")
    if signal.get("repository_identity") != expected_repository_identity:
        raise Stage15PreflightError("CAPACITY_REPOSITORY_MISMATCH")
    measured = _parse_utc(str(signal.get("measured_at_utc", "")))
    now = _parse_utc(now_utc)
    age = (now - measured).total_seconds()
    if age < -max_future_skew_seconds:
        raise Stage15PreflightError("CAPACITY_SIGNAL_FROM_FUTURE")
    if signal_is_stale(str(signal["measured_at_utc"]), now_utc, max_age_seconds=max_age_seconds):
        raise Stage15PreflightError("CAPACITY_SIGNAL_STALE")
    state = str(signal.get("overall_state", "UNKNOWN"))
    if state not in CAPACITY_STATES:
        raise Stage15PreflightError("CAPACITY_STATE_INVALID")
    if state not in STAGE15_CAPACITY_STATES:
        raise Stage15PreflightError(f"CAPACITY_NOT_ADMISSIBLE:{state}")
    return {
        "project_id": expected_project_id,
        "repository_identity": expected_repository_identity,
        "observed_revision": signal.get("observed_revision"),
        "measured_at_utc": signal.get("measured_at_utc"),
        "age_seconds": max(0, int(age)),
        "overall_state": state,
        "capacity_admission": True,
    }


def normalize_operations_observation(
    observation: Mapping[str, object],
    *,
    expected_project_id: str,
    now_utc: str,
    max_age_seconds: int = DEFAULT_MAX_OPERATIONS_AGE_SECONDS,
    max_future_skew_seconds: int = DEFAULT_MAX_FUTURE_SKEW_SECONDS,
) -> dict[str, object]:
    raw_id = str(observation.get("project_id", ""))
    canonical = canonical_project_id(raw_id)
    if canonical != expected_project_id:
        raise Stage15PreflightError("OPERATIONS_PROJECT_MISMATCH")
    observed_at = _timestamp_from_observation(observation)
    observed = _parse_utc(observed_at)
    now = _parse_utc(now_utc)
    age = (now - observed).total_seconds()
    if age < -max_future_skew_seconds:
        raise Stage15PreflightError("OPERATIONS_OBSERVATION_FROM_FUTURE")
    if age > max_age_seconds:
        raise Stage15PreflightError("OPERATIONS_OBSERVATION_STALE")
    return {
        "project_id": canonical,
        "observed_project_id": raw_id,
        "legacy_alias_used": raw_id != canonical,
        "mesh_normalization_complete": bool(observation.get("normalized", False)) if raw_id == canonical else False,
        "observed_at_utc": observed_at,
        "age_seconds": max(0, int(age)),
        "status": observation.get("status", observation.get("run_state", "UNKNOWN")),
    }


def validate_persistence_health(
    health: Mapping[str, object],
    *,
    expected_project_id: str,
    now_utc: str,
    max_age_seconds: int = DEFAULT_MAX_PERSISTENCE_AGE_SECONDS,
    max_future_skew_seconds: int = DEFAULT_MAX_FUTURE_SKEW_SECONDS,
) -> dict[str, object]:
    if not health:
        raise Stage15PreflightError("PERSISTENCE_HEALTH_MISSING")
    if health.get("schema") != "org-agent-mesh/persistence-health/v1":
        raise Stage15PreflightError("PERSISTENCE_HEALTH_SCHEMA_MISMATCH")
    if health.get("project_id") != expected_project_id:
        raise Stage15PreflightError("PERSISTENCE_PROJECT_MISMATCH")
    observed_at = str(health.get("reconciled_at_utc", ""))
    observed = _parse_utc(observed_at)
    now = _parse_utc(now_utc)
    age = (now - observed).total_seconds()
    if age < -max_future_skew_seconds:
        raise Stage15PreflightError("PERSISTENCE_HEALTH_FROM_FUTURE")
    if age > max_age_seconds:
        raise Stage15PreflightError("PERSISTENCE_HEALTH_STALE")
    for key in ("route_normalized", "forum_verified", "github_backup_verified", "zero_loss"):
        if health.get(key) is not True:
            raise Stage15PreflightError(f"PERSISTENCE_{key.upper()}_REQUIRED")
    for key in ("single_sink_count", "digest_mismatch_count", "conflict_count"):
        value = health.get(key)
        if not isinstance(value, int) or value < 0:
            raise Stage15PreflightError(f"PERSISTENCE_{key.upper()}_INVALID")
        if value != 0:
            raise Stage15PreflightError(f"PERSISTENCE_{key.upper()}_NONZERO")
    if health.get("authority_conveyed") is not False:
        raise Stage15PreflightError("PERSISTENCE_HEALTH_CANNOT_CONVEY_AUTHORITY")
    result = dict(health)
    result["age_seconds"] = max(0, int(age))
    result["persistence_admission"] = True
    return result


@dataclass(frozen=True)
class Stage15ProjectEvidence:
    project_id: str
    repository_identity: str
    source_revision: str
    capacity: Mapping[str, object]
    operations: Mapping[str, object]
    kernel_preflight_pass: bool
    persistence: Mapping[str, object]


@dataclass(frozen=True)
class Stage15EvidenceEnvelope:
    schema: str
    global_run_id: str
    stage_population: int
    generated_at_utc: str
    expected_projects: tuple[str, ...]
    projects: tuple[Mapping[str, object], ...]
    contract_ready: bool
    preflight_ready: bool
    stage_passed: bool
    authority_conveyed: bool
    launch_authorized: bool
    blockers: tuple[str, ...]
    evidence_digest: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def assemble_stage15_evidence(
    *,
    global_run_id: str,
    now_utc: str,
    project_evidence: Sequence[Stage15ProjectEvidence],
    expected_projects: Sequence[str] = EXPECTED_PROJECTS,
) -> Stage15EvidenceEnvelope:
    if not global_run_id:
        raise Stage15PreflightError("GLOBAL_RUN_ID_REQUIRED")
    _parse_utc(now_utc)
    expected = tuple(sorted(expected_projects))
    if len(expected) != 7 or len(set(expected)) != 7:
        raise Stage15PreflightError("EXACT_SEVEN_PROJECT_SET_REQUIRED")
    evidence_by_project = {item.project_id: item for item in project_evidence}
    if len(evidence_by_project) != len(project_evidence):
        raise Stage15PreflightError("DUPLICATE_PROJECT_EVIDENCE")
    if set(evidence_by_project) != set(expected):
        raise Stage15PreflightError("PROJECT_EVIDENCE_SET_MISMATCH")

    projects: list[dict[str, object]] = []
    blockers: list[str] = []
    for project_id in expected:
        item = evidence_by_project[project_id]
        capacity = validate_capacity_signal(
            item.capacity,
            expected_project_id=project_id,
            expected_repository_identity=item.repository_identity,
            now_utc=now_utc,
        )
        operations = normalize_operations_observation(
            item.operations,
            expected_project_id=project_id,
            now_utc=now_utc,
        )
        try:
            persistence = validate_persistence_health(
                item.persistence,
                expected_project_id=project_id,
                now_utc=now_utc,
            )
        except Stage15PreflightError as exc:
            persistence = {
                "project_id": project_id,
                "persistence_admission": False,
                "error": str(exc),
            }
            blockers.append(f"{project_id}:{exc}")
        if not operations["mesh_normalization_complete"]:
            blockers.append(f"{project_id}:MESH_NORMALIZATION_INCOMPLETE")
        if not item.kernel_preflight_pass:
            blockers.append(f"{project_id}:KERNEL_PREFLIGHT_FAILED")
        projects.append({
            "project_id": project_id,
            "repository_identity": item.repository_identity,
            "source_revision": item.source_revision,
            "capacity": capacity,
            "operations": operations,
            "persistence": persistence,
            "kernel_preflight_pass": bool(item.kernel_preflight_pass),
        })

    canonical_payload = {
        "schema": "org-agent-mesh/stage15-evidence/v2",
        "global_run_id": global_run_id,
        "stage_population": 15,
        "generated_at_utc": now_utc,
        "expected_projects": list(expected),
        "projects": projects,
        "contract_ready": True,
        "preflight_ready": not blockers,
        "stage_passed": False,
        "authority_conveyed": False,
        "launch_authorized": False,
        "blockers": sorted(blockers),
    }
    digest = "sha256:" + sha256(json.dumps(canonical_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return Stage15EvidenceEnvelope(
        schema=canonical_payload["schema"],
        global_run_id=global_run_id,
        stage_population=15,
        generated_at_utc=now_utc,
        expected_projects=expected,
        projects=tuple(projects),
        contract_ready=True,
        preflight_ready=not blockers,
        stage_passed=False,
        authority_conveyed=False,
        launch_authorized=False,
        blockers=tuple(sorted(blockers)),
        evidence_digest=digest,
    )
