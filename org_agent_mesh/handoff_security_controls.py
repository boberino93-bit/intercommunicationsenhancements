from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from typing import Iterable
from urllib.parse import parse_qsl, urlparse


ROLES = {"PRIMARY", "MANAGER", "RESEARCH"}
SECRET_QUERY_KEYS = {
    "token",
    "security_token",
    "access_token",
    "auth",
    "authorization",
    "api_key",
    "apikey",
    "key",
    "secret",
    "password",
    "passwd",
    "credential",
}


class SecurityControlError(ValueError):
    pass


class LinkStatus(str, Enum):
    VERIFIED_DIRECT = "VERIFIED_DIRECT"
    VERIFIED_DOWNLOAD = "VERIFIED_DOWNLOAD"
    VERIFIED_NAVIGATION = "VERIFIED_NAVIGATION"
    UNVERIFIED_DIRECT = "UNVERIFIED_DIRECT"
    STALE = "STALE"
    INACCESSIBLE = "INACCESSIBLE"
    AMBIGUOUS = "AMBIGUOUS"
    BROKEN = "BROKEN"


class CompletionState(str, Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE_REMEDIATION_REQUIRED = "INCOMPLETE_REMEDIATION_REQUIRED"
    INCOMPLETE_BLOCKED = "INCOMPLETE_BLOCKED"


@dataclass(frozen=True)
class CompletionAssessment:
    objective_verified: bool
    known_avoidable_residue: tuple[str, ...] = ()
    remediation_authorized_and_possible: bool = True

    def state(self) -> CompletionState:
        if not self.objective_verified:
            return CompletionState.INCOMPLETE_REMEDIATION_REQUIRED
        if not self.known_avoidable_residue:
            return CompletionState.COMPLETE
        if self.remediation_authorized_and_possible:
            return CompletionState.INCOMPLETE_REMEDIATION_REQUIRED
        return CompletionState.INCOMPLETE_BLOCKED

    def require_complete(self) -> None:
        state = self.state()
        if state is not CompletionState.COMPLETE:
            residue = ",".join(self.known_avoidable_residue) or "OBJECTIVE_NOT_VERIFIED"
            raise SecurityControlError(f"COMPLETION_INTEGRITY_BLOCKED:{state.value}:{residue}")


@dataclass(frozen=True)
class HandoffEnvelope:
    handoff_id: str
    project_id: str
    source_agent_id: str
    source_agent_role: str
    target_agent_id: str
    target_agent_role: str
    canonical_project_revision: str
    authority_conveyed: bool = False

    def validate(self, *, expected_project_id: str) -> None:
        if self.project_id != expected_project_id:
            raise SecurityControlError("PROJECT_MISMATCH")
        if self.source_agent_role.upper() not in ROLES:
            raise SecurityControlError("SOURCE_ROLE_INVALID")
        if self.target_agent_role.upper() not in ROLES:
            raise SecurityControlError("TARGET_ROLE_INVALID")
        if self.authority_conveyed is not False:
            raise SecurityControlError("HANDOFF_MAY_NOT_CONVEY_EXECUTION_AUTHORITY")
        if not self.handoff_id or not self.canonical_project_revision:
            raise SecurityControlError("HANDOFF_ID_OR_REVISION_MISSING")


@dataclass(frozen=True)
class BreakGlassTokenBinding:
    token_id: str
    token_digest: str
    principal_id: str
    project_id: str
    target_scope: str
    action_digest: str
    consequence_class: str
    issued_at_utc: str
    expires_at_utc: str
    consumed: bool = False

    @staticmethod
    def digest_token(raw_token: str) -> str:
        if not raw_token:
            raise SecurityControlError("BREAK_GLASS_TOKEN_MISSING")
        return "sha256:" + sha256(raw_token.encode("utf-8")).hexdigest()

    def validate(
        self,
        *,
        raw_token: str,
        now: datetime,
        principal_id: str,
        project_id: str,
        target_scope: str,
        action_digest: str,
        consequence_class: str,
        normal_security_controls_ok: bool,
    ) -> None:
        if not normal_security_controls_ok:
            raise SecurityControlError("NORMAL_SECURITY_CONTROLS_NOT_SATISFIED")
        if self.consumed:
            raise SecurityControlError("BREAK_GLASS_TOKEN_REPLAY")
        if not self.token_id:
            raise SecurityControlError("BREAK_GLASS_TOKEN_ID_MISSING")
        if self.digest_token(raw_token) != self.token_digest:
            raise SecurityControlError("BREAK_GLASS_TOKEN_INVALID")
        checks = {
            "PRINCIPAL_MISMATCH": self.principal_id == principal_id,
            "PROJECT_MISMATCH": self.project_id == project_id,
            "TARGET_SCOPE_MISMATCH": self.target_scope == target_scope,
            "ACTION_DIGEST_MISMATCH": self.action_digest == action_digest,
            "CONSEQUENCE_CLASS_MISMATCH": self.consequence_class == consequence_class,
        }
        for reason, ok in checks.items():
            if not ok:
                raise SecurityControlError(reason)
        current = _ensure_aware(now)
        issued = _parse_iso(self.issued_at_utc)
        expires = _parse_iso(self.expires_at_utc)
        if current < issued:
            raise SecurityControlError("BREAK_GLASS_TOKEN_NOT_YET_VALID")
        if current >= expires:
            raise SecurityControlError("BREAK_GLASS_TOKEN_EXPIRED")


@dataclass(frozen=True)
class ActionableLink:
    url: str
    status: LinkStatus
    target_id: str
    project_id: str
    verified_at_utc: str | None = None

    def validate_for_presentation(self) -> None:
        parsed = urlparse(self.url)
        if parsed.scheme not in {"https", "http"} or not parsed.netloc:
            raise SecurityControlError("LINK_MALFORMED")
        for key, _value in parse_qsl(parsed.query, keep_blank_values=True):
            if key.lower() in SECRET_QUERY_KEYS:
                raise SecurityControlError("SECRET_MATERIAL_IN_URL")
        fragment_keys = {k.lower() for k, _ in parse_qsl(parsed.fragment, keep_blank_values=True)}
        if fragment_keys & SECRET_QUERY_KEYS:
            raise SecurityControlError("SECRET_MATERIAL_IN_URL")
        if self.status in {LinkStatus.VERIFIED_DIRECT, LinkStatus.VERIFIED_DOWNLOAD}:
            if not self.verified_at_utc:
                raise SecurityControlError("VERIFIED_LINK_REQUIRES_VERIFICATION_TIMESTAMP")
            _parse_iso(self.verified_at_utc)
        if not self.target_id or not self.project_id:
            raise SecurityControlError("LINK_TARGET_BINDING_MISSING")


def require_all_controls(required: Iterable[str], satisfied: Iterable[str]) -> None:
    missing = sorted(set(required) - set(satisfied))
    if missing:
        raise SecurityControlError("MISSING_REQUIRED_CONTROLS:" + ",".join(missing))


def _parse_iso(value: str) -> datetime:
    if not value:
        raise SecurityControlError("TIMESTAMP_MISSING")
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise SecurityControlError("TIMESTAMP_INVALID") from exc
    return _ensure_aware(parsed)


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise SecurityControlError("TIMESTAMP_MUST_BE_TIMEZONE_AWARE")
    return value.astimezone(timezone.utc)
