import base64
import hashlib
import hmac
import struct
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from org_agent_mesh.authentication_gateway import (
    AuthenticationError,
    GITHUB_PROOF_DISPOSITION,
    InMemoryReplayStore,
    MicrosoftAuthenticatorFactor,
    MicrosoftIdentityResult,
    SmsFallbackFactor,
    TotpFactor,
    authorize_factor_set,
    new_challenge,
)
from org_agent_mesh.totp_verifier import match_totp_counter, verify_totp


def code_for(secret_b32: str, unix_time: int, digits: int = 6) -> str:
    key = base64.b32decode(secret_b32)
    counter = unix_time // 30
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(value % (10 ** digits)).zfill(digits)


class MemorySms:
    def __init__(self):
        self.sent = []

    def send(self, destination_ref, message, *, idempotency_key):
        self.sent.append((destination_ref, message, idempotency_key))
        return "provider-message-1"


class AuthenticationGatewayTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 8, 6, 20, tzinfo=timezone.utc)
        self.secret = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        self.key = b"K" * 32
        self.challenge = new_challenge(
            case_id="AUTH-TEST-42",
            principal_id="robert_leonard",
            action_digest="abc123",
            consequence_class="SECURITY_OR_CREDENTIAL_BOUNDARY_CHANGE",
            now=self.now,
        )

    def totp(self):
        return TotpFactor(lambda principal_id: self.secret, InMemoryReplayStore(), self.key)

    def test_rfc6238_known_vector_six_digits(self):
        self.assertEqual(code_for(self.secret, 59), "287082")
        self.assertTrue(verify_totp(self.secret, "287082", unix_time=59, window=0))

    def test_match_totp_counter_returns_exact_adjacent_counter(self):
        previous = code_for(self.secret, int(self.now.timestamp()) - 30)
        expected = (int(self.now.timestamp()) // 30) - 1
        self.assertEqual(match_totp_counter(self.secret, previous, unix_time=int(self.now.timestamp()), window=1), expected)

    def test_totp_attestation_bound_to_case_and_action(self):
        factor = self.totp()
        att = factor.verify(self.challenge, code_for(self.secret, int(self.now.timestamp())), now=self.now)
        self.assertEqual(att.case_id, self.challenge.case_id)
        self.assertEqual(att.action_digest, self.challenge.action_digest)

    def test_totp_current_counter_replay_denied(self):
        factor = self.totp(); code = code_for(self.secret, int(self.now.timestamp()))
        factor.verify(self.challenge, code, now=self.now)
        with self.assertRaisesRegex(AuthenticationError, "replay"):
            factor.verify(self.challenge, code, now=self.now)

    def test_totp_adjacent_window_replay_denied_by_matched_counter(self):
        factor = self.totp(); code = code_for(self.secret, int(self.now.timestamp()) - 30)
        factor.verify(self.challenge, code, now=self.now)
        with self.assertRaisesRegex(AuthenticationError, "replay"):
            factor.verify(self.challenge, code, now=self.now + timedelta(seconds=1))

    def test_totp_secret_is_runtime_resolved(self):
        calls = []
        factor = TotpFactor(lambda pid: (calls.append(pid) or self.secret), InMemoryReplayStore(), self.key)
        factor.verify(self.challenge, code_for(self.secret, int(self.now.timestamp())), now=self.now)
        self.assertEqual(calls, ["robert_leonard"])

    def microsoft_result(self, **overrides):
        values = dict(
            principal_id="robert_leonard",
            tenant_id="tenant-a",
            token_id="jti-1",
            challenge_nonce=self.challenge.nonce,
            authenticated_at=self.now,
            authentication_context_id="tenant-configured-context",
            authenticator_satisfied=True,
            token_validated=True,
            phishing_resistant=False,
        )
        values.update(overrides)
        return MicrosoftIdentityResult(**values)

    def microsoft(self):
        return MicrosoftAuthenticatorFactor(
            allowed_tenant_ids={"tenant-a"},
            required_authentication_context_id="tenant-configured-context",
            replay_store=InMemoryReplayStore(),
            attestation_key=self.key,
        )

    def test_microsoft_accepts_bound_validated_result(self):
        att = self.microsoft().verify(self.challenge, self.microsoft_result(), now=self.now)
        self.assertEqual(att.method, "MICROSOFT_ENTRA_AUTHENTICATOR")

    def test_microsoft_rejects_unvalidated_token(self):
        with self.assertRaisesRegex(AuthenticationError, "not_validated"):
            self.microsoft().verify(self.challenge, self.microsoft_result(token_validated=False), now=self.now)

    def test_microsoft_rejects_wrong_tenant(self):
        with self.assertRaisesRegex(AuthenticationError, "tenant_mismatch"):
            self.microsoft().verify(self.challenge, self.microsoft_result(tenant_id="evil"), now=self.now)

    def test_microsoft_rejects_wrong_nonce(self):
        with self.assertRaisesRegex(AuthenticationError, "nonce_mismatch"):
            self.microsoft().verify(self.challenge, self.microsoft_result(challenge_nonce="wrong"), now=self.now)

    def test_microsoft_rejects_wrong_auth_context(self):
        with self.assertRaisesRegex(AuthenticationError, "context_mismatch"):
            self.microsoft().verify(self.challenge, self.microsoft_result(authentication_context_id="c99"), now=self.now)

    def test_microsoft_token_replay_denied(self):
        factor = self.microsoft(); result = self.microsoft_result()
        factor.verify(self.challenge, result, now=self.now)
        with self.assertRaisesRegex(AuthenticationError, "replay"):
            factor.verify(self.challenge, result, now=self.now)

    def test_sms_requires_protected_destination_reference(self):
        sms = SmsFallbackFactor(transport=MemorySms(), pepper=b"P" * 32, attestation_key=self.key)
        with self.assertRaisesRegex(AuthenticationError, "protected_reference"):
            sms.issue(self.challenge, "+15555550123", now=self.now)

    def test_sms_plaintext_code_not_stored(self):
        transport = MemorySms(); sms = SmsFallbackFactor(transport=transport, pepper=b"P" * 32, attestation_key=self.key)
        sms.issue(self.challenge, "vault://principals/robert/mobile", now=self.now)
        code = transport.sent[0][1].split()[2].rstrip(".")
        record = sms._records[self.challenge.challenge_id]
        self.assertNotIn(code, record.digest)
        self.assertNotEqual(code, record.digest)

    def test_sms_single_use(self):
        transport = MemorySms(); sms = SmsFallbackFactor(transport=transport, pepper=b"P" * 32, attestation_key=self.key)
        sms.issue(self.challenge, "vault://principals/robert/mobile", now=self.now)
        code = transport.sent[0][1].split()[2].rstrip(".")
        sms.verify(self.challenge, code, now=self.now)
        with self.assertRaisesRegex(AuthenticationError, "sms_replay_denied"):
            sms.verify(self.challenge, code, now=self.now)

    def test_sms_attempt_limit(self):
        transport = MemorySms(); sms = SmsFallbackFactor(transport=transport, pepper=b"P" * 32, attestation_key=self.key)
        sms.issue(self.challenge, "vault://principals/robert/mobile", now=self.now)
        for _ in range(3):
            with self.assertRaisesRegex(AuthenticationError, "invalid_sms_code"):
                sms.verify(self.challenge, "00000000", now=self.now)
        with self.assertRaisesRegex(AuthenticationError, "attempt_limit"):
            sms.verify(self.challenge, "11111111", now=self.now)

    def test_high_consequence_rejects_totp_alone(self):
        t = self.totp(); tatt = t.verify(self.challenge, code_for(self.secret, int(self.now.timestamp())), now=self.now)
        with self.assertRaisesRegex(AuthenticationError, "strong_independent_step_up_required"):
            authorize_factor_set(challenge=self.challenge, attestations=[tatt], attestation_key=self.key, now=self.now)

    def test_high_consequence_accepts_totp_plus_microsoft(self):
        tatt = self.totp().verify(self.challenge, code_for(self.secret, int(self.now.timestamp())), now=self.now)
        matt = self.microsoft().verify(self.challenge, self.microsoft_result(), now=self.now)
        result = authorize_factor_set(challenge=self.challenge, attestations=[tatt, matt], attestation_key=self.key, now=self.now)
        self.assertEqual(result, "TOTP_PLUS_STRONG_INDEPENDENT_PROOF_VERIFIED")

    def test_high_consequence_accepts_totp_plus_verified_github_disposition(self):
        tatt = self.totp().verify(self.challenge, code_for(self.secret, int(self.now.timestamp())), now=self.now)
        result = authorize_factor_set(
            challenge=self.challenge,
            attestations=[tatt],
            attestation_key=self.key,
            now=self.now,
            independent_proof_disposition=GITHUB_PROOF_DISPOSITION,
        )
        self.assertEqual(result, "TOTP_PLUS_STRONG_INDEPENDENT_PROOF_VERIFIED")

    def test_high_consequence_rejects_totp_plus_sms(self):
        tatt = self.totp().verify(self.challenge, code_for(self.secret, int(self.now.timestamp())), now=self.now)
        transport = MemorySms(); sms = SmsFallbackFactor(transport=transport, pepper=b"P" * 32, attestation_key=self.key)
        sms.issue(self.challenge, "vault://principals/robert/mobile", now=self.now)
        code = transport.sent[0][1].split()[2].rstrip(".")
        satt = sms.verify(self.challenge, code, now=self.now)
        with self.assertRaisesRegex(AuthenticationError, "strong_independent_step_up_required"):
            authorize_factor_set(challenge=self.challenge, attestations=[tatt, satt], attestation_key=self.key, now=self.now)

    def test_standard_protected_mutation_accepts_totp(self):
        standard = new_challenge(
            case_id="AUTH-STD",
            principal_id="robert_leonard",
            action_digest="digest",
            consequence_class="STANDARD_MUTATION",
            now=self.now,
        )
        att = self.totp().verify(standard, code_for(self.secret, int(self.now.timestamp())), now=self.now)
        self.assertEqual(authorize_factor_set(challenge=standard, attestations=[att], attestation_key=self.key, now=self.now), "TOTP_VERIFIED")

    def test_cross_case_attestation_mix_denied(self):
        att = self.totp().verify(self.challenge, code_for(self.secret, int(self.now.timestamp())), now=self.now)
        other = new_challenge(case_id="AUTH-OTHER", principal_id="robert_leonard", action_digest="other", consequence_class="STANDARD_MUTATION", now=self.now)
        with self.assertRaisesRegex(AuthenticationError, "factor_binding_mismatch"):
            authorize_factor_set(challenge=other, attestations=[att], attestation_key=self.key, now=self.now)

    def test_tampered_attestation_signature_denied(self):
        standard = new_challenge(case_id="AUTH-STD2", principal_id="robert_leonard", action_digest="digest2", consequence_class="STANDARD_MUTATION", now=self.now)
        att = self.totp().verify(standard, code_for(self.secret, int(self.now.timestamp())), now=self.now)
        tampered = replace(att, evidence_digest="0" * 64)
        with self.assertRaisesRegex(AuthenticationError, "signature_invalid"):
            authorize_factor_set(challenge=standard, attestations=[tampered], attestation_key=self.key, now=self.now)


if __name__ == "__main__":
    unittest.main()
