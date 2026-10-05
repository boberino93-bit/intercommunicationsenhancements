import json
from pathlib import Path
import unittest

from org_agent_mesh.owner_recovery import OwnerRecoveryDecision, OwnerRecoveryError, RecoveryFactorEvidence
from org_agent_mesh.totp_verifier import verify_totp

ROOT = Path(__file__).resolve().parents[1]


class OwnerRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads((ROOT / "governance" / "OWNER_CREDENTIAL_RECOVERY_POLICY.json").read_text())

    def test_two_independent_factors_allow_rotation_path(self):
        decision = OwnerRecoveryDecision(
            request_id="REC-1",
            owner_id="owner",
            target_scope="global",
            factors=(
                RecoveryFactorEvidence("AUTHENTICATOR_TOTP", "E1", "phone-a", True),
                RecoveryFactorEvidence("REGISTERED_GITHUB_PROOF", "E2", "github", True),
            ),
        )
        self.assertEqual(decision.validate(self.policy), "ROTATE_CREDENTIAL_AND_RETURN_TO_NORMAL_AUTHORIZATION")

    def test_single_factor_denied(self):
        decision = OwnerRecoveryDecision(
            request_id="REC-2",
            owner_id="owner",
            target_scope="global",
            factors=(RecoveryFactorEvidence("AUTHENTICATOR_TOTP", "E1", "phone-a", True),),
        )
        with self.assertRaisesRegex(OwnerRecoveryError, "QUORUM_NOT_MET"):
            decision.validate(self.policy)

    def test_same_device_two_totp_not_independent(self):
        decision = OwnerRecoveryDecision(
            request_id="REC-3",
            owner_id="owner",
            target_scope="global",
            factors=(
                RecoveryFactorEvidence("AUTHENTICATOR_TOTP", "E1", "phone-a", True),
                RecoveryFactorEvidence("AUTHENTICATOR_TOTP", "E2", "phone-a", True),
            ),
        )
        with self.assertRaises(OwnerRecoveryError):
            decision.validate(self.policy)

    def test_totp_rfc_vector(self):
        secret = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        self.assertTrue(verify_totp(secret, "287082", unix_time=59, digits=6, window=0))
        self.assertFalse(verify_totp(secret, "000000", unix_time=59, digits=6, window=0))


if __name__ == "__main__":
    unittest.main()
