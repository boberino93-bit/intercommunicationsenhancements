import json
from pathlib import Path
import unittest

from org_agent_mesh.change_review import ChangeReview, ChangeReviewError, ReviewReceipt

ROOT = Path(__file__).resolve().parents[1]


class ChangeReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads((ROOT / "governance" / "GLOBAL_SECURITY_CHANGE_POLICY.json").read_text())

    def make_review(self, **overrides):
        data = {
            "source_project": "intercommunicationsenhancements",
            "acting_role": "PRIMARY",
            "target_class": "GLOBAL_SWARM_SECURITY",
            "warning_acknowledged": True,
            "first": ReviewReceipt("R1", "PATH_A", "owner", "CASE-1", "global", True),
            "second": ReviewReceipt("R2", "PATH_B", "owner", "CASE-1", "global", True),
            "backup_ref": "backup/ref",
            "expected_pre_state": "abc123",
            "propagation_record": "XPR-1"
        }
        data.update(overrides)
        return ChangeReview(**data)

    def test_valid_review(self):
        self.make_review().validate(self.policy, subject_id="owner", case_id="CASE-1", base_checks_ok=True)

    def test_warning_required(self):
        with self.assertRaisesRegex(ChangeReviewError, "WARNING_ACK_REQUIRED"):
            self.make_review(warning_acknowledged=False).validate(self.policy, subject_id="owner", case_id="CASE-1", base_checks_ok=True)

    def test_receipts_must_be_distinct(self):
        same = ReviewReceipt("R1", "PATH_A", "owner", "CASE-1", "global", True)
        with self.assertRaisesRegex(ChangeReviewError, "DISTINCT_RECEIPTS_REQUIRED"):
            self.make_review(first=same, second=same).validate(self.policy, subject_id="owner", case_id="CASE-1", base_checks_ok=True)

    def test_base_checks_remain_required(self):
        with self.assertRaisesRegex(ChangeReviewError, "BASE_CHECKS_REQUIRED"):
            self.make_review().validate(self.policy, subject_id="owner", case_id="CASE-1", base_checks_ok=False)


if __name__ == "__main__":
    unittest.main()
