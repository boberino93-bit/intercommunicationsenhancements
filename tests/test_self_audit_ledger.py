import copy
import json
from pathlib import Path
import unittest

from org_agent_mesh.self_audit import (
    SelfAuditError,
    canonical_record_hash,
    is_self_audit_request,
    ledger_head,
    role_extension,
    validate_append,
    validate_ledger_transition,
    validate_record,
    verify_anchored_head,
    verify_chain,
)

ROOT = Path(__file__).resolve().parents[1]
AUDIT1 = ROOT / "governance" / "audit" / "ledger" / "AUDIT-0001.json"
HEAD = ROOT / "governance" / "audit" / "LEDGER_HEAD.json"


class SelfAuditLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit1 = json.loads(AUDIT1.read_text())
        cls.head = json.loads(HEAD.read_text())

    def make_second(self):
        record = copy.deepcopy(self.audit1)
        record["audit_record_id"] = "AUDIT-0002"
        record["timestamp"] = "2026-10-05T13:30:00-07:00"
        record["audit_trigger"] = "test second audit"
        record["previous_audit_record"] = self.audit1["audit_record_id"]
        record["previous_record_hash"] = self.audit1["record_hash"]
        record["supersedes_record"] = None
        record["record_hash"] = canonical_record_hash(record)
        return record

    def test_audit_0001_hash_is_valid(self):
        self.assertEqual(self.audit1["record_hash"], canonical_record_hash(self.audit1))
        validate_record(self.audit1)

    def test_genesis_chain_and_anchor_are_valid(self):
        self.assertTrue(verify_chain([self.audit1]))
        self.assertTrue(verify_anchored_head([self.audit1], self.head))

    def test_tampering_is_detected(self):
        changed = copy.deepcopy(self.audit1)
        changed["overall_score"] = 10
        with self.assertRaisesRegex(SelfAuditError, "HASH_MISMATCH"):
            validate_record(changed)

    def test_tail_truncation_is_detected_by_anchor(self):
        second = self.make_second()
        records = [self.audit1, second]
        anchor = ledger_head(records)
        self.assertTrue(verify_anchored_head(records, anchor))
        self.assertFalse(verify_anchored_head([self.audit1], anchor))

    def test_valid_append_requires_previous_links(self):
        second = self.make_second()
        validate_append([self.audit1], second)

    def test_valid_ledger_transition_may_only_append(self):
        second = self.make_second()
        validate_ledger_transition([self.audit1], [self.audit1, second])

    def test_ledger_transition_cannot_shrink_history(self):
        second = self.make_second()
        with self.assertRaisesRegex(SelfAuditError, "HISTORY_SHRINK_DENIED"):
            validate_ledger_transition([self.audit1, second], [self.audit1])

    def test_ledger_transition_cannot_rewrite_historical_record(self):
        changed = copy.deepcopy(self.audit1)
        changed["overall_score"] = 8.5
        changed["record_hash"] = canonical_record_hash(changed)
        with self.assertRaisesRegex(SelfAuditError, "HISTORICAL_RECORD_MUTATION_DENIED"):
            validate_ledger_transition([self.audit1], [changed])

    def test_duplicate_id_is_denied(self):
        duplicate = copy.deepcopy(self.audit1)
        with self.assertRaisesRegex(SelfAuditError, "REPLAY_DENIED"):
            validate_append([self.audit1], duplicate)

    def test_bad_previous_hash_is_denied(self):
        second = self.make_second()
        second["previous_record_hash"] = "0" * 64
        second["record_hash"] = canonical_record_hash(second)
        with self.assertRaisesRegex(SelfAuditError, "PREVIOUS_HASH_MISMATCH"):
            validate_append([self.audit1], second)

    def test_framework_version_mismatch_fails_closed(self):
        changed = copy.deepcopy(self.audit1)
        changed["framework_version"] = "9.9.9"
        changed["record_hash"] = canonical_record_hash(changed)
        with self.assertRaisesRegex(SelfAuditError, "FRAMEWORK_VERSION_MISMATCH"):
            validate_record(changed)

    def test_material_evidence_requires_valid_provenance(self):
        changed = copy.deepcopy(self.audit1)
        changed["evidence"][0]["provenance"] = "MADE_UP"
        changed["record_hash"] = canonical_record_hash(changed)
        with self.assertRaisesRegex(SelfAuditError, "EVIDENCE_INVALID"):
            validate_record(changed)

    def test_required_scores_cannot_be_omitted(self):
        changed = copy.deepcopy(self.audit1)
        changed["scores"].pop("authorization_discipline")
        changed["record_hash"] = canonical_record_hash(changed)
        with self.assertRaisesRegex(SelfAuditError, "REQUIRED_SCORES_MISSING"):
            validate_record(changed)

    def test_known_role_requires_its_extension_scores(self):
        changed = copy.deepcopy(self.audit1)
        changed["role_scores"].pop("authorization_gating")
        changed["record_hash"] = canonical_record_hash(changed)
        with self.assertRaisesRegex(SelfAuditError, "REQUIRED_ROLE_SCORES_MISSING"):
            validate_record(changed)

    def test_unknown_role_cannot_invent_extension(self):
        changed = copy.deepcopy(self.audit1)
        changed["agent_role"] = "UNKNOWN_SPECIALIST"
        changed["role_scores"] = {"invented_metric": 9.0}
        changed["record_hash"] = canonical_record_hash(changed)
        with self.assertRaisesRegex(SelfAuditError, "UNKNOWN_ROLE_EXTENSION_MUST_BE_EMPTY"):
            validate_record(changed)

    def test_unknown_role_can_use_common_core_with_empty_extension(self):
        changed = copy.deepcopy(self.audit1)
        changed["agent_role"] = "UNKNOWN_SPECIALIST"
        changed["role_scores"] = {}
        changed["record_hash"] = canonical_record_hash(changed)
        validate_record(changed)

    def test_common_trigger_phrases_are_detected(self):
        self.assertTrue(is_self_audit_request("Please self-evaluate your performance"))
        self.assertTrue(is_self_audit_request("Audit yourself against the framework"))
        self.assertFalse(is_self_audit_request("Summarize the project"))

    def test_role_extensions_are_stable(self):
        self.assertIn("authorization_gating", role_extension("PRIMARY"))
        self.assertIn("dependency_tracking", role_extension("manager"))
        self.assertIn("source_quality", role_extension("research"))
        self.assertEqual(role_extension("UNKNOWN_SPECIALIST"), tuple())


if __name__ == "__main__":
    unittest.main()
