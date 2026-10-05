from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json


PROVENANCE_WEIGHTS = {
    "OBSERVED": 1.0,
    "RETRIEVED": 0.95,
    "REPORTED_BY_AGENT": 0.65,
    "INFERRED": 0.6,
    "EXPECTED": 0.4,
    "UNVERIFIED": 0.2,
}

LEVELS = {"UNSCOPED_CHAT", "PROJECT_CHAT", "GLOBAL_PRIMARY"}

PROTECTED_CLASSES = {
    "AUTHENTICATION",
    "AUTHORIZATION",
    "SECRETS",
    "PRIVILEGE_ROLE_CONTROLS",
    "RECOVERY",
    "ROOT_GOVERNANCE",
    "DESTRUCTIVE",
    "CROSS_PROJECT_SOURCE_WRITE",
    "SCHEDULE_ACTIVATION",
}

ALLOWED_PRIMARY_MAINTENANCE_CLASSES = {
    "DOC_NORMALIZATION",
    "TEST_FIXTURE_MAINTENANCE",
    "REGRESSION_TEST_ADDITION",
    "NON_AUTHORITATIVE_OBSERVABILITY",
    "METADATA_CLEANUP",
    "LINK_PRESENTATION_FIX",
    "CI_STATE_INTERPRETATION",
}


def _family_key(value: str) -> str:
    return "_".join(value.strip().upper().split())


@dataclass(frozen=True)
class RegressionEvent:
    event_id: str
    level: str
    project_id: str
    family: str
    signature: str
    provenance: str
    severity: int
    evidence_ref: str
    remediated: bool = False
    remediation_ref: str = ""
    post_remediation_recurrence: bool = False
    authority_conveyed: bool = False

    @staticmethod
    def fingerprint(family: str, signature: str) -> str:
        normalized = f"{_family_key(family)}|{' '.join(signature.lower().split())}"
        return sha256(normalized.encode("utf-8")).hexdigest()

    @property
    def fingerprint_value(self) -> str:
        return self.fingerprint(self.family, self.signature)

    def validate(self) -> None:
        if self.level not in LEVELS:
            raise ValueError("REGRESSION_LEVEL_INVALID")
        if self.provenance not in PROVENANCE_WEIGHTS:
            raise ValueError("PROVENANCE_INVALID")
        if self.authority_conveyed:
            raise ValueError("REGRESSION_EVENT_CANNOT_CONVEY_AUTHORITY")
        if not 1 <= self.severity <= 5:
            raise ValueError("SEVERITY_OUT_OF_RANGE")
        if not self.event_id or not self.family.strip() or not self.signature.strip() or not self.evidence_ref:
            raise ValueError("REGRESSION_EVENT_INCOMPLETE")
        if self.level != "UNSCOPED_CHAT" and not self.project_id:
            raise ValueError("PROJECT_ID_REQUIRED")
        if (self.remediated or self.post_remediation_recurrence) and not self.remediation_ref:
            raise ValueError("REMEDIATION_REFERENCE_REQUIRED")


@dataclass(frozen=True)
class LedgerSnapshot:
    record_count: int
    head_hash: str


@dataclass
class RegressionLedger:
    events: list[RegressionEvent] = field(default_factory=list)
    hashes: list[str] = field(default_factory=list)

    def append(self, event: RegressionEvent) -> str:
        event.validate()
        if any(existing.event_id == event.event_id for existing in self.events):
            raise ValueError("EVENT_ID_REPLAY_DENIED")
        previous_hash = self.hashes[-1] if self.hashes else ""
        digest = sha256(
            json.dumps(
                {"event": asdict(event), "previous_hash": previous_hash},
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        self.events.append(event)
        self.hashes.append(digest)
        return digest

    def snapshot(self) -> LedgerSnapshot:
        return LedgerSnapshot(len(self.events), self.hashes[-1] if self.hashes else "")

    def verify(self) -> bool:
        previous_hash = ""
        for event, expected in zip(self.events, self.hashes):
            digest = sha256(
                json.dumps(
                    {"event": asdict(event), "previous_hash": previous_hash},
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            if digest != expected:
                return False
            previous_hash = digest
        return len(self.events) == len(self.hashes)

    def verify_snapshot(self, expected: LedgerSnapshot) -> bool:
        return self.verify() and self.snapshot() == expected

    def family_stats(self, family: str) -> dict[str, object]:
        key = _family_key(family)
        events = [event for event in self.events if _family_key(event.family) == key]
        if not events:
            return {
                "count": 0,
                "confidence": 0.0,
                "projects": 0,
                "recurrence_after_remediation": 0,
                "remediation_effectiveness": None,
            }
        confidence = sum(
            PROVENANCE_WEIGHTS[event.provenance] * (event.severity / 5)
            for event in events
        ) / len(events)
        remediated = sum(1 for event in events if event.remediated)
        recurrence = sum(1 for event in events if event.post_remediation_recurrence)
        effectiveness = None
        if remediated:
            effectiveness = round(max(0.0, 1 - recurrence / remediated), 4)
        return {
            "count": len(events),
            "confidence": round(min(confidence, 1.0), 4),
            "projects": len({event.project_id for event in events if event.project_id}),
            "recurrence_after_remediation": recurrence,
            "remediation_effectiveness": effectiveness,
        }

    def candidate(self, family: str) -> str:
        stats = self.family_stats(family)
        if not stats["count"]:
            return "NONE"
        if (
            stats["recurrence_after_remediation"]
            or stats["projects"] >= 3
            or stats["count"] >= 5
        ):
            return "SERVICE_PACK_CANDIDATE"
        if stats["confidence"] >= 0.55 and stats["count"] >= 2:
            return "HOTFIX_CANDIDATE"
        return "OBSERVE"


def normalize_intake(
    *,
    event_id: str,
    level: str,
    project_id: str,
    family: str,
    signature: str,
    provenance: str,
    severity: int,
    evidence_ref: str,
) -> RegressionEvent:
    event = RegressionEvent(
        event_id=event_id,
        level=level,
        project_id=project_id,
        family=_family_key(family),
        signature=" ".join(signature.split()),
        provenance=provenance,
        severity=severity,
        evidence_ref=evidence_ref,
    )
    event.validate()
    return event


def primary_maintenance_allowed(
    change_class: str,
    *,
    reversible: bool,
    tests_passed: bool,
    bounded_scope: bool,
    touches_security: bool = False,
    cross_project_write: bool = False,
) -> bool:
    normalized = _family_key(change_class)
    if normalized not in ALLOWED_PRIMARY_MAINTENANCE_CLASSES:
        return False
    if touches_security or cross_project_write or normalized in PROTECTED_CLASSES:
        return False
    return bool(reversible and tests_passed and bounded_scope)
