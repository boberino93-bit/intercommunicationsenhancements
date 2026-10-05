from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Mapping, Sequence

CAPACITY_STATES = {"GREEN", "AMBER", "PRESERVE", "RESERVE_ONLY", "EXHAUSTED", "UNKNOWN"}
RUN_STATES = {"ACTIVE", "READY", "CONVERGING", "DEGRADED_READ_ONLY", "COMPLETE"}
ACTIONS = {"HOLD", "REQUEST_ADMIT", "REQUEST_DRAIN_TO_STANDBY"}


class SystemScalerError(ValueError):
    pass


@dataclass(frozen=True)
class ScalerConfig:
    project_count: int = 7
    specialist_cap_per_project: int = 8
    healthy_windows_required: int = 3
    cooldown_windows: int = 2
    manager_queue_soft_limit: int = 8
    manager_queue_hard_limit: int = 15
    max_global_admissions_per_cycle: int = 7
    max_project_admissions_per_cycle: int = 1

    def __post_init__(self) -> None:
        for name in (
            "project_count", "specialist_cap_per_project", "healthy_windows_required",
            "cooldown_windows", "manager_queue_soft_limit", "manager_queue_hard_limit",
            "max_global_admissions_per_cycle", "max_project_admissions_per_cycle",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise SystemScalerError(f"{name} must be a positive integer")
        if self.manager_queue_soft_limit >= self.manager_queue_hard_limit:
            raise SystemScalerError("manager soft limit must be below hard limit")


@dataclass(frozen=True)
class ProjectScaleSignal:
    project_id: str
    active_research: int
    standby_research: int
    manager_queue_depth: int
    capacity_state: str
    collisions: int = 0
    unresolved_leases: int = 0
    completion_integrity_pass: bool = True
    ledger_chain_valid: bool = True
    handoff_fresh: bool = True
    unauthorized_mutations: int = 0
    cross_project_write_violations: int = 0
    run_state: str = "ACTIVE"
    idle_lease_free_agent_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.project_id:
            raise SystemScalerError("project_id is required")
        for name in (
            "active_research", "standby_research", "manager_queue_depth", "collisions",
            "unresolved_leases", "unauthorized_mutations", "cross_project_write_violations",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise SystemScalerError(f"{name} must be a non-negative integer")
        if self.capacity_state not in CAPACITY_STATES:
            raise SystemScalerError("invalid capacity_state")
        if self.run_state not in RUN_STATES:
            raise SystemScalerError("invalid run_state")
        if len(set(self.idle_lease_free_agent_ids)) != len(self.idle_lease_free_agent_ids):
            raise SystemScalerError("duplicate drain candidates")


@dataclass(frozen=True)
class ScalerMemory:
    healthy_windows: Mapping[str, int] = field(default_factory=dict)
    cooldown_remaining: Mapping[str, int] = field(default_factory=dict)
    fairness_cursor: int = 0


@dataclass(frozen=True)
class ScaleDecision:
    action: str
    project_id: str | None
    agent_id: str | None
    reason: str
    authority_conveyed: bool = False
    direct_termination_allowed: bool = False

    def __post_init__(self) -> None:
        if self.action not in ACTIONS:
            raise SystemScalerError("invalid action")
        if self.authority_conveyed or self.direct_termination_allowed:
            raise SystemScalerError("scaler may not convey authority or terminate agents")

    def as_dict(self) -> dict[str, object]:
        return {
            "action": self.action,
            "project_id": self.project_id,
            "agent_id": self.agent_id,
            "reason": self.reason,
            "authority_conveyed": False,
            "direct_termination_allowed": False,
        }


def stage_research_ceiling(stage_population: int, cfg: ScalerConfig) -> int:
    if stage_population not in {15, 30, 60, 100}:
        raise SystemScalerError("unsupported stage population")
    fixed_roles = cfg.project_count * 2
    return max(0, min(cfg.project_count * cfg.specialist_cap_per_project, stage_population - fixed_roles))


def _hard_freeze(signal: ProjectScaleSignal) -> str | None:
    if signal.capacity_state == "UNKNOWN":
        return "UNKNOWN_CAPACITY"
    if signal.run_state == "DEGRADED_READ_ONLY":
        return "DEGRADED_READ_ONLY"
    if signal.unauthorized_mutations:
        return "UNAUTHORIZED_MUTATION_EVIDENCE"
    if signal.cross_project_write_violations:
        return "CROSS_PROJECT_WRITE_VIOLATION"
    if not signal.handoff_fresh:
        return "STALE_HANDOFF"
    if not signal.ledger_chain_valid:
        return "LEDGER_CHAIN_INVALID"
    if not signal.completion_integrity_pass:
        return "COMPLETION_INTEGRITY_FAILURE"
    if signal.unresolved_leases:
        return "UNRESOLVED_LEASE"
    return None


def _healthy(signal: ProjectScaleSignal, cfg: ScalerConfig) -> bool:
    return (
        _hard_freeze(signal) is None
        and signal.capacity_state == "GREEN"
        and signal.manager_queue_depth < cfg.manager_queue_soft_limit
        and signal.collisions == 0
        and signal.run_state in {"ACTIVE", "READY"}
    )


def update_memory(signals: Sequence[ProjectScaleSignal], memory: ScalerMemory, cfg: ScalerConfig) -> ScalerMemory:
    healthy: dict[str, int] = {}
    cooldown: dict[str, int] = {}
    for signal in signals:
        prior = int(memory.healthy_windows.get(signal.project_id, 0))
        healthy[signal.project_id] = prior + 1 if _healthy(signal, cfg) else 0
        cooldown[signal.project_id] = max(0, int(memory.cooldown_remaining.get(signal.project_id, 0)) - 1)
    return ScalerMemory(healthy_windows=healthy, cooldown_remaining=cooldown, fairness_cursor=memory.fairness_cursor)


def decide(
    *,
    stage_population: int,
    signals: Sequence[ProjectScaleSignal],
    memory: ScalerMemory | None = None,
    cfg: ScalerConfig | None = None,
) -> dict[str, object]:
    cfg = cfg or ScalerConfig()
    memory = update_memory(signals, memory or ScalerMemory(), cfg)
    if len({s.project_id for s in signals}) != len(signals):
        raise SystemScalerError("duplicate project signals")
    if len(signals) != cfg.project_count:
        raise SystemScalerError("all registered project signals are required")

    ordered = sorted(signals, key=lambda s: s.project_id)
    decisions: list[ScaleDecision] = []

    # Fail closed on integrity/unknown-state signals before considering any scale-up.
    freezes = [(s, _hard_freeze(s)) for s in ordered]
    if any(reason for _, reason in freezes):
        reasons = ",".join(f"{s.project_id}:{reason}" for s, reason in freezes if reason)
        decisions.append(ScaleDecision("HOLD", None, None, f"GLOBAL_FREEZE:{reasons}"))
        return _result(stage_population, ordered, memory, decisions, cfg)

    # Hard pressure may request graceful drain, but only for explicitly idle/lease-free candidates.
    for signal in ordered:
        hard_pressure = signal.manager_queue_depth >= cfg.manager_queue_hard_limit or signal.capacity_state in {"RESERVE_ONLY", "EXHAUSTED"}
        if hard_pressure and signal.idle_lease_free_agent_ids:
            decisions.append(ScaleDecision(
                "REQUEST_DRAIN_TO_STANDBY",
                signal.project_id,
                sorted(signal.idle_lease_free_agent_ids)[0],
                "HARD_PRESSURE_GRACEFUL_DRAIN",
            ))

    if decisions:
        return _result(stage_population, ordered, memory, decisions, cfg)

    total_active = sum(s.active_research for s in ordered)
    ceiling = stage_research_ceiling(stage_population, cfg)
    available = max(0, ceiling - total_active)
    if available == 0:
        decisions.append(ScaleDecision("HOLD", None, None, "STAGE_RESEARCH_CEILING_REACHED"))
        return _result(stage_population, ordered, memory, decisions, cfg)

    if any(s.manager_queue_depth >= cfg.manager_queue_soft_limit or s.capacity_state in {"AMBER", "PRESERVE"} or s.collisions for s in ordered):
        decisions.append(ScaleDecision("HOLD", None, None, "SOFT_PRESSURE_OR_COLLISION"))
        return _result(stage_population, ordered, memory, decisions, cfg)

    eligible = [
        s for s in ordered
        if s.standby_research > 0
        and s.active_research < cfg.specialist_cap_per_project
        and memory.healthy_windows.get(s.project_id, 0) >= cfg.healthy_windows_required
        and memory.cooldown_remaining.get(s.project_id, 0) == 0
    ]
    if not eligible:
        decisions.append(ScaleDecision("HOLD", None, None, "HYSTERESIS_OR_CAPACITY_NOT_READY"))
        return _result(stage_population, ordered, memory, decisions, cfg)

    cursor = memory.fairness_cursor % len(eligible)
    rotated = eligible[cursor:] + eligible[:cursor]
    slots = min(available, cfg.max_global_admissions_per_cycle, len(rotated))
    chosen = rotated[:slots]
    cooldown = dict(memory.cooldown_remaining)
    for signal in chosen:
        decisions.append(ScaleDecision("REQUEST_ADMIT", signal.project_id, None, "SUSTAINED_HEALTHY_CAPACITY"))
        cooldown[signal.project_id] = cfg.cooldown_windows
    memory = ScalerMemory(
        healthy_windows=dict(memory.healthy_windows),
        cooldown_remaining=cooldown,
        fairness_cursor=(memory.fairness_cursor + len(chosen)) % max(1, len(eligible)),
    )
    return _result(stage_population, ordered, memory, decisions, cfg)


def _result(stage_population: int, signals: Sequence[ProjectScaleSignal], memory: ScalerMemory, decisions: Sequence[ScaleDecision], cfg: ScalerConfig) -> dict[str, object]:
    payload = {
        "schema": "org-agent-mesh/system-scaler-decision/v1",
        "stage_population": stage_population,
        "research_ceiling": stage_research_ceiling(stage_population, cfg),
        "active_research": sum(s.active_research for s in signals),
        "decisions": [d.as_dict() for d in decisions],
        "memory": {
            "healthy_windows": dict(sorted(memory.healthy_windows.items())),
            "cooldown_remaining": dict(sorted(memory.cooldown_remaining.items())),
            "fairness_cursor": memory.fairness_cursor,
        },
        "authority_conveyed": False,
        "direct_termination_allowed": False,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["decision_digest"] = "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()
    return payload
