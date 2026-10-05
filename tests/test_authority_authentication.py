import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

from org_agent_mesh.authority_authentication import (
    AuthorityAuthenticationError,
    AuthorizationCase,
    build_action_digest,
    consume_authorization_case,
    resolve_registered_principal,
    validate_authentication_disposition,
    validate_authorization_case,
)

ROOT = Path(__file__).resolve().parents[1]


class AuthorityAuthenticationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.auth = json.loads((ROOT / "governance" / "AUTHORITY_AUTHENTICATION_POLICY.json").read_text())
        cls.root = json.loads((ROOT / "governance" / "ROOT_CHANGE_AUTHORITY.json").read_text())

    def test_registered_principal_must_be_explicit(self):
        with self.assertRaisesRegex(AuthorityAuthenticationError, "explicit_principal_claim_required"):
            resolve_registered_principal(self.root, claimed_name="")
        principal = resolve_registered_principal(self.root, claimed_name="Robert Leonard")
        self.assertEqual(principal.principal_id, "robert_leonard")

    def test_static_personal_facts_are_forbidden_authentication(self):
        kba = self.auth["knowledge_based_authentication"]
        self.assertFalse(kba["allowed"])
        for category in ("DATE_OF_BIRTH", "GOVERNMENT_ID_NUMBER", "FAMILY_NAME_OR_MAIDEN_NAME"):
            self.assertIn(category, kba["forbidden_categories"])

    def test_standard_case_does_not_overclaim_independent_authentication(self):
        principal, disposition = validate_authentication_disposition(
            self.auth,
            self.root,
            claimed_name="Robert Leonard",
            consequence_class="STANDARD_MUTATION",
        )
        self.assertEqual(principal.github_login, "boberino93-bit")
        self.assertEqual(disposition, "REGISTERED_PRINCIPAL_CLAIM_NOT_INDEPENDENTLY_AUTHENTICATED")

    def test_high_consequence_requires_human_performed_external_proof(self):
        with self.assertRaisesRegex(AuthorityAuthenticationError, "independent_principal_proof_required"):
            validate_authentication_disposition(
                self.auth,
                self.root,
                claimed_name="Robert Leonard",
                consequence_class="UNIVERSAL_GOVERNANCE_CHANGE",
            )
        with self.assertRaisesRegex(AuthorityAuthenticationError, "agent_created_authentication_proof_denied"):
            validate_authentication_disposition(
                self.auth,
                self.root,
                claimed_name="Robert Leonard",
                consequence_class="UNIVERSAL_GOVERNANCE_CHANGE",
                evidence_type="HUMAN_PERFORMED_REGISTERED_GITHUB_CHALLENGE",
                evidence_actor="boberino93-bit",
                evidence_payload="AUTH-1 nonce-1",
                case_id="AUTH-1",
                nonce="nonce-1",
                proof_created_by_agent=True,
            )

    def test_high_consequence_external_challenge_binds_case_and_registered_actor(self):
        principal, disposition = validate_authentication_disposition(
            self.auth,
            self.root,
            claimed_name="Robert Leonard",
            consequence_class="UNIVERSAL_GOVERNANCE_CHANGE",
            evidence_type="HUMAN_PERFORMED_REGISTERED_GITHUB_CHALLENGE",
            evidence_actor="boberino93-bit",
            evidence_payload="I confirm AUTH-42 challenge 7f3a9b",
            case_id="AUTH-42",
            nonce="7f3a9b",
        )
        self.assertEqual(principal.principal_id, "robert_leonard")
        self.assertEqual(disposition, "INDEPENDENT_REGISTERED_PRINCIPAL_PROOF_VERIFIED")

    def test_case_is_action_bound_and_single_use(self):
        principal = resolve_registered_principal(self.root, claimed_name="Robert Leonard")
        now = datetime.now(timezone.utc)
        target = "boberino93-bit/intercommunicationsenhancements"
        mutation = "REPOSITORY_OR_FILE_WRITE"
        scope = "update one bounded governance policy"
        consequence = "STANDARD_MUTATION"
        digest = build_action_digest(
            target_scope=target,
            mutation_class=mutation,
            bounded_scope=scope,
            consequence_class=consequence,
        )
        case = AuthorizationCase(
            case_id="AUTH-TEST-1",
            claimed_principal="Robert Leonard",
            target_scope=target,
            mutation_class=mutation,
            bounded_scope=scope,
            consequence_class=consequence,
            action_digest=digest,
            issued_at=now - timedelta(seconds=1),
            expires_at=now + timedelta(minutes=10),
            authorization_statement="Principal Robert Leonard authorizes AUTH-TEST-1",
            authentication_disposition="REGISTERED_PRINCIPAL_CLAIM_NOT_INDEPENDENTLY_AUTHENTICATED",
        )
        validate_authorization_case(
            case,
            principal=principal,
            expected_target_scope=target,
            expected_mutation_class=mutation,
            expected_bounded_scope=scope,
            expected_consequence_class=consequence,
            now=now,
        )
        consumed = consume_authorization_case(case, frozenset())
        with self.assertRaisesRegex(AuthorityAuthenticationError, "authorization_case_replay_denied"):
            validate_authorization_case(
                case,
                principal=principal,
                expected_target_scope=target,
                expected_mutation_class=mutation,
                expected_bounded_scope=scope,
                expected_consequence_class=consequence,
                now=now,
                consumed_case_ids=consumed,
            )

    def test_material_scope_change_requires_new_case(self):
        principal = resolve_registered_principal(self.root, claimed_name="Robert Leonard")
        now = datetime.now(timezone.utc)
        case = AuthorizationCase(
            case_id="AUTH-TEST-2",
            claimed_principal="Robert Leonard",
            target_scope="repo-a",
            mutation_class="REPOSITORY_OR_FILE_WRITE",
            bounded_scope="file-a only",
            consequence_class="STANDARD_MUTATION",
            action_digest=build_action_digest(
                target_scope="repo-a",
                mutation_class="REPOSITORY_OR_FILE_WRITE",
                bounded_scope="file-a only",
                consequence_class="STANDARD_MUTATION",
            ),
            issued_at=now - timedelta(seconds=1),
            expires_at=now + timedelta(minutes=10),
            authorization_statement="I authorize AUTH-TEST-2",
            authentication_disposition="REGISTERED_PRINCIPAL_CLAIM_NOT_INDEPENDENTLY_AUTHENTICATED",
        )
        with self.assertRaisesRegex(AuthorityAuthenticationError, "authorization_action_digest_mismatch"):
            validate_authorization_case(
                case,
                principal=principal,
                expected_target_scope="repo-a",
                expected_mutation_class="REPOSITORY_OR_FILE_WRITE",
                expected_bounded_scope="file-a and file-b",
                expected_consequence_class="STANDARD_MUTATION",
                now=now,
            )


if __name__ == "__main__":
    unittest.main()
