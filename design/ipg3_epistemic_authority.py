"""Design-only epistemic authority gate for IPG3.

This module makes one invariant executable:

    Generative output is evidence/proposal, never mutation authority.

It does not mutate the active runtime. It issues and consumes design-only promotion
grants that are bound to one project, operation, resource, payload digest, state
version, issuer execution instance, decision, evidence set, and expiry.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from threading import RLock
import json
import uuid


class EpistemicGateError(RuntimeError):
    pass


TRUST_CLASSES = {
    "AUTHORITATIVE_CONFIG",
    "VERIFIED_FACT",
    "EXECUTION_EVIDENCE",
    "DERIVED_KNOWLEDGE",
    "AGENT_REFLECTION",
    "EXTERNAL_UNTRUSTED",
    "QUARANTINED",
}

_ALLOWED_PROMOTIONS = {
    "AUTHORITATIVE_CONFIG": set(),
    "VERIFIED_FACT": {"AUTHORITATIVE_CONFIG"},
    "EXECUTION_EVIDENCE": {"VERIFIED_FACT", "AUTHORITATIVE_CONFIG"},
    "DERIVED_KNOWLEDGE": {"VERIFIED_FACT"},
    "AGENT_REFLECTION": {"DERIVED_KNOWLEDGE"},
    "EXTERNAL_UNTRUSTED": {"DERIVED_KNOWLEDGE", "VERIFIED_FACT"},
    "QUARANTINED": set(),
}

LOW_TRUST_CLASSES = {"AGENT_REFLECTION", "DERIVED_KNOWLEDGE", "EXTERNAL_UNTRUSTED"}
AUTHORITY_CAPABILITIES = {"WRITE_ACCEPTED_STATE", "APPROVE_CHANGE"}


def _parse_utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception as exc:
        raise EpistemicGateError("invalid timestamp") from exc
    if parsed.tzinfo is None:
        raise EpistemicGateError("timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _canonical_sha256(value) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_sha256(value: str, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise EpistemicGateError(f"{field} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise EpistemicGateError(f"{field} must be a SHA-256 hex digest") from exc
    return value.lower()


@dataclass(frozen=True)
class EvidenceRef:
    evidence_id: str
    source_type: str
    source_id: str
    source_revision: str | None
    content_sha256: str
    observed_at_utc: str

    def __post_init__(self):
        if not self.evidence_id or not self.source_type or not self.source_id:
            raise EpistemicGateError("evidence identity and source are required")
        _require_sha256(self.content_sha256, "content_sha256")
        _parse_utc(self.observed_at_utc)

    @property
    def independence_key(self) -> str:
        """Agents rereading the same source lineage do not create independent evidence."""
        return "|".join(
            (
                self.source_type,
                self.source_id,
                self.source_revision or "",
                self.content_sha256.lower(),
            )
        )


@dataclass(frozen=True)
class AuthorityContext:
    project_id: str
    issuer_agent_id: str
    issuer_agent_instance_id: str
    issuer_role: str
    capabilities: tuple[str, ...]
    operation: str
    target_resource_id: str
    expected_version: int
    payload_sha256: str
    issued_at_utc: str
    expires_at_utc: str

    def __post_init__(self):
        if not all(
            (
                self.project_id,
                self.issuer_agent_id,
                self.issuer_agent_instance_id,
                self.issuer_role,
                self.operation,
                self.target_resource_id,
            )
        ):
            raise EpistemicGateError("authority context contains an empty identity/binding field")
        if self.expected_version < 0:
            raise EpistemicGateError("expected_version must be >= 0")
        _require_sha256(self.payload_sha256, "payload_sha256")
        issued = _parse_utc(self.issued_at_utc)
        expires = _parse_utc(self.expires_at_utc)
        if expires <= issued:
            raise EpistemicGateError("grant expiry must follow issue time")


@dataclass(frozen=True)
class PromotionGrant:
    grant_id: str
    project_id: str
    record_id: str
    source_class: str
    target_class: str
    decision_id: str
    operation: str
    target_resource_id: str
    expected_version: int
    payload_sha256: str
    issuer_agent_id: str
    issuer_agent_instance_id: str
    validator_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    evidence_independence_keys: tuple[str, ...]
    issued_at_utc: str
    expires_at_utc: str
    max_uses: int = 1

    @property
    def binding_sha256(self) -> str:
        return _canonical_sha256(
            {
                "project_id": self.project_id,
                "record_id": self.record_id,
                "source_class": self.source_class,
                "target_class": self.target_class,
                "decision_id": self.decision_id,
                "operation": self.operation,
                "target_resource_id": self.target_resource_id,
                "expected_version": self.expected_version,
                "payload_sha256": self.payload_sha256,
                "issuer_agent_id": self.issuer_agent_id,
                "issuer_agent_instance_id": self.issuer_agent_instance_id,
                "validator_ids": self.validator_ids,
                "evidence_ids": self.evidence_ids,
                "evidence_independence_keys": self.evidence_independence_keys,
                "issued_at_utc": self.issued_at_utc,
                "expires_at_utc": self.expires_at_utc,
                "max_uses": self.max_uses,
            }
        )


def required_independent_evidence(source_class: str, target_class: str) -> int:
    if target_class == "AUTHORITATIVE_CONFIG":
        return 2
    if target_class == "VERIFIED_FACT" and source_class in LOW_TRUST_CLASSES:
        return 2
    return 1


def issue_promotion_grant(
    record: dict,
    *,
    target_class: str,
    decision_id: str,
    validator_ids: list[str] | tuple[str, ...],
    evidence: list[EvidenceRef] | tuple[EvidenceRef, ...],
    authority: AuthorityContext,
    now: datetime | None = None,
) -> PromotionGrant:
    """Validate epistemic promotion and mint a narrowly-bound design-only grant."""

    if record.get("schema") != "org-agent-mesh/trust-provenance-record/v1-draft":
        raise EpistemicGateError("wrong trust/provenance schema")

    record_id = record.get("record_id")
    project_id = record.get("project_id")
    source_class = record.get("trust_class")
    validation_state = record.get("validation_state")

    if not record_id or not project_id or source_class not in TRUST_CLASSES:
        raise EpistemicGateError("invalid trust/provenance record identity or class")
    if project_id != authority.project_id:
        raise EpistemicGateError("authority project does not match knowledge record project")
    if validation_state in {"REJECTED", "REVOKED"}:
        raise EpistemicGateError("rejected or revoked knowledge cannot be promoted")
    if target_class not in TRUST_CLASSES:
        raise EpistemicGateError("unknown target trust class")
    if target_class == source_class:
        raise EpistemicGateError("promotion grant is unnecessary for an unchanged trust class")
    if target_class not in _ALLOWED_PROMOTIONS[source_class]:
        raise EpistemicGateError(f"trust promotion not allowed: {source_class} -> {target_class}")

    if source_class in LOW_TRUST_CLASSES and target_class == "AUTHORITATIVE_CONFIG":
        raise EpistemicGateError("low-trust generative/derived content cannot become authoritative config directly")

    validators = tuple(sorted({item for item in validator_ids if item}))
    if not validators:
        raise EpistemicGateError("promotion requires an attributable validator")

    evidence = tuple(evidence)
    if not evidence:
        raise EpistemicGateError("promotion requires evidence")
    independence_keys = tuple(sorted({item.independence_key for item in evidence}))
    required = required_independent_evidence(source_class, target_class)
    if len(independence_keys) < required:
        raise EpistemicGateError(
            f"promotion requires {required} independent evidence lineages; found {len(independence_keys)}"
        )

    if target_class == "AUTHORITATIVE_CONFIG":
        if authority.issuer_role != "PRIMARY":
            raise EpistemicGateError("authoritative configuration promotion requires PRIMARY issuer role")
        missing = AUTHORITY_CAPABILITIES - set(authority.capabilities)
        if missing:
            raise EpistemicGateError(
                f"authoritative configuration promotion missing capabilities: {sorted(missing)}"
            )

    if not decision_id:
        raise EpistemicGateError("promotion requires a durable decision_id")

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise EpistemicGateError("now must be timezone-aware")
    current = current.astimezone(timezone.utc)
    if _parse_utc(authority.expires_at_utc) <= current:
        raise EpistemicGateError("authority context is expired")
    if _parse_utc(authority.issued_at_utc) > current:
        raise EpistemicGateError("authority context was issued in the future")

    return PromotionGrant(
        grant_id=f"epg-{uuid.uuid4().hex}",
        project_id=project_id,
        record_id=record_id,
        source_class=source_class,
        target_class=target_class,
        decision_id=decision_id,
        operation=authority.operation,
        target_resource_id=authority.target_resource_id,
        expected_version=authority.expected_version,
        payload_sha256=authority.payload_sha256.lower(),
        issuer_agent_id=authority.issuer_agent_id,
        issuer_agent_instance_id=authority.issuer_agent_instance_id,
        validator_ids=validators,
        evidence_ids=tuple(sorted({item.evidence_id for item in evidence})),
        evidence_independence_keys=independence_keys,
        issued_at_utc=authority.issued_at_utc,
        expires_at_utc=authority.expires_at_utc,
    )


class EpistemicGrantLedger:
    """Atomic one-shot consumption reference ledger.

    This is intentionally separate from mutation execution. A consumer must still
    satisfy the normal local session/capability/project/lifecycle checks.
    """

    def __init__(self):
        self._uses: dict[str, int] = {}
        self._bindings: dict[str, str] = {}
        self._lock = RLock()

    def register(self, grant: PromotionGrant) -> str:
        with self._lock:
            existing = self._bindings.get(grant.grant_id)
            if existing is not None and existing != grant.binding_sha256:
                raise EpistemicGateError("grant id collision with different binding")
            self._bindings.setdefault(grant.grant_id, grant.binding_sha256)
            self._uses.setdefault(grant.grant_id, 0)
            return grant.grant_id

    def consume(
        self,
        grant: PromotionGrant,
        *,
        project_id: str,
        operation: str,
        target_resource_id: str,
        expected_version: int,
        payload_sha256: str,
        issuer_agent_instance_id: str,
        now: datetime | None = None,
    ) -> bool:
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            raise EpistemicGateError("now must be timezone-aware")
        if _parse_utc(grant.expires_at_utc) <= current.astimezone(timezone.utc):
            raise EpistemicGateError("promotion grant is expired")

        supplied_digest = _require_sha256(payload_sha256, "payload_sha256")
        expected = (
            grant.project_id,
            grant.operation,
            grant.target_resource_id,
            grant.expected_version,
            grant.payload_sha256,
            grant.issuer_agent_instance_id,
        )
        supplied = (
            project_id,
            operation,
            target_resource_id,
            expected_version,
            supplied_digest,
            issuer_agent_instance_id,
        )
        if supplied != expected:
            raise EpistemicGateError("promotion grant binding mismatch")

        with self._lock:
            binding = self._bindings.get(grant.grant_id)
            if binding is None:
                self.register(grant)
                binding = self._bindings[grant.grant_id]
            if binding != grant.binding_sha256:
                raise EpistemicGateError("promotion grant binding changed after registration")
            used = self._uses[grant.grant_id]
            if used >= grant.max_uses:
                raise EpistemicGateError("promotion grant already consumed")
            self._uses[grant.grant_id] = used + 1
            return True
