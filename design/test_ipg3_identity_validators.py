from datetime import datetime, timezone
import unittest

from ipg3_identity_validators import validate_agent_principal
from ipg3_validators import IPG3ValidationError

NOW = datetime(2026, 10, 4, 4, 0, 0, tzinfo=timezone.utc)


def principal_fixture():
    return {
        "schema": "org-agent-mesh/agent-principal/v1-draft",
        "principal_id": "principal-0001",
        "issuer": "test-issuer",
        "subject": "agent-primary",
        "project_id": "intercommunicationsenhancements",
        "agent_id": "primary",
        "agent_instance_id": "p-1",
        "role": "PRIMARY",
        "capability_claims": ["READ_SOURCE", "PUBLISH_MESSAGE"],
        "issued_at_utc": "2026-10-04T03:00:00Z",
        "expires_at_utc": "2026-10-04T05:00:00Z",
        "key_binding": {"key_id": "key-1", "algorithm": "TEST-SIGN", "public_key_fingerprint": "fingerprint-00000001"},
        "revocation": {"registry": "test-registry", "credential_version": 1},
        "integrity": {
            "credential_sha256": "6" * 64,
            "signature": {"algorithm": "TEST-SIGN", "key_id": "key-1", "value": "test-signature"}
        }
    }


class PrincipalTests(unittest.TestCase):
    def test_relationally_valid_principal(self):
        self.assertTrue(validate_agent_principal(principal_fixture(), expected_project_id="intercommunicationsenhancements", expected_agent_id="primary", expected_agent_instance_id="p-1", local_capability_ceiling={"READ_SOURCE", "PUBLISH_MESSAGE"}, allowed_algorithms={"TEST-SIGN"}, now=NOW))

    def test_forged_project_rejected(self):
        record = principal_fixture(); record["project_id"] = "duo-open"
        with self.assertRaises(IPG3ValidationError):
            validate_agent_principal(record, expected_project_id="intercommunicationsenhancements", now=NOW)

    def test_capability_claim_outside_local_ceiling_rejected(self):
        record = principal_fixture(); record["capability_claims"].append("DELETE_DATA")
        with self.assertRaises(IPG3ValidationError):
            validate_agent_principal(record, expected_project_id="intercommunicationsenhancements", local_capability_ceiling={"READ_SOURCE", "PUBLISH_MESSAGE"}, now=NOW)

    def test_signature_key_binding_mismatch_rejected(self):
        record = principal_fixture(); record["integrity"]["signature"]["key_id"] = "other-key"
        with self.assertRaises(IPG3ValidationError):
            validate_agent_principal(record, expected_project_id="intercommunicationsenhancements", now=NOW)

    def test_expired_principal_rejected(self):
        record = principal_fixture(); record["expires_at_utc"] = "2026-10-04T03:30:00Z"
        with self.assertRaises(IPG3ValidationError):
            validate_agent_principal(record, expected_project_id="intercommunicationsenhancements", now=NOW)


if __name__ == "__main__":
    unittest.main()
