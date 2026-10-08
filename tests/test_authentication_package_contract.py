import copy
import json
import unittest
from pathlib import Path

from org_agent_mesh.authentication_package_contract import (
    validate_factor_policy,
    validate_package_dependency_patterns,
)

ROOT = Path(__file__).resolve().parents[1]


class AuthenticationPackageContractTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT / "governance/AUTHENTICATION_FACTOR_POLICY.json").read_text())
        self.dependency_map = {
            "shared_patterns": [
                "AGENT_BOOTSTRAP.json",
                "BOOTSTRAP_ORDER.json",
                "governance/*.json",
                "protocols/*.md",
                "org_agent_mesh/*.py",
                "schemas/*.json",
                "templates/new-project/*.json",
                "governance/AUTHENTICATION_FACTOR_POLICY.json",
                "protocols/authentication_factor_gateway.md",
                "protocols/sip_sms_transport.md",
                "org_agent_mesh/authentication_gateway.py",
                "org_agent_mesh/authentication_package_contract.py",
                "org_agent_mesh/sms_transports.py",
                "schemas/authentication_attestation.schema.json",
            ]
        }

    def test_reference_policy_passes(self):
        validate_factor_policy(self.policy)

    def test_optional_totp_rejected(self):
        p = copy.deepcopy(self.policy); p["factors"]["baseline"]["required_for"] = []
        with self.assertRaisesRegex(ValueError, "mandatory TOTP"):
            validate_factor_policy(p)

    def test_inline_totp_seed_rejected(self):
        p = copy.deepcopy(self.policy); p["factors"]["baseline"]["secret_source"] = "INLINE"
        with self.assertRaisesRegex(ValueError, "TOTP secret"):
            validate_factor_policy(p)

    def test_missing_matched_counter_replay_protection_rejected(self):
        p = copy.deepcopy(self.policy); p["factors"]["baseline"]["replay_protection"] = "BOOLEAN_ONLY"
        with self.assertRaisesRegex(ValueError, "matched-counter"):
            validate_factor_policy(p)

    def test_missing_microsoft_rejected(self):
        p = copy.deepcopy(self.policy); p["factors"]["tertiary"]["method"] = "NONE"
        with self.assertRaisesRegex(ValueError, "Microsoft Authenticator"):
            validate_factor_policy(p)

    def test_hardcoded_entra_context_rejected(self):
        p = copy.deepcopy(self.policy); p["factors"]["tertiary"]["authentication_context_source"] = "c1"
        with self.assertRaisesRegex(ValueError, "must not be hard-coded"):
            validate_factor_policy(p)

    def test_unvalidated_microsoft_tokens_rejected(self):
        p = copy.deepcopy(self.policy); p["factors"]["tertiary"]["jwt_signature_issuer_audience_expiry_validation"] = "OPTIONAL"
        with self.assertRaisesRegex(ValueError, "cryptographic validation"):
            validate_factor_policy(p)

    def test_sms_strong_factor_escalation_rejected(self):
        p = copy.deepcopy(self.policy); p["strong_independent_methods"].append("SMS_OTP")
        with self.assertRaisesRegex(ValueError, "strong independent factor set drifted|SMS incorrectly elevated"):
            validate_factor_policy(p)

    def test_sms_plaintext_storage_rejected(self):
        p = copy.deepcopy(self.policy); p["factors"]["fallback"]["store_plaintext_code"] = True
        with self.assertRaisesRegex(ValueError, "plaintext"):
            validate_factor_policy(p)

    def test_sms_excessive_attempts_rejected(self):
        p = copy.deepcopy(self.policy); p["factors"]["fallback"]["max_attempts"] = 8
        with self.assertRaisesRegex(ValueError, "attempt limit"):
            validate_factor_policy(p)

    def test_missing_exact_runtime_component_rejected(self):
        d = copy.deepcopy(self.dependency_map)
        d["shared_patterns"].remove("org_agent_mesh/authentication_gateway.py")
        with self.assertRaisesRegex(ValueError, "omits auth-bearing components"):
            validate_package_dependency_patterns(d)

    def test_complete_dependency_contract_passes(self):
        validate_package_dependency_patterns(self.dependency_map)

    def test_package_builder_invokes_auth_contract(self):
        source = (ROOT / "tools/build_agent_packages.py").read_text()
        self.assertIn("validate_factor_policy(factor_policy)", source)
        self.assertIn("validate_package_dependency_patterns(dependency_map)", source)

    def test_sip_tls_cannot_be_disabled_in_policy(self):
        p = copy.deepcopy(self.policy)
        p["factors"]["fallback"]["sip_transport"]["tls_required_default"] = False
        with self.assertRaisesRegex(ValueError, "tls_required_default"):
            validate_factor_policy(p)

    def test_sip_gateway_allowlist_required(self):
        p = copy.deepcopy(self.policy)
        p["factors"]["fallback"]["sip_transport"]["gateway_host_allowlist_required"] = False
        with self.assertRaisesRegex(ValueError, "gateway_host_allowlist_required"):
            validate_factor_policy(p)

    def test_sip_interworking_must_be_explicit(self):
        p = copy.deepcopy(self.policy)
        p["factors"]["fallback"]["sip_transport"]["provider_sms_interworking_required"] = False
        with self.assertRaisesRegex(ValueError, "provider_sms_interworking_required"):
            validate_factor_policy(p)

    def test_sip_credentials_must_stay_external(self):
        p = copy.deepcopy(self.policy)
        p["factors"]["fallback"]["sip_transport"]["credentials_source"] = "INLINE"
        with self.assertRaisesRegex(ValueError, "credentials_source"):
            validate_factor_policy(p)

    def test_raw_phone_config_denied(self):
        p = copy.deepcopy(self.policy)
        p["factors"]["fallback"]["sip_transport"]["raw_phone_number_in_configuration"] = "ALLOW"
        with self.assertRaisesRegex(ValueError, "raw_phone_number"):
            validate_factor_policy(p)

    def test_only_200_202_success(self):
        p = copy.deepcopy(self.policy)
        p["factors"]["fallback"]["sip_transport"]["accepted_success_responses"] = [200, 202, 302]
        with self.assertRaisesRegex(ValueError, "success response"):
            validate_factor_policy(p)

    def test_transport_runtime_explicitly_packaged(self):
        d = copy.deepcopy(self.dependency_map)
        d["shared_patterns"].remove("org_agent_mesh/sms_transports.py")
        with self.assertRaisesRegex(ValueError, "omits auth-bearing components"):
            validate_package_dependency_patterns(d)

    def test_transport_protocol_explicitly_packaged(self):
        d = copy.deepcopy(self.dependency_map)
        d["shared_patterns"].remove("protocols/sip_sms_transport.md")
        with self.assertRaisesRegex(ValueError, "omits auth-bearing components"):
            validate_package_dependency_patterns(d)


if __name__ == "__main__":
    unittest.main()
