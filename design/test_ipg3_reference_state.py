from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import unittest

from ipg3_reference_state import ApprovalDenied, ApprovalLedger, EffectConflict, EffectLedger, StateConflict

NOW = datetime(2026, 10, 4, 4, 0, 0, tzinfo=timezone.utc)


def approval_fixture():
    return {
        "schema": "org-agent-mesh/human-approval/v1-draft",
        "approval_id": "approval-atomic-1", "project_id": "intercommunicationsenhancements",
        "approver": {"principal_id": "human:owner", "display_ref": "owner"},
        "operation_class": "WRITE_SOURCE",
        "target": {"system": "github", "resource": "design/file.txt", "scope_digest": "a" * 64},
        "task_id": "task-1", "effect_id": "effect-1",
        "issued_at_utc": "2026-10-04T03:00:00Z", "expires_at_utc": "2026-10-04T05:00:00Z",
        "max_uses": 1, "uses": 0, "status": "ISSUED", "decision_evidence_ref": "decision-1",
        "integrity": {"approval_sha256": None, "signature": None},
    }


def effect_request(digest="b" * 64):
    return {
        "effect_id": "effect-1", "project_id": "intercommunicationsenhancements", "task_id": "task-1",
        "message_id": "msg-1", "idempotency_key": "effect-key-1", "operation": "WRITE_SOURCE",
        "target": {"system": "github", "resource": "design/file.txt"}, "request_sha256": digest,
        "committing_agent": {"agent_id": "primary", "agent_instance_id": "p-1", "principal_id": "principal:p-1"},
    }


class ApprovalLedgerTests(unittest.TestCase):
    def test_single_use_approval_consumes_once(self):
        ledger = ApprovalLedger(); ledger.register(approval_fixture(), now=NOW)
        consumed = ledger.consume("intercommunicationsenhancements", "approval-atomic-1", operation_class="WRITE_SOURCE", target_system="github", target_resource="design/file.txt", scope_digest="a" * 64, expected_version=0, now=NOW)
        self.assertEqual(consumed.version, 1)
        self.assertEqual(consumed.record["status"], "CONSUMED")
        with self.assertRaises((ApprovalDenied, StateConflict)):
            ledger.consume("intercommunicationsenhancements", "approval-atomic-1", operation_class="WRITE_SOURCE", target_system="github", target_resource="design/file.txt", scope_digest="a" * 64, expected_version=0, now=NOW)

    def test_concurrent_consumers_only_one_wins(self):
        ledger = ApprovalLedger(); ledger.register(approval_fixture(), now=NOW)
        def attempt():
            try:
                ledger.consume("intercommunicationsenhancements", "approval-atomic-1", operation_class="WRITE_SOURCE", target_system="github", target_resource="design/file.txt", scope_digest="a" * 64, expected_version=0, now=NOW)
                return "WIN"
            except (ApprovalDenied, StateConflict):
                return "LOSE"
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: attempt(), range(2)))
        self.assertEqual(results.count("WIN"), 1)
        self.assertEqual(results.count("LOSE"), 1)

    def test_scope_mismatch_denied(self):
        ledger = ApprovalLedger(); ledger.register(approval_fixture(), now=NOW)
        with self.assertRaises(ApprovalDenied):
            ledger.consume("intercommunicationsenhancements", "approval-atomic-1", operation_class="WRITE_SOURCE", target_system="github", target_resource="main.py", scope_digest="a" * 64, expected_version=0, now=NOW)


class EffectLedgerTests(unittest.TestCase):
    def test_replay_matches_existing_effect(self):
        ledger = EffectLedger()
        disposition, prepared = ledger.prepare(effect_request(), now=NOW)
        self.assertEqual(disposition, "PREPARED")
        replay, same = ledger.prepare(effect_request(), now=NOW)
        self.assertEqual(replay, "REPLAY_MATCHED")
        self.assertEqual(same.record["effect_id"], prepared.record["effect_id"])

    def test_digest_collision_rejected(self):
        ledger = EffectLedger(); ledger.prepare(effect_request(), now=NOW)
        with self.assertRaises(EffectConflict): ledger.prepare(effect_request("c" * 64), now=NOW)

    def test_commit_then_retry_returns_duplicate_noop(self):
        ledger = EffectLedger(); _, prepared = ledger.prepare(effect_request(), now=NOW)
        committed = ledger.commit("intercommunicationsenhancements", "effect-key-1", request_sha256="b" * 64, external_receipt={"commit": "abc"}, result={"ok": True}, resulting_version="abc", expected_version=prepared.version, now=NOW)
        self.assertEqual(committed.record["status"], "COMMITTED")
        duplicate = ledger.commit("intercommunicationsenhancements", "effect-key-1", request_sha256="b" * 64, external_receipt={"commit": "abc"}, result={"ok": True}, resulting_version="abc", expected_version=committed.version, now=NOW)
        self.assertEqual(duplicate.record["status"], "DUPLICATE_NOOP")
        self.assertIsNone(duplicate.record["committed_at_utc"])
        self.assertEqual(ledger.get("intercommunicationsenhancements", "effect-key-1").record["status"], "COMMITTED")

    def test_unknown_state_does_not_claim_success(self):
        ledger = EffectLedger(); _, prepared = ledger.prepare(effect_request(), now=NOW)
        unknown = ledger.mark_unknown("intercommunicationsenhancements", "effect-key-1", expected_version=prepared.version)
        self.assertEqual(unknown.record["status"], "UNKNOWN")
        self.assertIsNone(unknown.record["committed_at_utc"])
        failed = ledger.fail_unknown("intercommunicationsenhancements", "effect-key-1", expected_version=unknown.version, evidence_refs=["reconcile:no-commit"])
        self.assertEqual(failed.record["status"], "FAILED")


if __name__ == "__main__":
    unittest.main()
