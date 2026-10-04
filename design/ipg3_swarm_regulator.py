"""Design-only adaptive research escalation and swarm sizing regulator for IPG3.

This module has no authority to spawn agents. It produces recommendations/allocations
that require an ACTIVE Primary execution instance to authorize through the control plane.

Three policies are retained for field comparison:
- v1: naive breadth sizing (baseline candidate)
- v2: dependency-aware sizing and reduced manager overhead
- v3: risk/verification cells, diminishing returns, and live resize hysteresis
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Iterable


CONSEQUENCE = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


@dataclass(frozen=True)
class ResearchAssessment:
    confidence: float
    independent_workstreams: int
    domains: int = 1
    conflicting_evidence: bool = False
    stall_count: int = 0
    consequence: str = "MEDIUM"
    verification_needed: bool = False
    tool_gap: bool = False
    context_pressure: float = 0.0
    attempts: int = 1
    dependency_density: float = 0.0  # 0 = independent, 1 = nearly sequential
    novelty: float = 0.0             # 0 = routine, 1 = highly novel

    def __post_init__(self):
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be in [0,1]")
        if self.independent_workstreams < 1:
            raise ValueError("independent_workstreams must be >= 1")
        if self.domains < 1:
            raise ValueError("domains must be >= 1")
        if self.consequence not in CONSEQUENCE:
            raise ValueError("invalid consequence")
        if not 0 <= self.context_pressure <= 1:
            raise ValueError("context_pressure must be in [0,1]")
        if not 0 <= self.dependency_density <= 1:
            raise ValueError("dependency_density must be in [0,1]")
        if not 0 <= self.novelty <= 1:
            raise ValueError("novelty must be in [0,1]")


@dataclass(frozen=True)
class Allocation:
    escalate: bool
    research_agents: int
    manager_agents: int
    topology: str
    score: float
    reasons: tuple[str, ...]


def assistance_score(a: ResearchAssessment) -> tuple[float, tuple[str, ...]]:
    """Evidence-weighted trigger score. Low confidence alone is insufficient."""
    score = 0.0
    reasons: list[str] = []
    if a.confidence < 0.60:
        score += min(1.4, (0.60 - a.confidence) * 3.0)
        reasons.append("low-confidence")
    if a.conflicting_evidence:
        score += 1.1
        reasons.append("conflicting-evidence")
    if a.stall_count >= 2:
        score += min(1.2, 0.35 * a.stall_count)
        reasons.append("repeated-stall")
    if a.verification_needed:
        score += 0.8
        reasons.append("independent-verification")
    if a.tool_gap:
        score += 1.0
        reasons.append("tool-capability-gap")
    if a.context_pressure >= 0.80:
        score += 0.6
        reasons.append("context-pressure")
    if a.independent_workstreams >= 3:
        score += 0.45
        reasons.append("parallel-workstreams")
    if CONSEQUENCE[a.consequence] >= 2:
        score += 0.55 if a.consequence == "HIGH" else 0.9
        reasons.append("high-consequence")
    if a.novelty >= 0.75:
        score += 0.45
        reasons.append("high-novelty")
    # Require either a meaningful combined signal or a hard trigger.
    hard_trigger = a.tool_gap or (a.conflicting_evidence and a.verification_needed)
    return score, tuple(reasons + (["hard-trigger"] if hard_trigger else []))


def should_escalate(a: ResearchAssessment) -> tuple[bool, float, tuple[str, ...]]:
    score, reasons = assistance_score(a)
    hard_trigger = "hard-trigger" in reasons
    # Avoid escalating on a first weak attempt unless a hard trigger exists.
    attempt_gate = a.attempts >= 2 or a.stall_count >= 2 or hard_trigger
    return bool((score >= 1.55 and attempt_gate) or hard_trigger), score, reasons


def _topology(research: int, managers: int) -> str:
    if research <= 0:
        return "REJECTED"
    if managers == 0:
        return "PRIMARY_DIRECT"
    if managers == 1:
        return "SINGLE_MANAGER_CELL"
    return "MULTI_MANAGER_CELLS"


def allocate_v1(a: ResearchAssessment) -> Allocation:
    """Naive first implementation: size mostly from breadth and verify/risk boosts."""
    escalate, score, reasons = should_escalate(a)
    if not escalate:
        return Allocation(False, 0, 0, "REJECTED", score, reasons)
    research = a.independent_workstreams
    research += 1 if a.verification_needed else 0
    research += 1 if a.conflicting_evidence else 0
    research += 1 if CONSEQUENCE[a.consequence] >= 2 else 0
    research = max(1, min(12, research))
    managers = 0 if research <= 2 else ceil(research / 4)
    return Allocation(True, research, managers, _topology(research, managers), score, reasons)


def allocate_v2(a: ResearchAssessment) -> Allocation:
    """First optimization: account for sequential dependencies and manager overhead."""
    escalate, score, reasons = should_escalate(a)
    if not escalate:
        return Allocation(False, 0, 0, "REJECTED", score, reasons)
    parallel_fraction = max(0.25, 1.0 - 0.80 * a.dependency_density)
    research = max(1, ceil(a.independent_workstreams * parallel_fraction))
    if a.verification_needed or a.conflicting_evidence:
        research += 1
    if a.consequence == "CRITICAL":
        research += 1
    research = min(12, research)
    managers = 0
    if research >= 4 and (a.domains >= 2 or a.dependency_density >= 0.45):
        managers = 1
    if research >= 8 and a.domains >= 3:
        managers = 2
    return Allocation(True, research, managers, _topology(research, managers), score, reasons)


def allocate_v3(a: ResearchAssessment) -> Allocation:
    """Second optimization: independent verification cells + diminishing-return caps."""
    escalate, score, reasons = should_escalate(a)
    if not escalate:
        return Allocation(False, 0, 0, "REJECTED", score, reasons)

    # Parallel capacity should follow executable fronts, not question count.
    effective_fronts = max(1, ceil(a.independent_workstreams * (1.0 - 0.85 * a.dependency_density)))
    research = effective_fronts

    # Add independent verification only where epistemic/risk signals justify it.
    verification_pressure = (
        int(a.verification_needed)
        + int(a.conflicting_evidence)
        + int(CONSEQUENCE[a.consequence] >= 2)
        + int(a.novelty >= 0.70)
    )
    if verification_pressure >= 2:
        research += 1
    if verification_pressure >= 4 and effective_fronts >= 3:
        research += 1

    # Tool gaps require a capable worker, not a large swarm.
    if a.tool_gap and effective_fronts == 1:
        research = max(research, 1)

    # Diminishing returns: more than ~2 agents per independent front needs strong cause.
    soft_cap = max(2, effective_fronts * 2)
    research = min(research, soft_cap, 12)

    # Management is driven by coordination/integration, not researcher count alone.
    integration_load = (a.domains - 1) + (1 if a.dependency_density >= 0.45 else 0) + (1 if effective_fronts >= 5 else 0)
    managers = 0
    if research >= 4 and integration_load >= 2:
        managers = 1
    if research >= 8 and integration_load >= 4:
        managers = 2
    if research >= 12 and integration_load >= 6:
        managers = 3
    managers = min(managers, max(0, ceil(research / 4)))
    return Allocation(True, research, managers, _topology(research, managers), score, reasons)


def resize_v3(current: Allocation, observed: dict) -> Allocation:
    """Recommend scale-up/down with hysteresis. Primary authorization is still required.

    observed keys: unresolved_fronts, duplicate_work_rate, idle_rate, new_domains,
    disagreement_rate, stalled_cycles, verification_gap.
    """
    if not current.escalate:
        raise ValueError("cannot resize a rejected allocation")
    research = current.research_agents
    managers = current.manager_agents
    reasons = list(current.reasons)

    unresolved = int(observed.get("unresolved_fronts", 0))
    duplicate = float(observed.get("duplicate_work_rate", 0.0))
    idle = float(observed.get("idle_rate", 0.0))
    new_domains = int(observed.get("new_domains", 0))
    disagreement = float(observed.get("disagreement_rate", 0.0))
    stalled = int(observed.get("stalled_cycles", 0))
    verification_gap = bool(observed.get("verification_gap", False))

    # Scale up only on sustained unmet parallel demand or verification need.
    if (unresolved >= 2 and stalled >= 2) or verification_gap:
        add = min(2, max(1, unresolved))
        research = min(12, research + add)
        reasons.append("scale-up-unresolved-demand")
    # Scale down on clear oversupply; hysteresis avoids flapping.
    elif duplicate >= 0.35 or idle >= 0.40:
        remove = 2 if max(duplicate, idle) >= 0.60 else 1
        research = max(1, research - remove)
        reasons.append("scale-down-oversupply")

    integration_load = new_domains + int(disagreement >= 0.35) + int(research >= 6)
    if research >= 4 and integration_load >= 2:
        managers = max(managers, 1)
    if research >= 8 and integration_load >= 4:
        managers = max(managers, 2)
    if research <= 3:
        managers = 0
    managers = min(managers, max(0, ceil(research / 4)))
    return Allocation(True, research, managers, _topology(research, managers), current.score, tuple(reasons))


def make_cells(allocation: Allocation, workstreams: Iterable[str]) -> tuple[dict, ...]:
    """Create a deterministic suggested cell layout; no agents are spawned here."""
    if not allocation.escalate:
        return tuple()
    items = list(workstreams)
    manager_count = allocation.manager_agents
    cell_count = manager_count if manager_count else 1
    cells = [{"cell_id": f"cell-{i+1}", "manager_slot": (i+1 if manager_count else None), "workstreams": []} for i in range(cell_count)]
    for idx, workstream in enumerate(items):
        cells[idx % cell_count]["workstreams"].append(workstream)
    base = allocation.research_agents // cell_count
    rem = allocation.research_agents % cell_count
    for idx, cell in enumerate(cells):
        cell["research_agents"] = base + (1 if idx < rem else 0)
    return tuple(cells)
