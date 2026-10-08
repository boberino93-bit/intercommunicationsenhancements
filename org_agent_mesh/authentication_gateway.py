from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import secrets
from typing import Callable, Iterable, Protocol

from .totp_verifier import match_totp_counter


HIGH_CONSEQUENCE_CLASSES = frozenset({
    "ROOT_AUTHORITY_CHANGE",
    "UNIVERSAL_GOVERNANCE_CHANGE",
    "PRODUCTION_PROMOTION_OR_DEPLOYMENT",
    "SECURITY_OR_CREDENTIAL_BOUNDARY_CHANGE",
    "FINANCIAL_EFFECT",
    "DESTRUCTIVE_OR_IRREVERSIBLE_OPERATION",
    "SCHEDULE_ENABLE_OR_REENABLE",
    "CROSS_PROJECT_MUTATION",
})

GITHUB_PROOF_DISPOSITION = "INDEPENDENT_REGISTERED_PRINCIPAL_PROOF_VERIFIED"


class AuthenticationError(ValueError):
    """Fail-closed authentication-factor error."""


class ReplayStore(Protocol):
    def consume(self, key: str, *, expires_at: datetime) -> None: ...


class SmsTransport(Protocol):
    def send(self, destination_ref: str, message: str, *, idempotency_key: str) -> str | None: ...


class InMemoryReplayStore:
    """Test/dev replay store. Production must use a process-independent durable store."""

    def __init__(self) -> None:
        self._keys: dict[str, datetime] = {}

    def consume(self, key: str, *, expires_at: datetime) -> None:
        # Deliberately do not prune against wall-clock time here. The caller may be
        # validating a deterministic event time, and wall-clock pruning can reopen a
        # replay window. Production backends may garbage-collect expired rows, but
        # uniqueness of an already-consumed evidence key must remain authoritative.
        if key in self._keys:
            raise AuthenticationError("authentication_evidence_replay_denied")
        self._keys[key] = _utc(expires_at)


@dataclass(frozen=True)
class AuthChallenge:
    challenge_id: str
    case_id: str
    principal_id: str
    action_digest: str
    consequence_class: str
    issued_at: datetime
    expires_at: datetime
    nonce: str


@dataclass(frozen=True)
class FactorAttestation:
    challenge_id: str
    case_id: str
    principal_id: str
    action_digest: str
    method: str
    assurance: str
    verified_at: datetime
    expires_at: datetime
    verifier_id: str
    evidence_digest: str
    signature: str


@dataclass(frozen=True)
class MicrosoftIdentityResult:
    """Normalized output of a real Entra/OIDC verifier.

    The adapter that creates this object must perform cryptographic JWT/OIDC
    validation before setting ``token_validated`` true.
    """

    principal_id: str
    tenant_id: str
    token_id: str
    challenge_nonce: str
    authenticated_at: datetime
    authentication_context_id: str
    authenticator_satisfied: bool
    token_validated: bool
    phishing_resistant: bool = False


@dataclass
class _SmsRecord:
    digest: str
    destination_digest: str
    attempts: int
    expires_at: datetime
    consumed: bool = False


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise AuthenticationError("timezone_required")
    return value.astimezone(timezone.utc)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_challenge(
    *,
    case_id: str,
    principal_id: str,
    action_digest: str,
    consequence_class: str,
    now: datetime | None = None,
    ttl_seconds: int = 300,
) -> AuthChallenge:
    now = _utc(now or utcnow())
    if not all(isinstance(v, str) and v.strip() for v in (case_id, principal_id, action_digest, consequence_class)):
        raise AuthenticationError("invalid_challenge_binding")
    if not (30 <= ttl_seconds <= 900):
        raise AuthenticationError("invalid_challenge_ttl")
    return AuthChallenge(
        challenge_id="AUTHN-" + secrets.token_hex(12).upper(),
        case_id=case_id,
        principal_id=principal_id,
        action_digest=action_digest,
        consequence_class=consequence_class,
        issued_at=now,
        expires_at=now + timedelta(seconds=ttl_seconds),
        nonce=secrets.token_urlsafe(32),
    )


