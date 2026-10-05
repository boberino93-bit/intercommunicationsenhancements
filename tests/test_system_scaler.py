import unittest

from org_agent_mesh.system_scaler import (
    DEFAULT_PROJECTS,
    ProjectScaleSignal,
    ScalerConfig,
    ScalerMemory,
    SystemScalerError,
    decide,
    stage_research_ceiling,
)

PROJECTS = list(DEFAULT_PROJECTS)
RUN_ID = "scale-run-001"
NOW = "2026-10-05T22:42:00Z"
MEASURED = "2026-10-05T22:41:30Z"


def sig(project_id, **overrides):
    data = dict(
        project_id=project_id,
        run_id=RUN_ID,
        measured_at_utc=MEASURED,
        active_research=0,
        standby_research=8,
        queued_eligible_work=1,
        manager_queue_depth=0,
        capacity_state="GREEN",
    )
    data.update(overrides)
    return ProjectScaleSignal(**data)


def signals(**overrides):
    return [sig(project_id, **overrides) for project_id in PROJECTS]


def decide_now(*, stage_population=30, items=None, memory=None, run_id=RUN_ID, now_utc=NOW, cfg=None):
    return decide(
        stage_population=stage_population,
        run_id=run_id,
        now_utc=now_utc,
        signals=items or signals(),
        memory=memory,
        cfg=cfg,
    )


