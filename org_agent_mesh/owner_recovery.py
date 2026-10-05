from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


class OwnerRecoveryError(ValueError):
    pass


@dataclass(frozen=True)
class RecoveryFactorEvidence:
    factor_type: str
    evidence_id: str
    independence_domain: str
    verified: bool


@dataclass(frozen=True)
class OwnerRecoveryDecision:
    request_id: str
    owner_id: str
    target_scope: str
    factors: tuple[RecoveryFactorEvidence, ...]

    def validate(self, policy: Mapping[str, Any]) -> str:
        if not self.request_id or not self.owner_id or not self.target_scope:
            raise OwnerRecoveryError("RECOVERY_REQUEST_INCOMPLETE")
        verified = [item for item in self.factors if item.verified]
        minimum = int(policy.get("minimum_factor_quorum", 2))
        if len(verified) < minimum:
            raise OwnerRecoveryError("RECOVERY_FACTOR_QUORUM_NOT_MET")
        domains = {item.independence_domain for item in verified if item.independence_domain}
        if len(domains) < minimum:
            raise OwnerRecoveryError("RECOVERY_INDEPENDENCE_QUORUM_NOT_MET")
        strong = set(policy.get("strong_factors", []))
        if policy.get("strong_factor_required_when_available", True):
            if not any(item.factor_type in strong for item in verified):
                raise OwnerRecoveryError("STRONG_RECOVERY_FACTOR_REQUIRED")
        if not policy.get("same_device_dual_totp_counts_as_independent", False):
            totp_domains = [item.independence_domain for item in verified if item.factor_type == "AUTHENTICATOR_TOTP"]
            if len(totp_domains) >= 2 and len(set(totp_domains)) != len(totp_domains):
                raise OwnerRecoveryError("SAME_DEVICE_TOTP_NOT_INDEPENDENT")
        return str(policy.get("recovery_outcome", "ROTATE_CREDENTIAL_AND_RETURN_TO_NORMAL_AUTHORIZATION"))


def verified_factor_types(factors: Iterable[RecoveryFactorEvidence]) -> frozenset[str]:
    return frozenset(item.factor_type for item in factors if item.verified)
