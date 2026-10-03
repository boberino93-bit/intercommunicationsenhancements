from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.capacity import (
    CapacityResource,
    aggregate_capacity_signals,
    build_capacity_signal,
    evaluate_write,
    signal_is_stale,
    signal_materially_changed,
)


class CapacityTest(unittest.TestCase):
    def test_known_limit_preserves_twenty_percent_reserve(self):
        resource = CapacityResource("COMMITS", hard_limit=100, used=60, source="EXPLICIT_CONFIG")
        self.assertEqual(resource.safe_ceiling, 80)
        self.assertEqual(resource.remaining_safe_budget, 20)
        self.assertEqual(resource.state, "AMBER")

    def test_preserve_and_reserve_only_states(self):
        self.assertEqual(CapacityResource("UPLOADS", 100, 79, "PROVIDER_OBSERVED").state, "PRESERVE")
        self.assertEqual(CapacityResource("UPLOADS", 100, 80, "PROVIDER_OBSERVED").state, "RESERVE_ONLY")

    def test_unknown_is_not_unlimited(self):
        resource = CapacityResource("COMMITS", hard_limit=None, used=None)
        self.assertEqual(resource.state, "UNKNOWN")
        decision = evaluate_write(resource, "DISCRETIONARY")
        self.assertFalse(decision.allowed)
        self.assertIn("UNKNOWN_CAPACITY", decision.reason)
        self.assertTrue(evaluate_write(resource, "ESSENTIAL_CANONICAL").allowed)

    def test_preserve_mode_requires_coalescing(self):
        resource = CapacityResource("COMMITS", hard_limit=100, used=79, source="EXPLICIT_CONFIG")
        self.assertFalse(evaluate_write(resource, "DISCRETIONARY").allowed)
        self.assertTrue(evaluate_write(resource, "COALESCED_CHECKPOINT").allowed)
        self.assertFalse(evaluate_write(resource, "COALESCED_CHECKPOINT", units=2).allowed)

    def test_unchanged_digest_is_suppressed(self):
        resource = CapacityResource("UPLOADS", hard_limit=100, used=10, source="EXPLICIT_CONFIG")
        decision = evaluate_write(resource, "COALESCED_CHECKPOINT", content_digest="abc", last_persisted_digest="abc")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "UNCHANGED_CONTENT")

    def test_signal_only_exposes_high_level_needs(self):
        resource = CapacityResource("COMMITS", hard_limit=100, used=76, source="EXPLICIT_CONFIG")
        signal = build_capacity_signal(
            project_id="project-a",
            repository_identity="owner/project-a",
            observed_revision="abc123",
            measured_at_utc="2026-10-03T23:00:00Z",
            resources=[resource],
            high_level_needs=["PRIMARY_DECISION", "CAPACITY_PRESSURE"],
            pending_writes={"ESSENTIAL_CANONICAL": 1},
        )
        self.assertEqual(signal["overall_state"], "PRESERVE")
        self.assertTrue(signal["batching_recommended"])
        self.assertTrue(signal["discretionary_writes_blocked"])
        with self.assertRaises(ValueError):
            build_capacity_signal(
                project_id="project-a",
                repository_identity="owner/project-a",
                observed_revision="abc123",
                measured_at_utc="2026-10-03T23:00:00Z",
                resources=[resource],
                high_level_needs=["RAW_DOMAIN_STATE"],
            )

    def test_signal_publication_is_transition_driven(self):
        resource = CapacityResource("COMMITS", hard_limit=100, used=61, source="EXPLICIT_CONFIG")
        first = build_capacity_signal(project_id="project-a", repository_identity="owner/project-a", observed_revision="a", measured_at_utc="2026-10-03T23:00:00Z", resources=[resource])
        same_band = build_capacity_signal(project_id="project-a", repository_identity="owner/project-a", observed_revision="b", measured_at_utc="2026-10-03T23:10:00Z", resources=[CapacityResource("COMMITS", 100, 69, "EXPLICIT_CONFIG")])
        self.assertFalse(signal_materially_changed(first, same_band))
        preserve = build_capacity_signal(project_id="project-a", repository_identity="owner/project-a", observed_revision="c", measured_at_utc="2026-10-03T23:20:00Z", resources=[CapacityResource("COMMITS", 100, 76, "EXPLICIT_CONFIG")])
        self.assertTrue(signal_materially_changed(first, preserve))

    def test_staleness_requires_explicit_policy(self):
        self.assertTrue(signal_is_stale("2026-10-03T20:00:00Z", "2026-10-03T23:00:01Z", max_age_seconds=10800))
        self.assertFalse(signal_is_stale("2026-10-03T20:00:00Z", "2026-10-03T23:00:00Z", max_age_seconds=10800))

    def test_aggregate_is_advisory_and_cross_project(self):
        def signal(project, state_used, needs=()):
            return build_capacity_signal(project_id=project, repository_identity=f"owner/{project}", observed_revision="x", measured_at_utc="2026-10-03T23:00:00Z", resources=[CapacityResource("COMMITS", 100, state_used, "EXPLICIT_CONFIG")], high_level_needs=needs)
        aggregate = aggregate_capacity_signals([signal("a", 10), signal("b", 79, ["PRIMARY_DECISION"])])
        self.assertEqual(aggregate["project_count"], 2)
        self.assertEqual(aggregate["projects_requiring_primary_decision"], ["b"])
        self.assertEqual(aggregate["capacity_pressure_projects"], [{"project_id": "b", "state": "PRESERVE"}])


if __name__ == "__main__":
    unittest.main()
