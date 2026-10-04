import unittest

from ipg3_evolution_engine import (
    EvolutionError,
    analyze_progress_ledger,
    authorize_review_transition,
    evaluate_benchmark_for_promotion,
    transition_candidate,
)


def candidate_fixture(status="BENCHMARKED"):
    return {
        "schema": "org-agent-mesh/evolution-candidate/v2-draft",
        "candidate_id": "candidate-0001",
        "project_id": "intercommunicationsenhancements",
        "generation": 1,
        "parent_candidate_ids": [],
        "improvement_algorithm_version": "1",
        "title": "candidate",
        "hypothesis": "improve reliability",
        "source_patterns": [],
        "affected_dimensions": ["MESSAGING"],
        "expected_benefits": ["safer replay"],
        "risk": "MEDIUM",
        "threat_model": {"new_attack_surfaces": [], "invariants_at_risk": [], "abuse_cases": []},
        "baseline_ref": "g2",
        "sandbox_ref": "sandbox-1",
        "required_benchmarks": ["benchmark-1"],
        "required_adversarial_tests": ["replay", "isolation"],
        "benchmark_result_refs": ["benchmark-1"],
        "review_refs": [],
        "status": status,
        "disposition_reason": None,
        "created_by": {"agent_id": "primary", "agent_instance_id": "p-1"},
        "created_at_utc": "2026-10-04T04:00:00Z",
    }


def benchmark_fixture(outcome="SUPERIOR", *, consistent=True, regression_severity=None):
    regressions = []
    if regression_severity:
        regressions.append({"invariant": "project isolation", "severity": regression_severity, "evidence_ref": "e1"})
    return {
        "schema": "org-agent-mesh/benchmark-result/v1-draft",
        "benchmark_result_id": "benchmark-1",
        "project_id": "intercommunicationsenhancements",
        "candidate_id": "candidate-0001",
        "baseline_ref": "g2",
        "suite_id": "suite-1",
        "suite_revision": "1",
        "executed_at_utc": "2026-10-04T04:00:00Z",
        "executor": {"agent_id": "verifier", "agent_instance_id": "v-1", "principal_id": None},
        "metrics": [{"name": "replay_safety", "direction": "EQUAL_REQUIRED", "baseline": True, "candidate": True, "unit": None, "passed": True}],
        "security_results": [
            {"test_id": "replay", "result": "PASS", "evidence_ref": "r1"},
            {"test_id": "isolation", "result": "PASS", "evidence_ref": "r2"},
        ],
        "regressions": regressions,
        "reproducibility": {"runs": 2, "consistent": consistent, "environment_refs": ["env-1", "env-2"]},
        "decision": {"outcome": outcome, "reason": "fixture"},
    }


def ledger_fixture(iterations):
    return {
        "schema": "org-agent-mesh/progress-ledger/v1-draft",
        "ledger_id": "ledger-1",
        "project_id": "intercommunicationsenhancements",
        "objective_id": "objective-1",
        "opened_at_utc": "2026-10-04T04:00:00Z",
        "updated_at_utc": "2026-10-04T04:10:00Z",
        "iterations": iterations,
        "progress_summary": {"novel_evidence_count": 0, "repeated_action_count": 0, "distinct_failure_classes": 0, "accepted_change_count": 0, "rejected_candidate_count": 0},
        "stall_state": {"status": "PROGRESSING", "signals": [], "consecutive_nonprogress_iterations": 0},
        "recommended_action": "CONTINUE",
    }


class CandidateLifecycleTests(unittest.TestCase):
    def test_cannot_skip_evidence_stages(self):
        with self.assertRaises(EvolutionError):
            transition_candidate(candidate_fixture("DISCOVERED"), "PRIMARY_ACCEPTED")

    def test_superior_reproducible_candidate_is_review_eligible(self):
        decision = evaluate_benchmark_for_promotion(candidate_fixture(), [benchmark_fixture()])
        self.assertTrue(decision.allowed)
        self.assertEqual(authorize_review_transition(candidate_fixture(), [benchmark_fixture()])["status"], "REVIEWED")

    def test_unsafe_candidate_cannot_self_promote(self):
        decision = evaluate_benchmark_for_promotion(candidate_fixture(), [benchmark_fixture("UNSAFE")])
        self.assertFalse(decision.allowed)
        with self.assertRaises(EvolutionError):
            authorize_review_transition(candidate_fixture(), [benchmark_fixture("UNSAFE")])

    def test_high_regression_blocks_promotion(self):
        decision = evaluate_benchmark_for_promotion(candidate_fixture(), [benchmark_fixture("SUPERIOR", regression_severity="HIGH")])
        self.assertFalse(decision.allowed)

    def test_inconsistent_benchmark_blocks_promotion(self):
        decision = evaluate_benchmark_for_promotion(candidate_fixture(), [benchmark_fixture("SUPERIOR", consistent=False)])
        self.assertFalse(decision.allowed)


class ProgressTests(unittest.TestCase):
    def test_repeated_nonprogress_triggers_stall(self):
        iterations = [
            {"iteration": i, "hypothesis": "same", "action_fingerprint": "same-action", "evidence_gained": [], "measurable_progress": False, "failure_class": "same-failure", "next_experiment": "retry"}
            for i in range(3)
        ]
        result = analyze_progress_ledger(ledger_fixture(iterations), stall_after=3)
        self.assertEqual(result["stall_state"]["status"], "STALLED")
        self.assertEqual(result["recommended_action"], "RETURN_TO_EVOLUTION_LEDGER")
        self.assertIn("REPEATED_ACTION", result["stall_state"]["signals"])
        self.assertIn("REPEATED_FAILURE", result["stall_state"]["signals"])

    def test_progress_resets_nonprogress_counter(self):
        iterations = [
            {"iteration": 0, "hypothesis": "a", "action_fingerprint": "a", "evidence_gained": [], "measurable_progress": False, "failure_class": "x", "next_experiment": "b"},
            {"iteration": 1, "hypothesis": "b", "action_fingerprint": "b", "evidence_gained": ["new-evidence"], "measurable_progress": True, "failure_class": None, "next_experiment": "c"},
        ]
        result = analyze_progress_ledger(ledger_fixture(iterations))
        self.assertEqual(result["stall_state"]["consecutive_nonprogress_iterations"], 0)
        self.assertEqual(result["stall_state"]["status"], "PROGRESSING")

    def test_exhausted_clean_search_converges(self):
        iterations = [
            {"iteration": i, "hypothesis": f"h{i}", "action_fingerprint": f"a{i}", "evidence_gained": [], "measurable_progress": False, "failure_class": None, "next_experiment": None}
            for i in range(3)
        ]
        result = analyze_progress_ledger(ledger_fixture(iterations), convergence_after=3)
        self.assertEqual(result["stall_state"]["status"], "CONVERGED")
        self.assertEqual(result["recommended_action"], "STOP_CONVERGED")


if __name__ == "__main__":
    unittest.main()