def _assert_live(challenge: AuthChallenge, now: datetime) -> None:
    now = _utc(now)
    if now < _utc(challenge.issued_at):
        raise AuthenticationError("challenge_not_yet_valid")
    if now > _utc(challenge.expires_at):
        raise AuthenticationError("challenge_expired")


def _attestation_payload(attestation: FactorAttestation) -> dict[str, str]:
    return {
        "challenge_id": attestation.challenge_id,
        "case_id": attestation.case_id,
        "principal_id": attestation.principal_id,
        "action_digest": attestation.action_digest,
        "method": attestation.method,
        "assurance": attestation.assurance,
        "verified_at": _utc(attestation.verified_at).isoformat(),
        "expires_at": _utc(attestation.expires_at).isoformat(),
        "verifier_id": attestation.verifier_id,
        "evidence_digest": attestation.evidence_digest,
    }


def _sign_payload(payload: dict[str, str], attestation_key: bytes) -> str:
    if len(attestation_key) < 32:
        raise AuthenticationError("attestation_key_too_short")
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hmac.new(attestation_key, encoded, hashlib.sha256).hexdigest()


def _make_attestation(
    *,
    challenge: AuthChallenge,
    method: str,
    assurance: str,
    verifier_id: str,
    evidence_digest: str,
    now: datetime,
    attestation_key: bytes,
    ttl_seconds: int = 180,
) -> FactorAttestation:
    now = _utc(now)
    expires_at = min(_utc(challenge.expires_at), now + timedelta(seconds=ttl_seconds))
    unsigned = FactorAttestation(
        challenge_id=challenge.challenge_id,
        case_id=challenge.case_id,
        principal_id=challenge.principal_id,
        action_digest=challenge.action_digest,
        method=method,
        assurance=assurance,
        verified_at=now,
        expires_at=expires_at,
        verifier_id=verifier_id,
        evidence_digest=evidence_digest,
        signature="",
    )
    return replace(unsigned, signature=_sign_payload(_attestation_payload(unsigned), attestation_key))


def validate_attestation(
    attestation: FactorAttestation,
    *,
    challenge: AuthChallenge,
    attestation_key: bytes,
    now: datetime,
) -> None:
    now = _utc(now)
    expected_binding = (
        challenge.challenge_id,
        challenge.case_id,
        challenge.principal_id,
        challenge.action_digest,
    )
    actual_binding = (
        attestation.challenge_id,
        attestation.case_id,
        attestation.principal_id,
        attestation.action_digest,
    )
    if actual_binding != expected_binding:
        raise AuthenticationError("factor_binding_mismatch")
    if now > _utc(attestation.expires_at):
        raise AuthenticationError("factor_attestation_expired")
    expected = _sign_payload(_attestation_payload(attestation), attestation_key)
    if not hmac.compare_digest(expected, attestation.signature):
        raise AuthenticationError("factor_attestation_signature_invalid")


class TotpFactor:
    verifier_id = "BOOTSTRAP_TOTP_RFC6238_V2"

    def __init__(
        self,
        secret_resolver: Callable[[str], str],
        replay_store: ReplayStore,
        attestation_key: bytes,
    ) -> None:
        self.secret_resolver = secret_resolver
        self.replay_store = replay_store
        self.attestation_key = attestation_key

    def verify(self, challenge: AuthChallenge, code: str, *, now: datetime | None = None) -> FactorAttestation:
        now = _utc(now or utcnow())
        _assert_live(challenge, now)
        secret = self.secret_resolver(challenge.principal_id)
        if not isinstance(secret, str) or not secret:
            raise AuthenticationError("totp_secret_unavailable")
        counter = match_totp_counter(secret, code, unix_time=int(now.timestamp()), step_seconds=30, digits=6, window=1)
        if counter is None:
            raise AuthenticationError("invalid_totp")
        replay_key = f"totp:{challenge.principal_id}:{counter}"
        self.replay_store.consume(replay_key, expires_at=now + timedelta(seconds=90))
        evidence_digest = hashlib.sha256(replay_key.encode("utf-8")).hexdigest()
        return _make_attestation(
            challenge=challenge,
            method="TOTP_RFC6238",
            assurance="POSSESSION_OTP",
            verifier_id=self.verifier_id,
            evidence_digest=evidence_digest,
            now=now,
            attestation_key=self.attestation_key,
        )


