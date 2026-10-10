import copy
import unittest

from shadow_projection import assert_semantic_projection, project_v2_to_v3, shadow_projection_fingerprint


def sample_message(**overrides):
    message = {
        "schema": "org-agent-mesh/message/v2",
        "protocol_version": "2.4.0-alpha.1",
        "id": "msg-001",
        "project_id": "intercommunicationsenhancements",
        "destination_project_id": "intercommunicationsenhancements",
        "timestamp_utc": "2026-10-04T03:00:00Z",
        "from_agent": "primary",
        "from_agent_instance_id": "primary-test-001",
        "from_role": "PRIMARY",
        "to": ["project-forum", "MANAGER"],
        "kind": "DECISION",
        "priority": "high",
        "subject": "Test decision",
        "summary": "Projection fixture",
        "applies_to_state": {"state": "fixture"},
        "evidence": [{"type": "test", "id": "e1"}],
        "artifacts": [{"id": "a1", "sha256": "0" * 64}],
        "reply_to": None,
        "supersedes": [],
        "requires_ack": True,
        "tags": ["fixture"],
        "correlation_id": "corr-001",
        "causation_id": None,
        "idempotency_key": "idem-001",
        "expires_at_utc": None,
    }
    message.update(overrides)
    return message


class ShadowProjectionTests(unittest.TestCase):
    def test_projection_is_deterministic(self):
        first = project_v2_to_v3(sample_message())
        second = project_v2_to_v3(sample_message())
        self.assertEqual(first, second)
        self.assertEqual(shadow_projection_fingerprint(sample_message()), first["integrity"]["canonical_envelope_sha256"])

    def test_protected_semantics_survive_projection(self):
        v2 = sample_message()
        v3 = project_v2_to_v3(v2)
        self.assertTrue(assert_semantic_projection(v2, v3))
        self.assertEqual(v3["class"], "DECISION")
        self.assertEqual(v3["delivery"]["ack_policy"], "EXECUTION")
        self.assertEqual(v3["trust"]["trust_class"], "EXECUTION_EVIDENCE")

    def test_projection_does_not_mutate_source(self):
        v2 = sample_message()
        original = copy.deepcopy(v2)
        project_v2_to_v3(v2)
        self.assertEqual(v2, original)

    def test_cross_project_v2_message_is_rejected(self):
        with self.assertRaises(ValueError):
            project_v2_to_v3(sample_message(destination_project_id="duo-open"))

    def test_missing_identity_is_rejected(self):
        v2 = sample_message()
        v2["from_agent_instance_id"] = ""
        with self.assertRaises(ValueError):
            project_v2_to_v3(v2)

    def test_idempotency_falls_back_to_message_id(self):
        v3 = project_v2_to_v3(sample_message(idempotency_key=None))
        self.assertEqual(v3["delivery"]["idempotency_key"], "msg-001")

    def test_no_ack_maps_to_none(self):
        v3 = project_v2_to_v3(sample_message(requires_ack=False))
        self.assertEqual(v3["delivery"]["ack_policy"], "NONE")

    def test_payload_tamper_is_detected(self):
        v2 = sample_message()
        v3 = project_v2_to_v3(v2)
        v3["payload"]["summary"] = "tampered"
        with self.assertRaises(AssertionError):
            assert_semantic_projection(v2, v3)


if __name__ == "__main__":
    unittest.main()