class SystemScalerTests(unittest.TestCase):
    def test_stage_ceilings(self):
        cfg = ScalerConfig()
        self.assertEqual(stage_research_ceiling(15, cfg), 1)
        self.assertEqual(stage_research_ceiling(30, cfg), 16)
        self.assertEqual(stage_research_ceiling(60, cfg), 46)
        self.assertEqual(stage_research_ceiling(100, cfg), 56)

    def test_three_healthy_windows_required(self):
        memory = ScalerMemory()
        for _ in range(2):
            out = decide_now(memory=memory)
            memory = ScalerMemory(**out["memory"])
            self.assertEqual(out["decisions"][0]["action"], "HOLD")
        out = decide_now(memory=memory)
        self.assertTrue(any(d["action"] == "REQUEST_ADMIT" for d in out["decisions"]))

    def test_no_demand_never_scales_up(self):
        memory = ScalerMemory(healthy_windows={p: 4 for p in PROJECTS})
        out = decide_now(items=signals(queued_eligible_work=0), memory=memory)
        self.assertEqual(out["decisions"][0]["reason"], "NO_ADMISSION_DEMAND")
        self.assertFalse(any(d["action"] == "REQUEST_ADMIT" for d in out["decisions"]))

    def test_stale_telemetry_freezes_and_preserves_memory(self):
        memory = ScalerMemory(healthy_windows={p: 3 for p in PROJECTS}, fairness_cursor=4)
        out = decide_now(items=signals(measured_at_utc="2026-10-05T22:30:00Z"), memory=memory)
        self.assertIn("STALE_TELEMETRY", out["decisions"][0]["reason"])
        self.assertEqual(out["memory"]["fairness_cursor"], 4)
        self.assertEqual(out["memory"]["healthy_windows"], dict(memory.healthy_windows))

    def test_future_telemetry_freezes(self):
        out = decide_now(items=signals(measured_at_utc="2026-10-05T22:43:00Z"))
        self.assertIn("FUTURE_TELEMETRY", out["decisions"][0]["reason"])

    def test_run_mismatch_freezes(self):
        items = signals()
        items[0] = sig(PROJECTS[0], run_id="other-run")
        out = decide_now(items=items)
        self.assertIn("RUN_ID_MISMATCH", out["decisions"][0]["reason"])

    def test_exact_project_set_required(self):
        with self.assertRaises(SystemScalerError):
            decide_now(items=signals()[:-1])

    def test_duplicate_project_fails_closed(self):
        items = signals()
        items[-1] = sig(PROJECTS[0])
        with self.assertRaises(SystemScalerError):
            decide_now(items=items)

    def test_unknown_capacity_freezes(self):
        items = signals()
        items[0] = sig(PROJECTS[0], capacity_state="UNKNOWN")
        out = decide_now(items=items)
        self.assertIn("UNKNOWN_CAPACITY", out["decisions"][0]["reason"])

    def test_exhausted_capacity_freezes_without_drain(self):
        items = signals()
        items[0] = sig(PROJECTS[0], capacity_state="EXHAUSTED", idle_lease_free_agent_ids=("r-1",))
        out = decide_now(items=items)
        self.assertIn("EXHAUSTED_CAPACITY_CHECKPOINT_UNSAFE", out["decisions"][0]["reason"])
        self.assertFalse(any(d["action"] == "REQUEST_DRAIN_TO_STANDBY" for d in out["decisions"]))

    def test_unresolved_lease_freezes(self):
        items = signals()
        items[0] = sig(PROJECTS[0], unresolved_leases=1)
        out = decide_now(items=items)
        self.assertIn("UNRESOLVED_LEASE", out["decisions"][0]["reason"])

    def test_hard_manager_pressure_only_drains_safe_candidate(self):
        items = signals()
        items[0] = sig(PROJECTS[0], manager_queue_depth=15, active_research=2, standby_research=6, idle_lease_free_agent_ids=("r-2",))
        memory = ScalerMemory(healthy_windows={p: 4 for p in PROJECTS})
        out = decide_now(items=items, memory=memory)
        self.assertEqual(out["decisions"][0]["action"], "REQUEST_DRAIN_TO_STANDBY")
        self.assertEqual(out["decisions"][0]["agent_id"], "r-2")
        self.assertFalse(any(d["action"] == "REQUEST_ADMIT" for d in out["decisions"]))

    def test_hard_pressure_without_safe_candidate_blocks_all_admission(self):
        items = signals()
        items[0] = sig(PROJECTS[0], manager_queue_depth=15, active_research=2, standby_research=6)
        memory = ScalerMemory(healthy_windows={p: 4 for p in PROJECTS})
        out = decide_now(items=items, memory=memory)
        self.assertEqual(out["decisions"][0]["reason"], "HARD_PRESSURE_NO_SAFE_DRAIN")
        self.assertFalse(any(d["action"] == "REQUEST_ADMIT" for d in out["decisions"]))

    def test_reserve_only_blocks_admissions_globally(self):
        items = signals()
        items[0] = sig(PROJECTS[0], capacity_state="RESERVE_ONLY")
        memory = ScalerMemory(healthy_windows={p: 4 for p in PROJECTS})
        out = decide_now(items=items, memory=memory)
        self.assertFalse(any(d["action"] == "REQUEST_ADMIT" for d in out["decisions"]))

    def test_soft_pressure_holds(self):
        memory = ScalerMemory(healthy_windows={p: 4 for p in PROJECTS})
        out = decide_now(items=signals(manager_queue_depth=8), memory=memory)
        self.assertEqual(out["decisions"][0]["reason"], "SOFT_PRESSURE_OR_COLLISION")

    def test_stage_contraction_requests_graceful_drains(self):
        items = [sig(p, active_research=3, standby_research=5, idle_lease_free_agent_ids=(f"{p}-idle",)) for p in PROJECTS]
        out = decide_now(stage_population=15, items=items)
        self.assertTrue(all(d["action"] == "REQUEST_DRAIN_TO_STANDBY" for d in out["decisions"]))
        self.assertGreater(out["remaining_excess_after_requested_drains"], 0)
        self.assertFalse(any(d["action"] == "REQUEST_ADMIT" for d in out["decisions"]))

    def test_stage_contraction_without_safe_candidates_holds(self):
        items = [sig(p, active_research=3, standby_research=5) for p in PROJECTS]
        out = decide_now(stage_population=15, items=items)
        self.assertIn("STAGE_CONTRACTION_BLOCKED", out["decisions"][0]["reason"])

    def test_specialist_cap_blocks_project_admission(self):
        items = [sig(p, active_research=8, standby_research=1) for p in PROJECTS]
        memory = ScalerMemory(healthy_windows={p: 4 for p in PROJECTS})
        out = decide_now(stage_population=100, items=items, memory=memory)
        self.assertFalse(any(d["action"] == "REQUEST_ADMIT" for d in out["decisions"]))

    def test_cooldown_blocks_recently_admitted_project(self):
        healthy = {p: 4 for p in PROJECTS}
        cooldown = {p: 0 for p in PROJECTS}
        cooldown[PROJECTS[0]] = 2
        out = decide_now(memory=ScalerMemory(healthy_windows=healthy, cooldown_remaining=cooldown))
        admitted = {d["project_id"] for d in out["decisions"] if d["action"] == "REQUEST_ADMIT"}
        self.assertNotIn(PROJECTS[0], admitted)

    def test_global_admission_rate_limit(self):
        cfg = ScalerConfig(max_global_admissions_per_cycle=2)
        memory = ScalerMemory(healthy_windows={p: 4 for p in PROJECTS})
        out = decide_now(stage_population=100, memory=memory, cfg=cfg)
        self.assertEqual(sum(d["action"] == "REQUEST_ADMIT" for d in out["decisions"]), 2)

    def test_fairness_cursor_changes_selected_project(self):
        memory_a = ScalerMemory(healthy_windows={p: 4 for p in PROJECTS}, fairness_cursor=0)
        memory_b = ScalerMemory(healthy_windows={p: 4 for p in PROJECTS}, fairness_cursor=1)
        cfg = ScalerConfig(max_global_admissions_per_cycle=1)
        a = decide_now(memory=memory_a, cfg=cfg)
        b = decide_now(memory=memory_b, cfg=cfg)
        self.assertNotEqual(a["decisions"][0]["project_id"], b["decisions"][0]["project_id"])

    def test_authority_never_conveyed_and_no_direct_termination(self):
        memory = ScalerMemory(healthy_windows={p: 4 for p in PROJECTS})
        out = decide_now(memory=memory)
        self.assertFalse(out["authority_conveyed"])
        self.assertFalse(out["direct_termination_allowed"])
        self.assertTrue(all(d["authority_conveyed"] is False and d["direct_termination_allowed"] is False for d in out["decisions"]))

    def test_decision_digest_is_deterministic_for_same_snapshot(self):
        memory = ScalerMemory(healthy_windows={p: 4 for p in PROJECTS})
        a = decide_now(memory=memory)
        b = decide_now(memory=memory)
        self.assertEqual(a["input_digest"], b["input_digest"])
        self.assertEqual(a["decision_digest"], b["decision_digest"])

    def test_input_digest_changes_when_telemetry_changes(self):
        memory = ScalerMemory(healthy_windows={p: 4 for p in PROJECTS})
        a = decide_now(memory=memory)
        items = signals()
        items[0] = sig(PROJECTS[0], queued_eligible_work=2)
        b = decide_now(items=items, memory=memory)
        self.assertNotEqual(a["input_digest"], b["input_digest"])
        self.assertNotEqual(a["decision_digest"], b["decision_digest"])


if __name__ == "__main__":
    unittest.main()
