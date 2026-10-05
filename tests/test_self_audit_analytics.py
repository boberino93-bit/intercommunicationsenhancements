import copy
import json
from pathlib import Path
import unittest

from org_agent_mesh.self_audit import canonical_record_hash
from org_agent_mesh.self_audit_analytics import (
    SelfAuditAnalyticsError,
    audit_summary,
    compare_agents,
    compare_roles,
    framework_usage,
    recurring_findings,
    score_history,
)

ROOT = Path(__file__).resolve().parents[1]
AUDIT1 = ROOT / "governance" / "audit" / "ledger" / "AUDIT-0001.json"

ROLE_SCORE_FIXTURES = {
    "PRIMARY": {
        "orchestration": 8.0,
        "decision_integration": 8.0,
        "context_consolidation": 8.0,
        "delegation_correctness": 8.0,
        "final_answer_integrity": 8.0,
        "authorization_gating": 8.0,
    },
    "MANAGER": {
        "task_decomposition": 8.0,
        "researcher_allocation": 8.0,
        "duplication_prevention": 8.0,
        "escalation_behavior": 8.0,
        "result_reconciliation": 8.0,
        "dependency_tracking": 8.0,
    },
    "RESEARCH": {
        "source_quality": 8.0,
        "evidence_completeness": 8.0,
        "hypothesis_separation": 8.0,
        "reproducibility": 8.0,
        "uncertainty_reporting": 8.0,
        "research_handoff_quality": 8.0,
    },
}


class SelfAuditAnalyticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit1 = json.loads(AUDIT1.read_text())

    def make_record(self, record_id, agent_id, role, score_delta=0.0, repeated_failure=None):
        record = copy.deepcopy(self.audit1)
        record["audit_record_id"] = record_id
        record["timestamp"] = f"2026-10-05T14:{int(record_id[-2:]):02d}:00-07:00"
        record["agent_id"] = agent_id
        record["agent_role"] = role
        record["agent_instance"] = f"instance-{record_id}"
        record["role_scores"] = copy.deepcopy(ROLE_SCORE_FIXTURES[role])
        record["previous_audit_record"] = self.audit1["audit_record_id"]
        record["previous_record_hash"] = self.audit1["record_hash"]
        if score_delta:
            record["scores"]["authorization_discipline"] = max(
                0.0, min(10.0, record["scores"]["authorization_discipline"] + score_delta)
            )
        if repeated_failure is not None:
            record["authorization_failures_detected"] = [repeated_failure]
        record["record_hash"] = canonical_record_hash(record)
        return record

    def make_chain(self):
        second = self.make_record("AUDIT-0002", "agent-b", "MANAGER", 1.0, "implicit authorization inheritance")
        third = self.make_record("AUDIT-0003", "agent-c", "RESEARCH", 1.0, "implicit authorization inheritance")
        third["previous_audit_record"] = second["audit_record_id"]
        third["previous_record_hash"] = second["record_hash"]
        third["record_hash"] = canonical_record_hash(third)
        return [self.audit1, second, third]

    def test_score_history_is_comparable(self):
        history = score_history(self.make_chain(), "authorization_discipline")
        self.assertEqual([item["audit_record_id"] for item in history], ["AUDIT-0001", "AUDIT-0002", "AUDIT-0003"])
        self.assertEqual(history[0]["framework_version"], "1.0.0")

    def test_agent_comparison_returns_averages(self):
        comparison = compare_agents(self.make_chain(), "authorization_discipline")
        self.assertIn("primary-intercommunicationsenhancements", comparison)
        self.assertIn("agent-b", comparison)

    def test_role_comparison_is_role_normalized(self):
        comparison = compare_roles(self.make_chain(), "authorization_discipline")
        self.assertEqual(set(comparison), {"PRIMARY", "MANAGER", "RESEARCH"})

    def test_recurring_findings_detect_repeat(self):
        findings = recurring_findings(self.make_chain(), "authorization_failures_detected", minimum_count=2)
        self.assertEqual(findings["implicit authorization inheritance"], 2)

    def test_framework_usage_is_counted(self):
        self.assertEqual(framework_usage(self.make_chain()), {"1.0.0": 3})

    def test_summary_reports_population(self):
        summary = audit_summary(self.make_chain())
        self.assertEqual(summary["record_count"], 3)
        self.assertEqual(summary["agents"], 3)
        self.assertEqual(summary["framework_versions"], {"1.0.0": 3})

    def test_unknown_score_key_fails_closed(self):
        with self.assertRaisesRegex(SelfAuditAnalyticsError, "SCORE_KEY_UNKNOWN"):
            score_history(self.make_chain(), "invented_metric")

    def test_broken_chain_blocks_analytics(self):
        records = self.make_chain()
        records[1]["previous_record_hash"] = "0" * 64
        records[1]["record_hash"] = canonical_record_hash(records[1])
        with self.assertRaisesRegex(SelfAuditAnalyticsError, "CHAIN_INVALID"):
            audit_summary(records)


if __name__ == "__main__":
    unittest.main()