class MicrosoftAuthenticatorFactor:
    verifier_id = "MICROSOFT_ENTRA_AUTHENTICATOR_V2"

    def __init__(
        self,
        *,
        allowed_tenant_ids: Iterable[str],
        required_authentication_context_id: str,
        replay_store: ReplayStore,
        attestation_key: bytes,
        max_auth_age_seconds: int = 300,
    ) -> None:
        self.allowed_tenant_ids = frozenset(str(v) for v in allowed_tenant_ids)
        self.required_authentication_context_id = str(required_authentication_context_id)
        self.replay_store = replay_store
        self.attestation_key = attestation_key
        self.max_auth_age_seconds = max_auth_age_seconds
        if not self.allowed_tenant_ids or not self.required_authentication_context_id:
            raise AuthenticationError("microsoft_runtime_configuration_missing")

    def verify(
        self,
        challenge: AuthChallenge,
        result: MicrosoftIdentityResult,
        *,
        now: datetime | None = None,
    ) -> FactorAttestation:
        now = _utc(now or utcnow())
        _assert_live(challenge, now)
        if not result.token_validated:
            raise AuthenticationError("microsoft_oidc_token_not_validated")
        if result.tenant_id not in self.allowed_tenant_ids:
            raise AuthenticationError("microsoft_tenant_mismatch")
        if result.principal_id != challenge.principal_id:
            raise AuthenticationError("microsoft_principal_mismatch")
        if not hmac.compare_digest(result.challenge_nonce, challenge.nonce):
            raise AuthenticationError("microsoft_nonce_mismatch")
        if result.authentication_context_id != self.required_authentication_context_id:
            raise AuthenticationError("microsoft_authentication_context_mismatch")
        if not result.authenticator_satisfied:
            raise AuthenticationError("microsoft_authenticator_not_satisfied")
        authenticated_at = _utc(result.authenticated_at)
        if authenticated_at < _utc(challenge.issued_at) - timedelta(seconds=30):
            raise AuthenticationError("microsoft_authentication_predates_challenge")
        if authenticated_at > now + timedelta(seconds=30):
            raise AuthenticationError("microsoft_authentication_from_future")
        if now - authenticated_at > timedelta(seconds=self.max_auth_age_seconds):
            raise AuthenticationError("microsoft_authentication_stale")
        self.replay_store.consume(
            f"entra:{result.tenant_id}:{result.token_id}",
            expires_at=min(challenge.expires_at, now + timedelta(minutes=10)),
        )
        evidence_digest = hashlib.sha256(
            f"entra:{result.tenant_id}:{result.token_id}".encode("utf-8")
        ).hexdigest()
        return _make_attestation(
            challenge=challenge,
            method="MICROSOFT_ENTRA_AUTHENTICATOR",
            assurance="PHISHING_RESISTANT" if result.phishing_resistant else "STRONG_OUT_OF_BAND",
            verifier_id=self.verifier_id,
            evidence_digest=evidence_digest,
            now=now,
            attestation_key=self.attestation_key,
        )


