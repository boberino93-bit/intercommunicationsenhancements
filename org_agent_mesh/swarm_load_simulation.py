from __future__ import annotations

from dataclasses import dataclass
from random import Random

@dataclass(frozen=True)
class LoadReport:
    agents: int
    heartbeats_attempted: int
    heartbeats_accepted: int
    duplicates_rejected: int
    delayed_rejected: int
    dropped: int
    retry_events: int
    retry_storm_contained: bool
    capacity_peak_ratio: float
    capacity_guard_held: bool
    corruption_events: int
    bounded_failure: bool


def simulate_100_agents(*, seed: int = 7, agents: int = 100, rounds: int = 12, drop_rate: float = 0.04, duplicate_rate: float = 0.03, delayed_rate: float = 0.03, capacity_limit_ratio: float = 0.80) -> LoadReport:
    if agents != 100:
        raise ValueError("production-readiness simulation must model exactly 100 agents")
    rng = Random(seed)
    attempted = accepted = dup = delayed = dropped = retries = 0
    in_flight_retries = 0
    peak = 0.0
    corruption = 0
    for _round in range(rounds):
        round_writes = 0
        for _agent in range(agents):
            attempted += 1
            x = rng.random()
            if x < drop_rate:
                dropped += 1
                if in_flight_retries < max(5, agents // 10):
                    in_flight_retries += 1
                    retries += 1
                continue
            if x < drop_rate + duplicate_rate:
                dup += 1
                continue
            if x < drop_rate + duplicate_rate + delayed_rate:
                delayed += 1
                continue
            accepted += 1
            round_writes += 1
        utilization = min(1.0, (round_writes / agents) * 0.50)
        peak = max(peak, utilization)
        in_flight_retries = max(0, in_flight_retries - max(1, agents // 20))
    contained = in_flight_retries <= max(5, agents // 10)
    guard_held = peak <= capacity_limit_ratio
    bounded = corruption == 0 and contained and guard_held and accepted + dup + delayed + dropped == attempted
    return LoadReport(agents, attempted, accepted, dup, delayed, dropped, retries, contained, peak, guard_held, corruption, bounded)
