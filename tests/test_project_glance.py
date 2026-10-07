from datetime import datetime, timezone
import unittest

from org_agent_mesh.project_glance import (
    ProjectGlanceError,
    build_project_glance_index,
    normalize_project_glance,
    render_project_glance,
)


NOW = datetime(2026, 10, 7, 13, 10, tzinfo=timezone.utc)


def sample(**overrides):
    value = {
        "project_id": "duo-open",
        "repository": "boberino93-bit/duo-open",
        "observed_at_utc": "2026-10-07T13:00:00Z",
        "status": "EXECUTING",
        "current_focus": "Fold7 continuity validation",
        "blockers": [],
        "next_action": "verify field trace",
        "last_material_change": "new field trace received",
        "evidence_refs": ["commit:abc"],
    }
    value.update(overrides)
    return value


class ProjectGlanceTests(unittest.TestCase):
    def test_fresh_snapshot_preserves_reported_status(self):
        result = normalize_project_glance(sample(), now=NOW, stale_seconds=3600)
        self.assertEqual(result["status"], "EXECUTING")
        self.assertEqual(result["freshness"], "FRESH")

    def test_stale_snapshot_never_claims_current_execution(self):
        result = normalize_project_glance(
            sample(observed_at_utc="2026-10-07T10:00:00Z"), now=NOW, stale_seconds=3600
        )
        self.assertEqual(result["reported_status"], "EXECUTING")
        self.assertEqual(result["status"], "STALE")
        self.assertEqual(result["freshness"], "STALE")

    def test_duplicate_project_is_rejected(self):
        with self.assertRaises(ProjectGlanceError):
            build_project_glance_index([sample(), sample()], now=NOW)

    def test_render_is_compact_and_includes_next_action(self):
        snapshot = build_project_glance_index([sample()], now=NOW)
        rendered = render_project_glance(snapshot)
        self.assertIn("Projects 1", rendered)
        self.assertIn("verify field trace", rendered)
        self.assertIn("duo-open", rendered)

    def test_unknown_is_explicit_not_idle(self):
        result = normalize_project_glance(sample(status="UNKNOWN"), now=NOW)
        self.assertEqual(result["status"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
