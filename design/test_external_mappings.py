import unittest

from a2a_mapping import bind_external_request_to_local_authority, normalize_agent_card, normalize_artifact, normalize_message, normalize_task
from agntcy_mapping import AGNTCYMappingError, map_verified_identity_to_principal_claim, normalize_directory_record, normalize_slim_identity


class A2AMappingTests(unittest.TestCase):
    def test_agent_card_capabilities_do_not_become_local_permissions(self):
        card = {
            "name": "Remote Agent", "version": "1.0.0", "protocolVersion": "1.0",
            "supportedInterfaces": [{"url": "https://example.invalid/a2a"}],
            "capabilities": {"streaming": True, "pushNotifications": True},
            "securitySchemes": {"oauth2": {"type": "oauth2"}},
            "skills": [{"id": "code", "name": "Code"}],
        }
        normalized = normalize_agent_card(card)
        self.assertEqual(normalized["trust_class"], "EXTERNAL_UNTRUSTED")
        self.assertEqual(normalized["local_capability_grants"], [])
        self.assertTrue(normalized["remote_capability_claims"]["streaming"])

    def test_task_message_artifact_are_untrusted_until_local_binding(self):
        task = normalize_task({"id": "task-r1", "contextId": "ctx-1", "status": {"state": "working"}}, remote_agent_ref="agent-r")
        msg = normalize_message({"messageId": "msg-r1", "role": "user", "parts": [{"text": "do work"}]}, remote_agent_ref="agent-r", remote_task_id="task-r1")
        artifact = normalize_artifact({"artifactId": "artifact-r1", "parts": [{"text": "result"}]}, remote_agent_ref="agent-r", remote_task_id="task-r1")
        for item in (task, msg, artifact):
            self.assertFalse(item["local_authorized"])
            self.assertEqual(item["trust_class"], "EXTERNAL_UNTRUSTED")

    def test_local_binding_uses_only_locally_approved_capabilities(self):
        task = normalize_task({"id": "task-r1", "status": {"state": "working"}}, remote_agent_ref="agent-r")
        bound = bind_external_request_to_local_authority(task, project_id="intercommunicationsenhancements", delegation_contract_id="delegate-1", approved_capabilities={"READ_SOURCE"})
        self.assertTrue(bound["local_authorized"])
        self.assertEqual(bound["local_capabilities"], ["READ_SOURCE"])


class AGNTCYMappingTests(unittest.TestCase):
    def test_verified_spire_identity_is_identity_evidence_not_authority(self):
        evidence = normalize_slim_identity({
            "credential_method": "SPIRE", "application_identity": "spiffe://example.test/ns/default/sa/agent",
            "verified": True, "trust_domain": "example.test", "evidence_ref": "slim-session-1",
        })
        self.assertEqual(evidence["verification"]["strength"], "WORKLOAD_ATTESTED")
        self.assertFalse(evidence["local_authorized"])
        self.assertEqual(evidence["local_capability_grants"], [])

    def test_unverified_identity_cannot_enter_local_principal_issuance(self):
        evidence = normalize_slim_identity({"credential_method": "JWT", "application_identity": "agent@example", "verified": False})
        with self.assertRaises(AGNTCYMappingError):
            map_verified_identity_to_principal_claim(evidence, project_id="intercommunicationsenhancements", agent_id="remote", agent_instance_id="remote-1", local_capability_ceiling={"READ_SOURCE"}, requested_capabilities={"READ_SOURCE"})

    def test_remote_requested_capabilities_are_intersected_with_local_ceiling(self):
        evidence = normalize_slim_identity({"credential_method": "JWT", "application_identity": "remote-agent", "verified": True, "issuer": "https://issuer.invalid", "evidence_ref": "jwt-1"})
        request = map_verified_identity_to_principal_claim(evidence, project_id="intercommunicationsenhancements", agent_id="remote", agent_instance_id="remote-1", local_capability_ceiling={"READ_SOURCE"}, requested_capabilities={"READ_SOURCE", "DELETE_DATA"})
        self.assertEqual(request["candidate_capabilities"], ["READ_SOURCE"])
        self.assertFalse(request["authorized"])
        self.assertTrue(request["requires_local_issuer"])

    def test_signed_directory_record_remains_discovery_not_permission(self):
        record = normalize_directory_record({"id": "agent-directory-id", "skills": [{"name": "research"}]}, signature_verified=True, verification_ref="dir-signature-1")
        self.assertEqual(record["trust_class"], "VERIFIED_FACT")
        self.assertFalse(record["local_authorized"])
        self.assertEqual(record["local_capability_grants"], [])


if __name__ == "__main__":
    unittest.main()
