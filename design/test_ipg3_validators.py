from datetime import datetime, timezone
import unittest

from ipg3_validators import (
    IPG3ValidationError,
    validate_cross_project_exchange,
    validate_effect_receipt,
    validate_human_approval,
)


NOW = datetime(2026, 10, 4, 4, 0, 0, tzinfo=timezone.utc)


def exchange_fixture():
    return {
        "schema": "org-agent-mesh/cross-project-exchange/v2-draft",
        "exchange_id": "exchange-000001",
        "source_project_id": "intercommunicationsenhancements",
        "destination_project_id": "duo-open",
        "created_at_utc": "2026-10-04T03:00:00Z",
        "expires_at_utc": "2026-10-04T05:00:00Z",
        "requester": {"agent_id": "primary", "agent_instance_id": "p-1", "principal_id": "principal:p-1"},
        "source_session": {"project_id": "intercommunicationsenhancements", "agent_id": "primary", "agent_instance_id": "p-1", "capability": "CROSS_PROJECT_EXCHANGE"},
        "approval_id": "approval-1",
        "purpose": "share sanitized framework pattern",
        "scope": {"allowed_artifact_types": ["DESIGN"], "allowed_paths": ["design/*"], "max_artifacts": 2, "max_total_bytes": 1000},
        "sanitization": {"profile_id": "default", "profile_revision": "1", "remove_secrets": True, "remove_personal_data": True, "remove_project_instance_state": True, "validation_ref": "validation-1"},
        "artifacts": [{"artifact_id": "a1", "source_sha256": "0" * 64, "sanitized_sha256": "1" * 64, "size_bytes": 100, "trust_record_id": "trust-1"}],
        "delivery": {"idempotency_key": "exchange-000001", "transport": "adapter:test", "effect_receipt_id": None},
        "destination_validation": {"required": True, "validator_id": None, "decision": "PENDING"},
        "status": "DISPATCHED",
    }


def approval_fixture():
    return {
        "schema": "org-agent-mesh/human-approval/v1-draft",
        "approval_id": "approval-0001",
        "project_id": "intercommunicationsenhancements",
        "approver": {"principal_id": "human:owner", "display_ref": "owner"},
        "operation_class": "CROSS_PROJECT_EXCHANGE",
        "target": {"system": "agentbus", "resource": "exchange-000001", "scope_digest": "2" * 64},
        "task_id": "task-1",
        "effect_id": None,
        "issued_at_utc": "2026-10-04T03:00:00Z",
        "expires_at_utc": "2026-10-04T05:00:00Z",
        "max_uses": 1,
        "uses": 0,
        "status": "ISSUED",
        "decision_evidence_ref": "message:approval",
        "integrity": {"approval_sha256": None, "signature": None},
    }


def effect_fixture():
    return {
        "schema": "org-agent-mesh/effect-receipt/v1-draft",
        "effect_id": "effect-0001",
        "project_id": "intercommunicationsenhancements",
        "task_id": "task-1",
        "message_id": "msg-1",
        "idempotency_key": "effect-key-1",
        "operation": "WRITE_SOURCE",
        "target": {"system": "github", "resource": "design/test.txt"},
        "request_sha256": "3" * 64,
        "committing_agent": {"agent_id": "primary", "agent_instance_id": "p-1", "principal_id": "principal:p-1"},
        "status": "COMMITTED",
        "prepared_at_utc": "2026-10-04T03:10:00Z",
        "committed_at_utc": "2026-10-04T03:11:00Z",
        "result": {"ok": True},
        "resulting_version": "abc123",
        "external_receipt": {"commit": "abc123"},
        "replay_disposition": "FIRST_COMMIT",
        "evidence_refs": ["github:abc123"],
    }


class CrossProjectTests(unittest.TestCase):
    def test_valid_exchange(self):
        self.assertTrue(validate_cross_project_exchange(exchange_fixture(), now=NOW))

    def test_same_project_exchange_rejected(self):
        record = exchange_fixture()
        record["destination_project_id"] = record["source_project_id"]
        with self.assertRaises(IPG3ValidationError):
            validate_cross_project_exchange(record, now=NOW)

    def test_requester_session_mismatch_rejected(self):
        record = exchange_fixture()
        record["requester"]["agent_instance_id"] = "forged"
        with self.assertRaises(IPG3ValidationError):
            validate_cross_project_exchange(record, now=NOW)

    def test_scope_overrun_rejected(self):
        record = exchange_fixture()
        record["artifacts"][0]["size_bytes"] = 1001
        with self.assertRaises(IPG3ValidationError):
            validate_cross_project_exchange(record, now=NOW)

    def test_unsanitized_exchange_rejected(self):
        record = exchange_fixture()
        record["sanitization"]["remove_secrets"] = False
        with self.assertRaises(IPG3ValidationError):
            validate_cross_project_exchange(record, now=NOW)


class ApprovalTests(unittest.TestCase):
    def test_valid_approval(self):
        self.assertTrue(validate_human_approval(approval_fixture(), now=NOW))

    def test_replay_exhausted_approval_rejected(self):
        record = approval_fixture()
        record["uses"] = 1
        with self.assertRaises(IPG3ValidationError):
            validate_human_approval(record, now=NOW)

    def test_consumed_state_requires_spent_uses(self):
        record = approval_fixture()
        record["status"] = "CONSUMED"
        with self.assertRaises(IPG3ValidationError):
            validate_human_approval(record, now=NOW)


class EffectReceiptTests(unittest.TestCase):
    def test_valid_commit(self):
        self.assertTrue(validate_effect_receipt(effect_fixture()))

    def test_duplicate_noop_cannot_claim_second_commit(self):
        record = effect_fixture()
        record["status"] = "DUPLICATE_NOOP"
        record["replay_disposition"] = "REPLAY_MATCHED"
        with self.assertRaises(IPG3ValidationError):
            validate_effect_receipt(record)

    def test_commit_before_prepare_rejected(self):
        record = effect_fixture()
        record["committed_at_utc"] = "2026-10-04T03:09:00Z"
        with self.assertRaises(IPG3ValidationError):
            validate_effect_receipt(record)


if __name__ == "__main__":
    unittest.main()
