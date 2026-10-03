from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.lanes import claim_lane


class LaneTest(unittest.TestCase):
    def test_duplicate_active_lane_requires_explicit_replication(self):
        base = {
            "project_id": "p1", "lane_id": "L", "assignment": "a", "scope": "s",
            "starting_project_state": "v1", "expected_output": "o", "dependencies": [],
            "possible_overlap": [], "current_status": "ACTIVE", "agent_id": "a", "agent_instance_id": "a-1"
        }
        with self.assertRaises(RuntimeError):
            claim_lane([base], dict(base, agent_id="b", agent_instance_id="b-1"))
        result = claim_lane([base], dict(base, agent_id="b", agent_instance_id="b-1"), allow_replication=True)
        self.assertTrue(result["replication_mode"])

    def test_same_lane_different_projects_do_not_collide(self):
        base = {
            "project_id": "p1", "lane_id": "L", "assignment": "a", "scope": "s",
            "starting_project_state": "v1", "expected_output": "o", "dependencies": [],
            "possible_overlap": [], "current_status": "ACTIVE", "agent_id": "a", "agent_instance_id": "a-1"
        }
        result = claim_lane([base], dict(base, project_id="p2"))
        self.assertFalse(result["replication_mode"])


if __name__ == "__main__":
    unittest.main()
