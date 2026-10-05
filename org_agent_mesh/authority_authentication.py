from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping, AbstractSet


class AuthorityAuthenticationError(ValueError):
    """Raised when identity assurance or an authorization case fails closed."""


@dataclass(frozen=True)
class Principal:
    principal_id: str
    name: str
    github_login: str


@dataclass(frozen=True)
class AuthorizationCase:
    case_id: str
    claimed_principal: str
    target_scope: str
    mutation_class: str
    bounded_scope: str
    consequence_class: str
    action_digest: str
    issued_at: datetime
    expires_at: datetime
    authorization_statement: str
    authentication_disposition: str


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise AuthorityAuthenticationError("timezone_required")
    return value.astimezone(timezone.utc)


def resolve_registered_principal(
    root_policy: Mapping[str, Any],
    *,
    claimed_name: str,
    claimed_github_login: str | None = None,
) -> Principal:
    if not isinstance(claimed_name, str) or not claimed_name.strip():
        raise AuthorityAuthenticationError("explicit_principal_claim_required")
    matches = []
    for item in root_policy.get("human_root_change_principals", []):
        if not isinstance(item, Mapping) or item.get("status", "ACTIVE") != "ACTIVE":
            continue
        if item.get("name") != claimed_name:
            continue
        if claimed_github_login is not None and item.get("github_login") != claimed_github_login:
            continue
        matches.append(item)
    if len(matches) != 1:
        raise AuthorityAuthenticationError("unknown_or_ambiguous_principal")
    item = matches[0]
    return Principal(
        principal_id=str(item.get("principal_id") or item["name"]),
        name=str(item["name"]),
        github_login=str(item["github_login"]),
    )


def build_action_digest(
    *,
    target_scope: str,
    mutation_class: str,
    bounded_scope: str,
    consequence_class: str,
) -> str:
    payload = {
        "bounded_scope": bounded_scope,
        "consequence_class": consequence_class,
        "mutation_class": mutation_class,
        "target_scope": target_scope,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_authentication_disposition(
    authentication_policy: Mapping[str, Any],
    root_policy: Mapping[str, Any],
    *,
    claimed_name: str,
    consequence_class: str,
    evidence_type: str | None = None,
    evidence_actor: str | None = None,
    evidence_payload: str | None = None,
    case_id: str | None = None,
    nonce: str | None = None,
    proof_created_by_agent: bool = False,
) -> tuple[Principal, str]:
    principal = resolve_registered_principal(root_policy, claimed_name=claimed_name)
    high = set(authentication_policy.get("high_consequence_classes", []))
    if consequence_class not in high:
        return principal, "REGISTERED_PRINCIPAL_CLAIM_NOT_INDEPENDENTLY_AUTHENTICATED"

    proof = authentication_policy.get("independent_external_proof", {})
    if evidence_type != proof.get("default_method"):
        raise AuthorityAuthenticationError("independent_principal_proof_required")
    if proof_created_by_agent:
        raise AuthorityAuthenticationError("agent_created_authentication_proof_denied")
    if evidence_actor != principal.github_login:
        raise AuthorityAuthenticationError("authentication_actor_mismatch")
    if not case_id or not nonce or not evidence_payload:
        raise AuthorityAuthenticationError("incomplete_authentication_challenge")
    if case_id not in evidence_payload or nonce not in evidence_payload:
        raise AuthorityAuthenticationError("authentication_challenge_mismatch")
    return principal, "INDEPENDENT_REGISTERED_PRINCIPAL_PROOF_VERIFIED"


def validate_authorization_case(
    case: AuthorizationCase,
    *,
    principal: Principal,
    expected_target_scope: str,
    expected_mutation_class: str,
    expected_bounded_scope: str,
    expected_consequence_class: str,
    now: datetime,
    consumed_case_ids: AbstractSet[str] = frozenset(),
) -> None:
    if case.case_id in consumed_case_ids:
        raise AuthorityAuthenticationError("authorization_case_replay_denied")
    if case.claimed_principal != principal.name:
        raise AuthorityAuthenticationError("authorization_principal_mismatch")
    if case.case_id not in case.authorization_statement:
        raise AuthorityAuthenticationError("authorization_statement_missing_case_id")
    if _utc(now) < _utc(case.issued_at):
        raise AuthorityAuthenticationError("authorization_case_not_yet_valid")
    if _utc(now) > _utc(case.expires_at):
        raise AuthorityAuthenticationError("authorization_case_expired")
    expected = build_action_digest(
        target_scope=expected_target_scope,
        mutation_class=expected_mutation_class,
        bounded_scope=expected_bounded_scope,
        consequence_class=expected_consequence_class,
    )
    if case.action_digest != expected:
        raise AuthorityAuthenticationError("authorization_action_digest_mismatch")
    if case.target_scope != expected_target_scope:
        raise AuthorityAuthenticationError("authorization_target_mismatch")
    if case.mutation_class != expected_mutation_class:
        raise AuthorityAuthenticationError("authorization_mutation_class_mismatch")
    if case.bounded_scope != expected_bounded_scope:
        raise AuthorityAuthenticationError("authorization_scope_mismatch")
    if case.consequence_class != expected_consequence_class:
        raise AuthorityAuthenticationError("authorization_consequence_mismatch")


def consume_authorization_case(case: AuthorizationCase, consumed_case_ids: AbstractSet[str]) -> frozenset[str]:
    if case.case_id in consumed_case_ids:
        raise AuthorityAuthenticationError("authorization_case_replay_denied")
    return frozenset(set(consumed_case_ids) | {case.case_id})
