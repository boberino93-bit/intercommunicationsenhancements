from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


AGENT_STATES = {"ACTIVE_SLOT", "STANDBY_READ_ONLY"}
ROLES = {"PRIMARY", "MANAGER", "RESEARCH"}
STAGE_TARGETS = (15, 30, 60, 100)


class SwarmScaleError(ValueError):
    pass


@dataclass(frozen=True)
class ScaleProfile:
    target_population: int = 100
    primary_per_project: int = 1
    manager_per_project: int = 1
    specialist_cap_per_project: int = 8
    provider_max_inflight: int = 1
    provider_min_start_interval_seconds: int = 30

    def __post_init__(self):
        for field_name in (
            "target_population",
            "primary_per_project",
            "manager_per_project",
            "specialist_cap_per_project",
            "provider_max_inflight",
            "provider_min_start_interval_seconds",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise SwarmScaleError(f"{field_name} must be a positive integer")


@dataclass(frozen=True)
class ScaleStage:
    population: int
    provider_max_inflight: int
    provider_min_start_interval_seconds: int


STAGES = {
    15: ScaleStage(15, 2, 10),
    30: ScaleStage(30, 2, 8),
    60: ScaleStage(60, 3, 6),
    100: ScaleStage(100, 4, 5),
}


def _normalized_projects(project_ids: Sequence[str]) -> tuple[str, ...]:
    if not project_ids:
        raise SwarmScaleError("at least one project is required")
    normalized = tuple(str(item).strip() for item in project_ids)
    if any(not item for item in normalized):
        raise SwarmScaleError("project ids must be non-empty")
    if len(set(normalized)) != len(normalized):
        raise SwarmScaleError("duplicate project ids are not allowed")
    return tuple(sorted(normalized))


def stage_for_population(population: int) -> ScaleStage:
    if population not in STAGES:
        raise SwarmScaleError("unsupported staged population")
    return STAGES[population]


def launch_window_seconds(population: int, min_start_interval_seconds: int) -> int:
    if population <= 0 or min_start_interval_seconds <= 0:
        raise SwarmScaleError("population and interval must be positive")
    return max(0, population - 1) * min_start_interval_seconds


def build_population_plan(
    project_ids: Sequence[str],
    *,
    target_population: int = 100,
    specialist_cap_per_project: int = 8,
) -> list[dict[str, object]]:
    projects = _normalized_projects(project_ids)
    if target_population <= 0 or specialist_cap_per_project <= 0:
        raise SwarmScaleError("target population and specialist cap must be positive")

    fixed_roles = len(projects) * 2
    if target_population < fixed_roles:
        raise SwarmScaleError("target population cannot cover one PRIMARY and one MANAGER per project")

    records: list[dict[str, object]] = []
    for project_id in projects:
        records.append({
            "agent_id": f"scale-{project_id}-primary-01",
            "project_id": project_id,
            "role": "PRIMARY",
            "state": "ACTIVE_SLOT",
            "mutation_eligible": False,
        })
        records.append({
            "agent_id": f"scale-{project_id}-manager-01",
            "project_id": project_id,
            "role": "MANAGER",
            "state": "ACTIVE_SLOT",
            "mutation_eligible": False,
        })

    remaining = target_population - fixed_roles
    active_research_capacity = len(projects) * specialist_cap_per_project
    active_research = min(remaining, active_research_capacity)

    for index in range(active_research):
        project_id = projects[index % len(projects)]
        project_ordinal = index // len(projects) + 1
        records.append({
            "agent_id": f"scale-{project_id}-research-{project_ordinal:02d}",
            "project_id": project_id,
            "role": "RESEARCH",
            "state": "ACTIVE_SLOT",
            "mutation_eligible": False,
        })

    standby = remaining - active_research
    for index in range(standby):
        project_id = projects[index % len(projects)]
        project_ordinal = specialist_cap_per_project + (index // len(projects)) + 1
        records.append({
            "agent_id": f"scale-{project_id}-research-{project_ordinal:02d}",
            "project_id": project_id,
            "role": "RESEARCH",
            "state": "STANDBY_READ_ONLY",
            "mutation_eligible": False,
        })

    return records


def summarize_population(plan: Sequence[Mapping[str, object]]) -> dict[str, object]:
    agent_ids = [str(item.get("agent_id", "")) for item in plan]
    if len(agent_ids) != len(set(agent_ids)):
        raise SwarmScaleError("agent ids must be unique")
    active = sum(item.get("state") == "ACTIVE_SLOT" for item in plan)
    standby = sum(item.get("state") == "STANDBY_READ_ONLY" for item in plan)
    roles = {role: 0 for role in ROLES}
    by_project: dict[str, dict[str, int]] = {}
    for item in plan:
        role = str(item.get("role"))
        state = str(item.get("state"))
        project_id = str(item.get("project_id", ""))
        if role not in ROLES or state not in AGENT_STATES or not project_id:
            raise SwarmScaleError("invalid population-plan record")
        roles[role] += 1
        bucket = by_project.setdefault(project_id, {"PRIMARY": 0, "MANAGER": 0, "RESEARCH_ACTIVE": 0, "RESEARCH_STANDBY": 0})
        if role == "RESEARCH":
            bucket["RESEARCH_ACTIVE" if state == "ACTIVE_SLOT" else "RESEARCH_STANDBY"] += 1
        else:
            bucket[role] += 1
    return {
        "population": len(plan),
        "active_slots": active,
        "standby_read_only": standby,
        "roles": roles,
        "projects": by_project,
    }


def validate_population_plan(
    plan: Sequence[Mapping[str, object]],
    *,
    project_ids: Sequence[str],
    target_population: int,
    specialist_cap_per_project: int,
) -> bool:
    projects = _normalized_projects(project_ids)
    if len(plan) != target_population:
        return False
    try:
        summary = summarize_population(plan)
    except SwarmScaleError:
        return False
    if set(summary["projects"].keys()) != set(projects):
        return False
    for project_id in projects:
        bucket = summary["projects"][project_id]
        if bucket["PRIMARY"] != 1 or bucket["MANAGER"] != 1:
            return False
        if bucket["RESEARCH_ACTIVE"] > specialist_cap_per_project:
            return False
    if any(bool(item.get("mutation_eligible")) for item in plan):
        return False
    return True


_REQUIRED_ZERO = (
    "unauthorized_mutations",
    "cross_project_write_violations",
    "duplicate_commits",
    "unresolved_leases",
    "stale_handoffs",
    "lost_agents",
    "unaccounted_work_items",
)


def evaluate_stage_gate(*, expected_agents: int, metrics: Mapping[str, object]) -> dict[str, object]:
    if expected_agents <= 0:
        raise SwarmScaleError("expected_agents must be positive")
    failures: list[str] = []
    if int(metrics.get("ready_agents", -1)) != expected_agents:
        failures.append("READY_AGENT_COUNT_MISMATCH")
    if int(metrics.get("accounted_agents", -1)) != expected_agents:
        failures.append("ACCOUNTED_AGENT_COUNT_MISMATCH")
    for key in _REQUIRED_ZERO:
        if int(metrics.get(key, -1)) != 0:
            failures.append(key.upper())
    for key in ("completion_integrity_pass", "ledger_chain_valid", "manager_backpressure_recovered"):
        if metrics.get(key) is not True:
            failures.append(key.upper())
    return {
        "schema": "org-agent-mesh/swarm-scale-stage-gate/v1",
        "expected_agents": expected_agents,
        "passed": not failures,
        "failures": failures,
    }


def next_stage(completed_population: int) -> int | None:
    for target in STAGE_TARGETS:
        if target > completed_population:
            return target
    return None
