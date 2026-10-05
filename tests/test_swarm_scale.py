import unittest

from org_agent_mesh.swarm_scale import (
    SwarmScaleError,
    build_population_plan,
    evaluate_stage_gate,
    launch_window_seconds,
    next_stage,
    stage_for_population,
    summarize_population,
    validate_population_plan,
)

PROJECTS = [
    "ai-behaviour-control-lab",
    "benefitflow",
    "duo-open",
    "fold7-power-lab",
    "intercommunicationsenhancements",
    "warp-propulsion-lab",
    "xrp-thesis",
]


class SwarmScaleTests(unittest.TestCase):
    def test_100_agent_plan_is_deterministic_and_valid(self):
        first = build_population_plan(PROJECTS, target_population=100, specialist_cap_per_project=8)
        second = build_population_plan(PROJECTS, target_population=100, specialist_cap_per_project=8)
        self.assertEqual(first, second)
        self.assertTrue(validate_population_plan(first, project_ids=PROJECTS, target_population=100, specialist_cap_per_project=8))

    def test_current_caps_yield_70_active_and_30_standby(self):
        summary = summarize_population(build_population_plan(PROJECTS, target_population=100, specialist_cap_per_project=8))
        self.assertEqual(summary["population"], 100)
        self.assertEqual(summary["active_slots"], 70)
        self.assertEqual(summary["standby_read_only"], 30)
        self.assertEqual(summary["roles"], {"PRIMARY": 7, "MANAGER": 7, "RESEARCH": 86})

    def test_each_project_has_one_primary_one_manager_and_at_most_eight_active_research(self):
        summary = summarize_population(build_population_plan(PROJECTS, target_population=100, specialist_cap_per_project=8))
        for bucket in summary["projects"].values():
            self.assertEqual(bucket["PRIMARY"], 1)
            self.assertEqual(bucket["MANAGER"], 1)
            self.assertLessEqual(bucket["RESEARCH_ACTIVE"], 8)

    def test_population_membership_never_conveys_mutation_eligibility(self):
        plan = build_population_plan(PROJECTS, target_population=100, specialist_cap_per_project=8)
        self.assertFalse(any(item["mutation_eligible"] for item in plan))

    def test_default_serial_launch_window_is_explicit(self):
        self.assertEqual(launch_window_seconds(100, 30), 2970)
        self.assertEqual(launch_window_seconds(100, stage_for_population(100).provider_min_start_interval_seconds), 495)

    def test_stage_ladder_is_ordered(self):
        self.assertEqual(next_stage(0), 15)
        self.assertEqual(next_stage(15), 30)
        self.assertEqual(next_stage(30), 60)
        self.assertEqual(next_stage(60), 100)
        self.assertIsNone(next_stage(100))

    def test_clean_stage_gate_passes(self):
        metrics = {
            "ready_agents": 15,
            "accounted_agents": 15,
            "unauthorized_mutations": 0,
            "cross_project_write_violations": 0,
            "duplicate_commits": 0,
            "unresolved_leases": 0,
            "stale_handoffs": 0,
            "lost_agents": 0,
            "unaccounted_work_items": 0,
            "completion_integrity_pass": True,
            "ledger_chain_valid": True,
            "manager_backpressure_recovered": True,
        }
        self.assertTrue(evaluate_stage_gate(expected_agents=15, metrics=metrics)["passed"])

    def test_authority_violation_blocks_stage_progression(self):
        metrics = {
            "ready_agents": 15,
            "accounted_agents": 15,
            "unauthorized_mutations": 1,
            "cross_project_write_violations": 0,
            "duplicate_commits": 0,
            "unresolved_leases": 0,
            "stale_handoffs": 0,
            "lost_agents": 0,
            "unaccounted_work_items": 0,
            "completion_integrity_pass": True,
            "ledger_chain_valid": True,
            "manager_backpressure_recovered": True,
        }
        result = evaluate_stage_gate(expected_agents=15, metrics=metrics)
        self.assertFalse(result["passed"])
        self.assertIn("UNAUTHORIZED_MUTATIONS", result["failures"])

    def test_duplicate_projects_fail_closed(self):
        with self.assertRaises(SwarmScaleError):
            build_population_plan(["a", "a"], target_population=15, specialist_cap_per_project=8)


if __name__ == "__main__":
    unittest.main()
