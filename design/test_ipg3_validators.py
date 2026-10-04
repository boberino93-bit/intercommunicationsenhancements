from datetime import datetime, timezone
import unittest

from ipg3_validators import (
    IPG3ValidationError,
    causal_event_hash,
    validate_cross_project_exchange,
    validate_delegation_contract,
    validate_effect_receipt,
    validate_human_approval,
    validate_trust_promotion,
    verify_causal_chain,
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
        "task_id": "task-1", "effect_id": None,
        "issued_at_utc": "2026-10-04T03:00:00Z", "expires_at_utc": "2026-10-04T05:00:00Z",
        "max_uses": 1, "uses": 0, "status": "ISSUED",
        "decision_evidence_ref": "message:approval",
        "integrity": {"approval_sha256": None, "signature": None},
    }


def effect_fixture():
    return {
        "schema": "org-agent-mesh/effect-receipt/v1-draft", "effect_id": "effect-0001",
        "project_id": "intercommunicationsenhancements", "task_id": "task-1", "message_id": "msg-1",
        "idempotency_key": "effect-key-1", "operation": "WRITE_SOURCE",
        "target": {"system": "github", "resource": "design/test.txt"}, "request_sha256": "3" * 64,
        "committing_agent": {"agent_id": "primary", "agent_instance_id": "p-1", "principal_id": "principal:p-1"},
        "status": "COMMITTED", "prepared_at_utc": "2026-10-04T03:10:00Z", "committed_at_utc": "2026-10-04T03:11:00Z",
        "result": {"ok": True}, "resulting_version": "abc123", "external_receipt": {"commit": "abc123"},
        "replay_disposition": "FIRST_COMMIT", "evidence_refs": ["github:abc123"],
    }


def delegation_fixture():
    return {
        "schema": "org-agent-mesh/delegation-contract/v1-draft", "contract_id": "delegation-0001",
        "project_id": "intercommunicationsenhancements", "created_at_utc": "2026-10-04T03:00:00Z", "expires_at_utc": "2026-10-04T05:00:00Z",
        "delegator": {"agent_id": "primary", "agent_instance_id": "p-1", "role": "PRIMARY"},
        "assignee": {"type": "ROLE", "id": "RESEARCH"}, "objective": "Evaluate protocol candidate",
        "scope": {"in_scope": ["design"], "out_of_scope": ["main-runtime"]},
        "source_of_truth": ["repository"], "allowed_tools": ["GitHub"],
        "capability_ceiling": ["READ_SOURCE"], "write_boundaries": [],
        "evidence_requirements": ["exact revision"], "output_contract": {"type": "report"},
        "completion_criteria": ["report produced"], "failure_criteria": ["identity ambiguous"],
        "parent_task_id": "task-1", "parent_trace_id": "trace-1", "status": "ACTIVE",
        "integrity": {"contract_sha256": None, "signature": None},
    }


def trust_fixture(trust_class="EXTERNAL_UNTRUSTED", validation_state="CONTENT_VERIFIED"):
    return {
        "schema": "org-agent-mesh/trust-provenance-record/v1-draft",
        "record_id": "trust-0001", "project_id": "intercommunicationsenhancements",
        "subject": {"type": "RESEARCH", "id": "research-1"}, "trust_class": trust_class,
        "validation_state": validation_state,
        "provenance": [{"source_type": "EXTERNAL_RESEARCH", "source_id": "paper", "revision": "1", "path": None, "sha256": "4" * 64, "observed_at_utc": "2026-10-04T03:00:00Z"}],
        "created_by": {"agent_id": "research", "agent_instance_id": "r-1", "principal_id": None},
        "created_at_utc": "2026-10-04T03:00:00Z", "expires_at_utc": None,
        "promotion_history": [], "integrity": {"content_sha256": "5" * 64, "signature": None},
    }


def causal_event(sequence, event_id, previous_hash=None, parent_event_id=None):
    event = {
        "schema": "org-agent-mesh/causal-event/v1-draft", "event_id": event_id,
        "project_id": "intercommunicationsenhancements", "event_sequence": sequence,
        "occurred_at_utc": f"2026-10-04T03:{sequence:02d}:00Z",
        "actor": {"agent_id": "primary", "agent_instance_id": "p-1", "principal_id": None, "role": "PRIMARY"},
        "event_type": "MESSAGE_PUBLISHED", "trace_id": "trace-1", "correlation_id": "corr-1", "causation_id": None,
        "parent_event_id": parent_event_id, "task_id": "task-1", "resource_refs": [], "before_version": None,
        "after_version": None, "evidence_refs": [], "previous_event_hash": previous_hash, "event_hash": "0" * 64, "signature": None,
    }
    event["event_hash"] = causal_event_hash(event)
    return event


