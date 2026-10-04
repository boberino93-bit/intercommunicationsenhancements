"""Synthetic field campaign for adaptive research escalation/swarm sizing.

The scenarios encode operational expectations, not model quality claims. The purpose is
to expose allocation-policy pathologies before live authority exists.
"""

from dataclasses import dataclass

from ipg3_swarm_regulator import ResearchAssessment, allocate_v1, allocate_v2, allocate_v3


@dataclass(frozen=True)
class Scenario:
    name: str
    assessment: ResearchAssessment
    expect_escalate: bool
    research_range: tuple[int, int]
    manager_range: tuple[int, int]


SCENARIOS = [
    Scenario("routine-local", ResearchAssessment(0.88, 1, attempts=1), False, (0,0), (0,0)),
    Scenario("first-weak-attempt", ResearchAssessment(0.28, 1, attempts=1), False, (0,0), (0,0)),
    Scenario("single-tool-gap", ResearchAssessment(0.82, 1, tool_gap=True), True, (1,1), (0,0)),
    Scenario("conflicting-evidence", ResearchAssessment(0.55, 2, conflicting_evidence=True, verification_needed=True, attempts=2), True, (2,3), (0,0)),
    Scenario("small-stalled-problem", ResearchAssessment(0.45, 2, attempts=3, stall_count=3), True, (2,3), (0,0)),
    Scenario("dependency-dense-chain", ResearchAssessment(0.38, 6, domains=2, attempts=3, stall_count=2, dependency_density=0.90), True, (1,3), (0,1)),
    Scenario("parallel-cross-domain", ResearchAssessment(0.42, 8, domains=4, attempts=2, verification_needed=True, consequence="HIGH", novelty=0.8), True, (8,10), (2,2)),
    Scenario("critical-three-front", ResearchAssessment(0.52, 3, domains=3, attempts=2, verification_needed=True, consequence="CRITICAL", novelty=0.85), True, (4,5), (1,1)),
    Scenario("broad-but-routine", ResearchAssessment(0.48, 5, domains=1, attempts=2, dependency_density=0.05), True, (5,6), (0,0)),
    Scenario("high-context-pressure-only", ResearchAssessment(0.56, 1, attempts=2, context_pressure=0.95), False, (0,0), (0,0)),
]


def distance(value: int, expected: tuple[int,int]) -> int:
    lo, hi = expected
    if value < lo:
        return lo - value
    if value > hi:
        return value - hi
    return 0


def evaluate(allocator):
    penalty = 0
    details = []
    for scenario in SCENARIOS:
        out = allocator(scenario.assessment)
        escalation_error = int(out.escalate != scenario.expect_escalate)
        rp = distance(out.research_agents, scenario.research_range)
        mp = distance(out.manager_agents, scenario.manager_range)
        scenario_penalty = escalation_error * 5 + rp * 2 + mp * 2
        penalty += scenario_penalty
        details.append((scenario.name, out.escalate, out.research_agents, out.manager_agents, scenario_penalty))
    return penalty, details


def main():
    generations = [("v1-baseline", allocate_v1), ("v2-dependency-aware", allocate_v2), ("v3-risk-cell+hysteresis", allocate_v3)]
    results = []
    for name, allocator in generations:
        penalty, details = evaluate(allocator)
        results.append((name, penalty, details))
        print(f"{name}: penalty={penalty}")
        for row in details:
            print("  ", row)

    v1, v2, v3 = [item[1] for item in results]
    if not v2 < v1:
        raise SystemExit(f"expected optimization v2 < v1, got {v2} >= {v1}")
    if not v3 < v2:
        raise SystemExit(f"expected optimization v3 < v2, got {v3} >= {v2}")
    print(f"FIELD TEST PASS: penalty improved {v1} -> {v2} -> {v3}")


if __name__ == "__main__":
    main()
