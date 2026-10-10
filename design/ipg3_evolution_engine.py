"""Design-only IPG3 evolution control-plane reference logic.

This module separates proposal state from promotion authority. It cannot mutate the active
framework; it validates candidate lifecycle and benchmark evidence so future runtime code
has explicit semantics to implement.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass


class EvolutionError(RuntimeError):
    pass


CANDIDATE_STATES = (
    "DISCOVERED", "NORMALIZED", "THREAT_MODELED", "SANDBOXED", "TESTED",
    "ADVERSARIALLY_TESTED", "BENCHMARKED", "REVIEWED", "PRIMARY_ACCEPTED",
    "INTEGRATED", "RELEASE_VALIDATED", "REJECTED", "SUPERSEDED", "BLOCKED", "ROLLED_BACK",
)

_TERMINAL = {"REJECTED", "SUPERSEDED", "BLOCKED", "ROLLED_BACK", "RELEASE_VALIDATED"}

_ALLOWED_TRANSITIONS = {
    "DISCOVERED": {"NORMALIZED", "REJECTED", "BLOCKED"},
    "NORMALIZED": {"THREAT_MODELED", "REJECTED", "BLOCKED"},
    "THREAT_MODELED": {"SANDBOXED", "REJECTED", "BLOCKED"},
    "SANDBOXED": {"TESTED", "REJECTED", "BLOCKED"},
    "TESTED": {"ADVERSARIALLY_TESTED", "REJECTED", "BLOCKED"},
    "ADVERSARIALLY_TESTED": {"BENCHMARKED", "REJECTED", "BLOCKED"},
    "BENCHMARKED": {"REVIEWED", "REJECTED", "BLOCKED"},
    "REVIEWED": {"PRIMARY_ACCEPTED", "REJECTED", "SUPERSEDED", "BLOCKED"},
    "PRIMARY_ACCEPTED": {"INTEGRATED", "REJECTED", "BLOCKED"},
    "INTEGRATED": {"RELEASE_VALIDATED", "ROLLED_BACK", "BLOCKED"},
    "RELEASE_VALIDATED": set(),
    "REJECTED": set(),
    "SUPERSEDED": set(),
    "BLOCKED": set(),
    "ROLLED_BACK": set(),
}


@dataclass(frozen=True)
class PromotionDecision:
    allowed: bool
    outcome: str
    reasons: tuple[str, ...]


def transition_candidate(candidate: dict, target_state: str) -> dict:
    current = candidate.get("status")
    if current not in CANDIDATE_STATES or target_state not in CANDIDATE_STATES:
        raise EvolutionError("unsupported candidate state")
    if target_state == current:
        return deepcopy(candidate)
    if target_state not in _ALLOWED_TRANSITIONS[current]:
        raise EvolutionError(f"invalid candidate transition: {current} -> {target_state}")
    updated = deepcopy(candidate)
    updated["status"] = target_state
    return updated


def evaluate_benchmark_for_promotion(
    candidate: dict,
    benchmark_results: list[dict],
    *,
    required_benchmark_ids: set[str] | None = None,
    required_adversarial_ids: set[str] | None = None,
) -> PromotionDecision:
    """Determine whether evidence permits BENCHMARKED -> REVIEWED progression.

    This does not perform the state transition and does not grant Primary acceptance.
    """
    reasons = []
    if candidate.get("status") != "BENCHMARKED":
        reasons.append("candidate is not in BENCHMARKED state")

    refs = {result.get("benchmark_result_id") for result in benchmark_results}
    required_benchmark_ids = set(required_benchmark_ids or candidate.get("required_benchmarks", []))
    missing = sorted(required_benchmark_ids - refs)
    if missing:
        reasons.append(f"missing benchmark evidence: {missing}")

    all_security = {}
    outcomes = []
    for result in benchmark_results:
        if result.get("candidate_id") != candidate.get("candidate_id"):
            reasons.append("benchmark candidate identity mismatch")
            continue
        decision = result.get("decision") or {}
        outcomes.append(decision.get("outcome"))
        for security in result.get("security_results", []):
            all_security[security.get("test_id")] = security.get("result")
        critical_regressions = [r for r in result.get("regressions", []) if r.get("severity") in {"HIGH", "CRITICAL"}]
        if critical_regressions:
            reasons.append("high/critical regression reported")
        reproducibility = result.get("reproducibility") or {}
        if not reproducibility.get("consistent"):
            reasons.append("benchmark is not reproducible")

    required_adversarial_ids = set(required_adversarial_ids or candidate.get("required_adversarial_tests", []))
    missing_security = sorted(test_id for test_id in required_adversarial_ids if all_security.get(test_id) != "PASS")
    if missing_security:
        reasons.append(f"required adversarial gates not passing: {missing_security}")

    if any(outcome == "UNSAFE" for outcome in outcomes):
        reasons.append("benchmark marked candidate unsafe")
    if any(outcome == "INFERIOR" for outcome in outcomes):
        reasons.append("benchmark marked candidate inferior")
    if not outcomes or not any(outcome in {"SUPERIOR", "NON_INFERIOR"} for outcome in outcomes):
        reasons.append("no qualifying benchmark outcome")

    allowed = not reasons
    outcome = "ELIGIBLE_FOR_REVIEW" if allowed else "NOT_ELIGIBLE"
    return PromotionDecision(allowed, outcome, tuple(reasons))


def authorize_review_transition(candidate: dict, benchmark_results: list[dict]) -> dict:
    decision = evaluate_benchmark_for_promotion(candidate, benchmark_results)
    if not decision.allowed:
        raise EvolutionError("; ".join(decision.reasons))
    return transition_candidate(candidate, "REVIEWED")


def analyze_progress_ledger(ledger: dict, *, stall_after: int = 3, convergence_after: int = 3) -> dict:
    """Derive progress/stall state from iteration evidence without changing strategy itself."""
    iterations = list(ledger.get("iterations", []))
    if stall_after < 1 or convergence_after < 1:
        raise ValueError("thresholds must be >= 1")

    action_counts = Counter(item.get("action_fingerprint") for item in iterations if item.get("action_fingerprint"))
    failure_counts = Counter(item.get("failure_class") for item in iterations if item.get("failure_class"))
    repeated_actions = sum(count - 1 for count in action_counts.values() if count > 1)
    distinct_failure_classes = len(failure_counts)
    novel_evidence = sum(len(set(item.get("evidence_gained", []))) for item in iterations)
    nonprogress = 0
    for item in reversed(iterations):
        if item.get("measurable_progress"):
            break
        nonprogress += 1

    signals = set()
    if repeated_actions:
        signals.add("REPEATED_ACTION")
    if any(count >= 2 for count in failure_counts.values()):
        signals.add("REPEATED_FAILURE")
    if iterations and not any(item.get("evidence_gained") for item in iterations[-stall_after:]):
        signals.add("NO_NOVEL_EVIDENCE")

    last = iterations[-convergence_after:] if iterations else []
    converged = (
        len(last) >= convergence_after
        and all(item.get("measurable_progress") is False for item in last)
        and all(not item.get("failure_class") for item in last)
        and all(not item.get("next_experiment") for item in last)
    )

    if converged:
        status = "CONVERGED"
        action = "STOP_CONVERGED"
        signals.add("MARGINAL_GAIN_BELOW_THRESHOLD")
    elif nonprogress >= stall_after:
        status = "STALLED"
        action = "RETURN_TO_EVOLUTION_LEDGER"
    elif nonprogress > 0 or signals:
        status = "WATCH"
        action = "CONTINUE"
    else:
        status = "PROGRESSING"
        action = "CONTINUE"

    updated = deepcopy(ledger)
    updated["progress_summary"] = {
        "novel_evidence_count": novel_evidence,
        "repeated_action_count": repeated_actions,
        "distinct_failure_classes": distinct_failure_classes,
        "accepted_change_count": ledger.get("progress_summary", {}).get("accepted_change_count", 0),
        "rejected_candidate_count": ledger.get("progress_summary", {}).get("rejected_candidate_count", 0),
    }
    updated["stall_state"] = {
        "status": status,
        "signals": sorted(signals),
        "consecutive_nonprogress_iterations": nonprogress,
    }
    updated["recommended_action"] = action
    return updated
