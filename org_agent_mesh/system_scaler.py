from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping, Sequence

CAPACITY_STATES = {"GREEN", "AMBER", "PRESERVE", "RESERVE_ONLY", "EXHAUSTED", "UNKNOWN"}
RUN_STATES = {"ACTIVE", "READY", "CONVERGING", "DEGRADED_READ_ONLY", "COMPLETE"}
ACTIONS = {"HOLD", "REQUEST_ADMIT", "REQUEST_DRAIN_TO_STANDBY"}
DEFAULT_PROJECTS = (
    "ai-behaviour-control-lab",
    "benefitflow",
    "duo-open",
    "fold7-power-lab",
    "intercommunicationsenhancements",
    "warp-propulsion-lab",
    "xrp-thesis",
)


class SystemScalerError(ValueError):
    pass


def _parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise SystemScalerError("UTC timestamp must be a non-empty string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise SystemScalerError("UTC timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class ScalerConfig:
    project_count: int = 7
    expected_project_ids: tuple[str, ...] = DEFAULT_PROJECTS
    specialist_cap_per_project: int = 8
    healthy_windows_required: int = 3
    cooldown_windows: int = 2
    manager_queue_soft_limit: int = 8
    manager_queue_hard_limit: int = 15
    max_global_admissions_per_cycle: int = 7
    max_project_admissions_per_cycle: int = 1
    max_global_drains_per_cycle: int = 7
    max_signal_age_seconds: int = 120
    max_future_skew_seconds: int = 5

    def __post_init__(self) -> None:
        for name in (
            "project_count", "specialist_cap_per_project", "healthy_windows_required",
            "cooldown_windows", "manager_queue_soft_limit", "manager_queue_hard_limit",
            "max_global_admissions_per_cycle", "max_project_admissions_per_cycle",
            "max_global_drains_per_cycle", "max_signal_age_seconds", "max_future_skew_seconds",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise SystemScalerError(f"{name} must be a positive integer")
        if self.manager_queue_soft_limit >= self.manager_queue_hard_limit:
            raise SystemScalerError("manager soft limit must be below hard limit")
        normalized = tuple(sorted(str(p).strip() for p in self.expected_project_ids))
        if len(normalized) != self.project_count or len(set(normalized)) != len(normalized) or any(not p for p in normalized):
            raise SystemScalerError("expected_project_ids must contain exactly project_count unique ids")
        object.__setattr__(self, "expected_project_ids", normalized)


@dataclass(frozen=True)
class ProjectScaleSignal:
    project_id: str
    run_id: str
    measured_at_utc: str
    active_research: int
    standby_research: int
    queued_eligible_work: int
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
        if not self.project_id or not self.run_id:
            raise SystemScalerError("project_id and run_id are required")
        _parse_utc(self.measured_at_utc)
        for name in (
            "active_research", "standby_research", "queued_eligible_work", "manager_queue_depth", "collisions",
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
    if signal.capacity_state == "EXHAUSTED":
        return "EXHAUSTED_CAPACITY_CHECKPOINT_UNSAFE"
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


def _telemetry_freeze(signal: ProjectScaleSignal, *, run_id: str, now: datetime, cfg: ScalerConfig) -> str | None:
    if signal.run_id != run_id:
        return "RUN_ID_MISMATCH"
    measured = _parse_utc(signal.measured_at_utc)
    age = (now - measured).total_seconds()
    if age > cfg.max_signal_age_seconds:
        return "STALE_TELEMETRY"
    if age < -cfg.max_future_skew_seconds:
        return "FUTURE_TELEMETRY"
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


def _signal_dict(signal: ProjectScaleSignal) -> dict[str, object]:
    return {
        "project_id": signal.project_id,
        "run_id": signal.run_id,
        "measured_at_utc": signal.measured_at_utc,
        "active_research": signal.active_research,
        "standby_research": signal.standby_research,
        "queued_eligible_work": signal.queued_eligible_work,
        "manager_queue_depth": signal.manager_queue_depth,
        "capacity_state": signal.capacity_state,
        "collisions": signal.collisions,
        "unresolved_leases": signal.unresolved_leases,
        "completion_integrity_pass": signal.completion_integrity_pass,
        "ledger_chain_valid": signal.ledger_chain_valid,
        "handoff_fresh": signal.handoff_fresh,
        "unauthorized_mutations": signal.unauthorized_mutations,
        "cross_project_write_violations": signal.cross_project_write_violations,
        "run_state": signal.run_state,
        "idle_lease_free_agent_ids": list(signal.idle_lease_free_agent_ids),
    }


def _input_digest(*, stage_population: int, run_id: str, now_utc: str, signals: Sequence[ProjectScaleSignal], cfg: ScalerConfig) -> str:
    payload = {
        "stage_population": stage_population,
        "run_id": run_id,
        "now_utc": now_utc,
        "signals": [_signal_dict(s) for s in sorted(signals, key=lambda item: item.project_id)],
        "expected_project_ids": list(cfg.expected_project_ids),
        "specialist_cap_per_project": cfg.specialist_cap_per_project,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()


def decide(
    *,
    stage_population: int,
    run_id: str,
    now_utc: str,
    signals: Sequence[ProjectScaleSignal],
    memory: ScalerMemory | None = None,
    cfg: ScalerConfig | None = None,
) -> dict[str, object]:
    cfg = cfg or ScalerConfig()
    original_memory = memory or ScalerMemory()
    now = _parse_utc(now_utc)
    if not run_id:
        raise SystemScalerError("run_id is required")
    if len({s.project_id for s in signals}) != len(signals):
        raise SystemScalerError("duplicate project signals")
    if set(s.project_id for s in signals) != set(cfg.expected_project_ids):
        raise SystemScalerError("exact registered project signal set is required")

    ordered = sorted(signals, key=lambda s: s.project_id)
    input_digest = _input_digest(stage_population=stage_population, run_id=run_id, now_utc=now_utc, signals=ordered, cfg=cfg)
    telemetry_freezes = [(s, _telemetry_freeze(s, run_id=run_id, now=now, cfg=cfg)) for s in ordered]
    if any(reason for _, reason in telemetry_freezes):
        reasons = ",".join(f"{s.project_id}:{reason}" for s, reason in telemetry_freezes if reason)
        return _result(stage_population, run_id, input_digest, ordered, original_memory, [ScaleDecision("HOLD", None, None, f"GLOBAL_FREEZE:{reasons}")], cfg)

    hard_freezes = [(s, _hard_freeze(s)) for s in ordered]
    if any(reason for _, reason in hard_freezes):
        reasons = ",".join(f"{s.project_id}:{reason}" for s, reason in hard_freezes if reason)
        return _result(stage_population, run_id, input_digest, ordered, original_memory, [ScaleDecision("HOLD", None, None, f"GLOBAL_FREEZE:{reasons}")], cfg)

    memory = update_memory(ordered, original_memory, cfg)
    total_active = sum(s.active_research for s in ordered)
    ceiling = stage_research_ceiling(stage_population, cfg)

    # Stage contraction takes precedence. Drain only idle/lease-free agents and admit nothing
    # until active research is at or below the new stage ceiling.
    excess = max(0, total_active - ceiling)
    if excess:
        candidates: list[tuple[str, str]] = []
        for signal in ordered:
            for agent_id in sorted(signal.idle_lease_free_agent_ids):
                candidates.append((signal.project_id, agent_id))
        drain_count = min(excess, cfg.max_global_drains_per_cycle, len(candidates))
        if drain_count == 0:
            return _result(stage_population, run_id, input_digest, ordered, memory, [ScaleDecision("HOLD", None, None, f"STAGE_CONTRACTION_BLOCKED:EXCESS={excess}")], cfg)
        decisions = [ScaleDecision("REQUEST_DRAIN_TO_STANDBY", project_id, agent_id, "STAGE_CONTRACTION_GRACEFUL_DRAIN") for project_id, agent_id in candidates[:drain_count]]
        return _result(stage_population, run_id, input_digest, ordered, memory, decisions, cfg, remaining_excess=max(0, excess - drain_count))

    # Any hard pressure is globally admission-blocking. RESERVE_ONLY or manager hard pressure
    # may request a graceful drain if one is safe; EXHAUSTED was already frozen above because
    # checkpoint/handoff persistence cannot be assumed available.
    pressure = [s for s in ordered if s.manager_queue_depth >= cfg.manager_queue_hard_limit or s.capacity_state == "RESERVE_ONLY"]
    if pressure:
        drains: list[ScaleDecision] = []
        for signal in pressure:
            if signal.idle_lease_free_agent_ids:
                drains.append(ScaleDecision("REQUEST_DRAIN_TO_STANDBY", signal.project_id, sorted(signal.idle_lease_free_agent_ids)[0], "HARD_PRESSURE_GRACEFUL_DRAIN"))
            if len(drains) >= cfg.max_global_drains_per_cycle:
                break
        if drains:
            return _result(stage_population, run_id, input_digest, ordered, memory, drains, cfg)
        return _result(stage_population, run_id, input_digest, ordered, memory, [ScaleDecision("HOLD", None, None, "HARD_PRESSURE_NO_SAFE_DRAIN")], cfg)

    available = max(0, ceiling - total_active)
    if available == 0:
        return _result(stage_population, run_id, input_digest, ordered, memory, [ScaleDecision("HOLD", None, None, "STAGE_RESEARCH_CEILING_REACHED")], cfg)

    if any(s.manager_queue_depth >= cfg.manager_queue_soft_limit or s.capacity_state in {"AMBER", "PRESERVE"} or s.collisions for s in ordered):
        return _result(stage_population, run_id, input_digest, ordered, memory, [ScaleDecision("HOLD", None, None, "SOFT_PRESSURE_OR_COLLISION")], cfg)

    eligible = [
        s for s in ordered
        if s.queued_eligible_work > 0
        and s.standby_research > 0
        and s.active_research < cfg.specialist_cap_per_project
        and memory.healthy_windows.get(s.project_id, 0) >= cfg.healthy_windows_required
        and memory.cooldown_remaining.get(s.project_id, 0) == 0
    ]
    if not eligible:
        reason = "NO_ADMISSION_DEMAND" if not any(s.queued_eligible_work > 0 for s in ordered) else "HYSTERESIS_OR_CAPACITY_NOT_READY"
        return _result(stage_population, run_id, input_digest, ordered, memory, [ScaleDecision("HOLD", None, None, reason)], cfg)

    cursor = memory.fairness_cursor % len(eligible)
    rotated = eligible[cursor:] + eligible[:cursor]
    slots = min(available, cfg.max_global_admissions_per_cycle, len(rotated))
    chosen = rotated[:slots]
    cooldown = dict(memory.cooldown_remaining)
    decisions: list[ScaleDecision] = []
    for signal in chosen:
        decisions.append(ScaleDecision("REQUEST_ADMIT", signal.project_id, None, "SUSTAINED_HEALTHY_DEMAND"))
        cooldown[signal.project_id] = cfg.cooldown_windows
    memory = ScalerMemory(
        healthy_windows=dict(memory.healthy_windows),
        cooldown_remaining=cooldown,
        fairness_cursor=(memory.fairness_cursor + len(chosen)) % max(1, len(eligible)),
    )
    return _result(stage_population, run_id, input_digest, ordered, memory, decisions, cfg)


def _result(
    stage_population: int,
    run_id: str,
    input_digest: str,
    signals: Sequence[ProjectScaleSignal],
    memory: ScalerMemory,
    decisions: Sequence[ScaleDecision],
    cfg: ScalerConfig,
    *,
    remaining_excess: int = 0,
) -> dict[str, object]:
    payload = {
        "schema": "org-agent-mesh/system-scaler-decision/v2",
        "run_id": run_id,
        "stage_population": stage_population,
        "research_ceiling": stage_research_ceiling(stage_population, cfg),
        "active_research": sum(s.active_research for s in signals),
        "remaining_excess_after_requested_drains": remaining_excess,
        "input_digest": input_digest,
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
