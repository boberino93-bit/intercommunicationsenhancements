from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import unittest

from org_agent_mesh.owner_recovery import (
    OwnerRecoveryDecision,
    OwnerRecoveryError,
    RecoveryFactorEvidence,
    RecoveryReplayLedger,
)

ROOT = Path(__file__).resolve().parents[1]


class OwnerRecoveryLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads((ROOT / "governance" / "OWNER_CREDENTIAL_RECOVERY_POLICY.json").read_text())

    def make_factor(self, evidence_id, factor_type, domain, owner, request, now, **overrides):
        data = {
            "factor_type": factor_type,
            "evidence_id": evidence_id,
            "independence_domain": domain,
            "verified": True,
            "owner_id": owner,
            "request_id": request,
            "verifier_ref": f"verifier:{evidence_id}",
            "issued_at": now - timedelta(seconds=1),
            "expires_at": now + timedelta(minutes=5),
            "consumed": False,
            "metadata": {"result": "verified"},
        }
        data.update(overrides)
        return RecoveryFactorEvidence(**data)

    def make_decision(self, request="REC-1", owner="owner", now=None):
        now = now or datetime.now(timezone.utc)
        return OwnerRecoveryDecision(
            request_id=request,
            owner_id=owner,
            target_scope="global",
            factors=(
                self.make_factor("E1", "AUTHENTICATOR_TOTP", "device-a", owner, request, now),
                self.make_factor("E2", "REGISTERED_GITHUB_PROOF", "github", owner, request, now),
            ),
        ), now

    def test_two_fresh_independent_factors_allow_rotation_path(self):
        decision, now = self.make_decision()
        self.assertEqual(
            decision.validate(self.policy, now=now, ledger=RecoveryReplayLedger()),
            "ROTATE_CREDENTIAL_AND_RETURN_TO_NORMAL_AUTHORIZATION",
        )

    def test_single_factor_is_denied(self):
        decision, now = self.make_decision()
        one_factor = OwnerRecoveryDecision(
            request_id=decision.request_id,
            owner_id=decision.owner_id,
            target_scope=decision.target_scope,
            factors=(decision.factors[0],),
        )
        with self.assertRaisesRegex(OwnerRecoveryError, "RECOVERY_FACTOR_QUORUM_NOT_MET"):
            one_factor.validate(self.policy, now=now, ledger=RecoveryReplayLedger())

    def test_same_device_dual_totp_is_not_independent(self):
        decision, now = self.make_decision()
        second = self.make_factor("E2", "AUTHENTICATOR_TOTP", "device-a", "owner", "REC-1", now)
        same_device = OwnerRecoveryDecision(
            request_id=decision.request_id,
            owner_id=decision.owner_id,
            target_scope=decision.target_scope,
            factors=(decision.factors[0], second),
        )
        with self.assertRaises(OwnerRecoveryError):
            same_device.validate(self.policy, now=now, ledger=RecoveryReplayLedger())

    def test_expired_factor_is_denied(self):
        now = datetime.now(timezone.utc)
        decision, _ = self.make_decision(now=now)
        expired = self.make_factor(
            "E1",
            "AUTHENTICATOR_TOTP",
            "device-a",
            "owner",
            "REC-1",
            now,
            issued_at=now - timedelta(minutes=10),
            expires_at=now - timedelta(minutes=1),
        )
        decision = OwnerRecoveryDecision(
            request_id=decision.request_id,
            owner_id=decision.owner_id,
            target_scope=decision.target_scope,
            factors=(expired, decision.factors[1]),
        )
        with self.assertRaises(OwnerRecoveryError):
            decision.validate(self.policy, now=now, ledger=RecoveryReplayLedger())

    def test_wrong_request_binding_is_denied(self):
        decision, now = self.make_decision()
        wrong = self.make_factor("E1", "AUTHENTICATOR_TOTP", "device-a", "owner", "OTHER", now)
        decision = OwnerRecoveryDecision(
            request_id=decision.request_id,
            owner_id=decision.owner_id,
            target_scope=decision.target_scope,
            factors=(wrong, decision.factors[1]),
        )
        with self.assertRaises(OwnerRecoveryError):
            decision.validate(self.policy, now=now, ledger=RecoveryReplayLedger())

    def test_consumed_request_cannot_be_replayed(self):
        decision, now = self.make_decision()
        ledger = RecoveryReplayLedger().consume(decision)
        with self.assertRaisesRegex(OwnerRecoveryError, "RECOVERY_REQUEST_REPLAY_DENIED"):
            decision.validate(self.policy, now=now, ledger=ledger)

    def test_same_evidence_cannot_be_consumed_twice(self):
        decision, _ = self.make_decision()
        ledger = RecoveryReplayLedger().consume(decision)
        second, _ = self.make_decision(request="REC-2")
        reused = RecoveryFactorEvidence(
            factor_type=second.factors[0].factor_type,
            evidence_id=decision.factors[0].evidence_id,
            independence_domain=second.factors[0].independence_domain,
            verified=True,
            owner_id=second.owner_id,
            request_id=second.request_id,
            verifier_ref=second.factors[0].verifier_ref,
            issued_at=second.factors[0].issued_at,
            expires_at=second.factors[0].expires_at,
            metadata={"result": "verified"},
        )
        second = OwnerRecoveryDecision(
            request_id=second.request_id,
            owner_id=second.owner_id,
            target_scope=second.target_scope,
            factors=(reused, second.factors[1]),
        )
        with self.assertRaisesRegex(OwnerRecoveryError, "RECOVERY_EVIDENCE_REPLAY_DENIED"):
            ledger.consume(second)


if __name__ == "__main__":
    unittest.main()