class CrossProjectTests(unittest.TestCase):
    def test_valid_exchange(self): self.assertTrue(validate_cross_project_exchange(exchange_fixture(), now=NOW))
    def test_same_project_exchange_rejected(self):
        record = exchange_fixture(); record["destination_project_id"] = record["source_project_id"]
        with self.assertRaises(IPG3ValidationError): validate_cross_project_exchange(record, now=NOW)
    def test_requester_session_mismatch_rejected(self):
        record = exchange_fixture(); record["requester"]["agent_instance_id"] = "forged"
        with self.assertRaises(IPG3ValidationError): validate_cross_project_exchange(record, now=NOW)
    def test_scope_overrun_rejected(self):
        record = exchange_fixture(); record["artifacts"][0]["size_bytes"] = 1001
        with self.assertRaises(IPG3ValidationError): validate_cross_project_exchange(record, now=NOW)
    def test_unsanitized_exchange_rejected(self):
        record = exchange_fixture(); record["sanitization"]["remove_secrets"] = False
        with self.assertRaises(IPG3ValidationError): validate_cross_project_exchange(record, now=NOW)


class ApprovalTests(unittest.TestCase):
    def test_valid_approval(self): self.assertTrue(validate_human_approval(approval_fixture(), now=NOW))
    def test_replay_exhausted_approval_rejected(self):
        record = approval_fixture(); record["uses"] = 1
        with self.assertRaises(IPG3ValidationError): validate_human_approval(record, now=NOW)
    def test_consumed_state_requires_spent_uses(self):
        record = approval_fixture(); record["status"] = "CONSUMED"
        with self.assertRaises(IPG3ValidationError): validate_human_approval(record, now=NOW)


class EffectReceiptTests(unittest.TestCase):
    def test_valid_commit(self): self.assertTrue(validate_effect_receipt(effect_fixture()))
    def test_duplicate_noop_cannot_claim_second_commit(self):
        record = effect_fixture(); record["status"] = "DUPLICATE_NOOP"; record["replay_disposition"] = "REPLAY_MATCHED"
        with self.assertRaises(IPG3ValidationError): validate_effect_receipt(record)
    def test_commit_before_prepare_rejected(self):
        record = effect_fixture(); record["committed_at_utc"] = "2026-10-04T03:09:00Z"
        with self.assertRaises(IPG3ValidationError): validate_effect_receipt(record)


class DelegationTests(unittest.TestCase):
    def test_capability_ceiling_is_subset_of_parent(self):
        self.assertTrue(validate_delegation_contract(delegation_fixture(), expected_project_id="intercommunicationsenhancements", parent_capabilities={"READ_SOURCE", "WRITE_SOURCE"}, child_capabilities={"READ_SOURCE"}, now=NOW))
    def test_child_escalation_rejected(self):
        with self.assertRaises(IPG3ValidationError): validate_delegation_contract(delegation_fixture(), parent_capabilities={"READ_SOURCE"}, child_capabilities={"WRITE_SOURCE"}, now=NOW)
    def test_scope_contradiction_rejected(self):
        record = delegation_fixture(); record["scope"]["out_of_scope"] = ["design"]
        with self.assertRaises(IPG3ValidationError): validate_delegation_contract(record, now=NOW)


class TrustPromotionTests(unittest.TestCase):
    def test_external_can_become_verified_with_evidence(self):
        self.assertTrue(validate_trust_promotion(trust_fixture(), "VERIFIED_FACT", decision_id="decision-1", validator_count=1))
    def test_reflection_cannot_jump_to_authoritative_config(self):
        with self.assertRaises(IPG3ValidationError): validate_trust_promotion(trust_fixture("AGENT_REFLECTION"), "AUTHORITATIVE_CONFIG", decision_id="decision-1", validator_count=2)
    def test_quarantined_content_cannot_be_promoted(self):
        with self.assertRaises(IPG3ValidationError): validate_trust_promotion(trust_fixture("QUARANTINED"), "DERIVED_KNOWLEDGE", decision_id="decision-1")


class CausalChainTests(unittest.TestCase):
    def test_valid_hash_linked_chain(self):
        first = causal_event(0, "event-0")
        second = causal_event(1, "event-1", first["event_hash"], "event-0")
        self.assertTrue(verify_causal_chain([first, second]))
    def test_tamper_detected(self):
        first = causal_event(0, "event-0"); first["task_id"] = "tampered"
        with self.assertRaises(IPG3ValidationError): verify_causal_chain([first])
    def test_predecessor_mismatch_detected(self):
        first = causal_event(0, "event-0"); second = causal_event(1, "event-1", "f" * 64, "event-0")
        with self.assertRaises(IPG3ValidationError): verify_causal_chain([first, second])


if __name__ == "__main__":
    unittest.main()
