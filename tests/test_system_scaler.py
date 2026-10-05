import unittest

from org_agent_mesh.system_scaler import (
    ProjectScaleSignal,
    ScalerConfig,
    ScalerMemory,
    SystemScalerError,
    decide,
    stage_research_ceiling,
)


PROJECTS = [
    "ai-behaviour-control-lab", "benefitflow", "duo-open", "fold7-power-lab",
    "intercommunicationsenhancements", "warp-propulsion-lab", "xrp-thesis",
]


def sig(project_id, **overrides):
    data = dict(
        project_id=project_id,
        active_research=0,
        standby_research=8,
        manager_queue_depth=0,
        capacity_state="GREEN",
    )
    data.update(overrides)
    return ProjectScaleSignal(**data)


def signals(**overrides):
    return [sig(project_id, **overrides) for project_id in PROJECTS]


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
            out = decide(stage_population=30, signals=signals(), memory=memory)
            memory = ScalerMemory(**out["memory"])
            self.assertEqual(out["decisions"][0]["action"], "HOLD")
        out = decide(stage_population=30, signals=signals(), memory=memory)
        self.assertTrue(any(d["action"] == "REQUEST_ADMIT" for d in out["decisions"]))

    def test_unknown_capacity_freezes(self):
        items = signals()
        items[0] = sig(PROJECTS[0], capacity_state="UNKNOWN")
        out = decide(stage_population=30, signals=items)
        self.assertEqual(out["decisions"][0]["action"], "HOLD")
        self.assertIn("UNKNOWN_CAPACITY", out["decisions"][0]["reason"])

    def test_unresolved_lease_freezes(self):
        items = signals()
        items[0] = sig(PROJECTS[0], unresolved_leases=1)
        out = decide(stage_population=30, signals=items)
        self.assertIn("UNRESOLVED_LEASE", out["decisions"][0]["reason"])

    def test_hard_pressure_only_drains_known_safe_candidate(self):
        items = signals()
        items[0] = sig(PROJECTS[0], manager_queue_depth=15, active_research=2, standby_research=6, idle_lease_free_agent_ids=("r-2",))
        out = decide(stage_population=30, signals=items)
        d = out["decisions"][0]
        self.assertEqual(d["action"], "REQUEST_DRAIN_TO_STANDBY")
        self.assertEqual(d["agent_id"], "r-2")
        self.assertFalse(d["direct_termination_allowed"])

    def test_hard_pressure_without_safe_candidate_does_not_kill(self):
        items = signals()
        items[0] = sig(PROJECTS[0], manager_queue_depth=15, active_research=2, standby_research=6)
        out = decide(stage_population=30, signals=items)
        self.assertFalse(any(d["action"] == "REQUEST_DRAIN_TO_STANDBY" for d in out["decisions"]))
        self.assertTrue(all(d["direct_termination_allowed"] is False for d in out["decisions"]))

    def test_soft_pressure_holds(self):
        items = signals(manager_queue_depth=8)
        memory = ScalerMemory(healthy_windows={p: 4 for p in PROJECTS})
        out = decide(stage_population=30, signals=items, memory=memory)
        self.assertEqual(out["decisions"][0]["action"], "HOLD")

    def test_specialist_cap_blocks_project_admission(self):
        items = [sig(p, active_research=8, standby_research=1) for p in PROJECTS]
        memory = ScalerMemory(healthy_windows={p: 4 for p in PROJECTS})
        out = decide(stage_population=100, signals=items, memory=memory)
        self.assertFalse(any(d["action"] == "REQUEST_ADMIT" for d in out["decisions"]))

    def test_authority_never_conveyed(self):
        memory = ScalerMemory(healthy_windows={p: 4 for p in PROJECTS})
        out = decide(stage_population=30, signals=signals(), memory=memory)
        self.assertFalse(out["authority_conveyed"])
        self.assertTrue(all(d["authority_conveyed"] is False for d in out["decisions"]))

    def test_decision_digest_is_deterministic(self):
        memory = ScalerMemory(healthy_windows={p: 4 for p in PROJECTS})
        a = decide(stage_population=30, signals=signals(), memory=memory)
        b = decide(stage_population=30, signals=signals(), memory=memory)
        self.assertEqual(a["decision_digest"], b["decision_digest"])

    def test_duplicate_project_fails_closed(self):
        items = signals()
        items[-1] = sig(PROJECTS[0])
        with self.assertRaises(SystemScalerError):
            decide(stage_population=30, signals=items)


if __name__ == "__main__":
    unittest.main()