class SmsFallbackFactor:
    verifier_id = "SMS_RESTRICTED_FALLBACK_V2"

    def __init__(
        self,
        *,
        transport: SmsTransport,
        pepper: bytes,
        attestation_key: bytes,
        max_attempts: int = 3,
        ttl_seconds: int = 300,
    ) -> None:
        if len(pepper) < 32:
            raise AuthenticationError("sms_pepper_too_short")
        if not (1 <= max_attempts <= 5):
            raise AuthenticationError("unsafe_sms_attempt_limit")
        if not (30 <= ttl_seconds <= 300):
            raise AuthenticationError("unsafe_sms_ttl")
        self.transport = transport
        self.pepper = pepper
        self.attestation_key = attestation_key
        self.max_attempts = max_attempts
        self.ttl_seconds = ttl_seconds
        self._records: dict[str, _SmsRecord] = {}

    def _digest(self, challenge_id: str, code: str) -> str:
        return hmac.new(self.pepper, f"{challenge_id}:{code}".encode("utf-8"), hashlib.sha256).hexdigest()

    def issue(self, challenge: AuthChallenge, destination_ref: str, *, now: datetime | None = None) -> None:
        now = _utc(now or utcnow())
        _assert_live(challenge, now)
        if not destination_ref.startswith(("vault://", "secret://", "principal://")):
            raise AuthenticationError("sms_destination_must_be_protected_reference")
        code = f"{secrets.randbelow(100_000_000):08d}"
        expires_at = min(challenge.expires_at, now + timedelta(seconds=self.ttl_seconds))
        self._records[challenge.challenge_id] = _SmsRecord(
            digest=self._digest(challenge.challenge_id, code),
            destination_digest=hashlib.sha256(destination_ref.encode("utf-8")).hexdigest(),
            attempts=0,
            expires_at=expires_at,
        )
        self.transport.send(
            destination_ref,
            f"Authentication code: {code}. Expires in 5 minutes.",
            idempotency_key=challenge.challenge_id,
        )

    def verify(self, challenge: AuthChallenge, code: str, *, now: datetime | None = None) -> FactorAttestation:
        now = _utc(now or utcnow())
        _assert_live(challenge, now)
        rec = self._records.get(challenge.challenge_id)
        if rec is None:
            raise AuthenticationError("sms_challenge_not_issued")
        if rec.consumed:
            raise AuthenticationError("sms_replay_denied")
        if now > _utc(rec.expires_at):
            raise AuthenticationError("sms_code_expired")
        if rec.attempts >= self.max_attempts:
            raise AuthenticationError("sms_attempt_limit_exceeded")
        if not isinstance(code, str) or not code.isdigit() or len(code) != 8:
            rec.attempts += 1
            raise AuthenticationError("invalid_sms_code")
        if not hmac.compare_digest(rec.digest, self._digest(challenge.challenge_id, code)):
            rec.attempts += 1
            raise AuthenticationError("invalid_sms_code")
        rec.consumed = True
        evidence_digest = hashlib.sha256(
            f"sms:{challenge.challenge_id}:{rec.destination_digest}".encode("utf-8")
        ).hexdigest()
        return _make_attestation(
            challenge=challenge,
            method="SMS_OTP",
            assurance="RESTRICTED_FALLBACK",
            verifier_id=self.verifier_id,
            evidence_digest=evidence_digest,
            now=now,
            attestation_key=self.attestation_key,
        )


def authorize_factor_set(
    *,
    challenge: AuthChallenge,
    attestations: Iterable[FactorAttestation],
    attestation_key: bytes,
    now: datetime,
    independent_proof_disposition: str | None = None,
) -> str:
    """Evaluate factor evidence before mutation authorization is considered.

    This function never grants mutation authority. It only returns an authentication
    disposition that the separate authorization layer may consume.
    """
    now = _utc(now)
    _assert_live(challenge, now)
    methods: set[str] = set()
    for attestation in attestations:
        validate_attestation(attestation, challenge=challenge, attestation_key=attestation_key, now=now)
        methods.add(attestation.method)

    if "TOTP_RFC6238" not in methods:
        raise AuthenticationError("mandatory_totp_required")

    if challenge.consequence_class in HIGH_CONSEQUENCE_CLASSES:
        has_microsoft = "MICROSOFT_ENTRA_AUTHENTICATOR" in methods
        has_github = independent_proof_disposition == GITHUB_PROOF_DISPOSITION
        if not (has_microsoft or has_github):
            raise AuthenticationError("strong_independent_step_up_required")
        return "TOTP_PLUS_STRONG_INDEPENDENT_PROOF_VERIFIED"

    return "TOTP_VERIFIED"
