from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.cross_project import validate_cross_project_exchange
from org_agent_mesh.project_scope import ProjectScopeError

BASE = {
    "schema": "org-agent-mesh/cross-project-exchange/v1",
    "exchange_id": "x1",
    "source_project_id": "a",
    "destination_project_id": "b",
    "requesting_agent_id": "primary",
    "purpose": "share bounded result",
    "data_classification": "INTERNAL",
    "requested_artifacts": ["artifact-1"],
    "allowed_use": "evaluation",
    "created_at_utc": "2026-10-03T00:00:00Z",
    "expires_at_utc": "2026-10-04T00:00:00Z",
    "correlation_id": "c1",
    "approval": {"status": "APPROVED", "approved_by": "human"}
}


class CrossProjectTest(unittest.TestCase):
    def test_denied_by_default(self):
        with self.assertRaises(ProjectScopeError):
            validate_cross_project_exchange(BASE)

    def test_explicit_capability_and_approval(self):
        self.assertTrue(validate_cross_project_exchange(BASE, has_cross_project_capability=True))

    def test_requires_approval(self):
        exchange = dict(BASE, approval={"status": "PENDING"})
        with self.assertRaises(ProjectScopeError):
            validate_cross_project_exchange(exchange, has_cross_project_capability=True)


if __name__ == "__main__":
    unittest.main()
