import unittest

from ipg3_swarm_regulator import ResearchAssessment, allocate_v3, resize_v3, should_escalate


class EscalationTests(unittest.TestCase):
    def test_simple_problem_does_not_escalate(self):
        a = ResearchAssessment(confidence=0.82, independent_workstreams=1, attempts=1)
        escalate, _, _ = should_escalate(a)
        self.assertFalse(escalate)

    def test_tool_gap_is_hard_trigger(self):
        a = ResearchAssessment(confidence=0.85, independent_workstreams=1, tool_gap=True, attempts=1)
        allocation = allocate_v3(a)
        self.assertTrue(allocation.escalate)
        self.assertEqual(allocation.research_agents, 1)
        self.assertEqual(allocation.manager_agents, 0)

    def test_conflict_plus_verification_escalates(self):
        a = ResearchAssessment(confidence=0.62, independent_workstreams=2, conflicting_evidence=True, verification_needed=True, attempts=1)
        self.assertTrue(allocate_v3(a).escalate)

    def test_first_weak_attempt_alone_does_not_escalate(self):
        a = ResearchAssessment(confidence=0.30, independent_workstreams=1, attempts=1)
        self.assertFalse(allocate_v3(a).escalate)


class SizingTests(unittest.TestCase):
    def test_dependency_dense_problem_does_not_explode(self):
        a = ResearchAssessment(confidence=0.42, independent_workstreams=6, domains=2, attempts=3, stall_count=2, dependency_density=0.90)
        result = allocate_v3(a)
        self.assertLessEqual(result.research_agents, 3)
        self.assertEqual(result.manager_agents, 0)

    def test_cross_domain_parallel_problem_gets_management(self):
        a = ResearchAssessment(confidence=0.45, independent_workstreams=8, domains=4, attempts=2, verification_needed=True, consequence="HIGH", novelty=0.8)
        result = allocate_v3(a)
        self.assertGreaterEqual(result.research_agents, 8)
        self.assertGreaterEqual(result.manager_agents, 2)

    def test_small_coherent_swarm_stays_primary_direct(self):
        a = ResearchAssessment(confidence=0.45, independent_workstreams=2, domains=1, attempts=3, stall_count=2)
        result = allocate_v3(a)
        self.assertEqual(result.manager_agents, 0)
        self.assertEqual(result.topology, "PRIMARY_DIRECT")


class ResizeTests(unittest.TestCase):
    def test_scale_up_on_sustained_unresolved_demand(self):
        base = allocate_v3(ResearchAssessment(confidence=0.4, independent_workstreams=3, attempts=3, stall_count=2))
        grown = resize_v3(base, {"unresolved_fronts": 3, "stalled_cycles": 2})
        self.assertGreater(grown.research_agents, base.research_agents)

    def test_scale_down_on_duplicate_work(self):
        base = allocate_v3(ResearchAssessment(confidence=0.4, independent_workstreams=5, domains=3, attempts=3, stall_count=2))
        shrunk = resize_v3(base, {"duplicate_work_rate": 0.7})
        self.assertLess(shrunk.research_agents, base.research_agents)

    def test_resize_cannot_act_on_rejected_allocation(self):
        base = allocate_v3(ResearchAssessment(confidence=0.9, independent_workstreams=1))
        with self.assertRaises(ValueError):
            resize_v3(base, {"unresolved_fronts": 2, "stalled_cycles": 2})


if __name__ == "__main__":
    unittest.main()
