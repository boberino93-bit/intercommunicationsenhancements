"""Dynamic field campaign for IPG3 swarm resize/coordination behavior."""

from dataclasses import dataclass

from ipg3_swarm_regulator import Allocation, ResearchAssessment, allocate_v3, resize_v3


@dataclass(frozen=True)
class ResizeScenario:
    name: str
    start: Allocation
    observed: dict
    expected_research: tuple[int, int]
    expected_managers: tuple[int, int]


def dist(v, rng):
    lo, hi = rng
    return max(lo - v, 0, v - hi)


def scenarios():
    under = allocate_v3(ResearchAssessment(0.45, 2, attempts=3, stall_count=3))
    over = allocate_v3(ResearchAssessment(0.45, 6, attempts=2, dependency_density=0.0))
    domain = allocate_v3(ResearchAssessment(0.45, 6, domains=1, attempts=2, dependency_density=0.0))
    stable = allocate_v3(ResearchAssessment(0.45, 5, domains=2, attempts=2, dependency_density=0.0))
    verify = allocate_v3(ResearchAssessment(0.45, 2, attempts=3, stall_count=2))
    return [
        ResizeScenario("scale-up-unresolved", under, {"unresolved_fronts":3,"stalled_cycles":2}, (4,4), (0,1)),
        ResizeScenario("scale-down-duplicate", over, {"duplicate_work_rate":0.65}, (4,4), (0,1)),
        ResizeScenario("add-manager-new-domains", domain, {"new_domains":2,"disagreement_rate":0.50}, (6,6), (1,1)),
        ResizeScenario("hysteresis-no-flap", stable, {"duplicate_work_rate":0.20,"idle_rate":0.30,"stalled_cycles":1}, (5,5), (0,1)),
        ResizeScenario("verification-gap", verify, {"verification_gap":True,"unresolved_fronts":1}, (3,4), (0,1)),
    ]


def main():
    total_penalty = 0
    churn = 0
    for scenario in scenarios():
        if not scenario.start.escalate:
            raise SystemExit(f"field fixture {scenario.name} attempted resize without an authorized swarm")
        result = resize_v3(scenario.start, scenario.observed)
        penalty = 2 * dist(result.research_agents, scenario.expected_research) + 2 * dist(result.manager_agents, scenario.expected_managers)
        total_penalty += penalty
        if (result.research_agents, result.manager_agents) != (scenario.start.research_agents, scenario.start.manager_agents):
            churn += 1
        print(scenario.name, "start=", (scenario.start.research_agents, scenario.start.manager_agents), "result=", (result.research_agents, result.manager_agents), "penalty=", penalty)
    if total_penalty != 0:
        raise SystemExit(f"dynamic swarm field test failed with penalty={total_penalty}")
    if churn != 4:
        raise SystemExit(f"expected exactly four justified topology changes, got {churn}")
    print("DYNAMIC FIELD TEST PASS: penalty=0; justified topology changes=4/5; no-flap case stayed stable")


if __name__ == "__main__":
    main()
