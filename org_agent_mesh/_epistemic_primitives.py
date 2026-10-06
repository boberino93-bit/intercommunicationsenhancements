from __future__ import annotations

from dataclasses import dataclass, field, asdict, replace
from datetime import datetime, timezone
from enum import Enum, IntEnum
from hashlib import sha256
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence


def _norm(text: str | None) -> str:
    return " ".join((text or "").strip().casefold().split())


def _digest(value) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _parse_ts(value: str | None):
    if not value:
        return None
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return dt.astimezone(timezone.utc)


class EpistemicError(ValueError): pass
class AuthorityError(PermissionError): pass
class StaleModelRevision(RuntimeError): pass


class EvidenceTier(IntEnum):
    DIRECT_CURRENT_OPERATIONAL = 1
    TARGET_DEPLOYMENT = 2
    CURRENT_AUTHORITATIVE = 3
    HISTORICAL_AUTHORITATIVE = 4
    SECONDARY = 5
    INFERENCE = 6


class ClaimStatus(str, Enum):
    CONFIRMED="CONFIRMED"; LIKELY="LIKELY"; PLAUSIBLE="PLAUSIBLE"; UNRESOLVED="UNRESOLVED"
    CONTRADICTED="CONTRADICTED"; SUPERSEDED="SUPERSEDED"; NOT_APPLICABLE="NOT_APPLICABLE"


class TemporalStatus(str, Enum):
    CURRENT="CURRENT"; HISTORICAL="HISTORICAL"; TRANSITIONAL="TRANSITIONAL"; SUPERSEDED="SUPERSEDED"; FUTURE="FUTURE"; UNKNOWN="UNKNOWN"


class ContradictionClass(str, Enum):
    TEMPORAL_TRANSITION="TEMPORAL_TRANSITION"; VERSION_DIFFERENCE="VERSION_DIFFERENCE"; ENVIRONMENT_DIFFERENCE="ENVIRONMENT_DIFFERENCE"
    CONFIGURATION_DIFFERENCE="CONFIGURATION_DIFFERENCE"; DEPLOYMENT_CUSTOMIZATION="DEPLOYMENT_CUSTOMIZATION"; TERMINOLOGY_DIFFERENCE="TERMINOLOGY_DIFFERENCE"
    USER_OR_WORKFLOW_DIFFERENCE="USER_OR_WORKFLOW_DIFFERENCE"; SOURCE_QUALITY_DIFFERENCE="SOURCE_QUALITY_DIFFERENCE"
    INCOMPLETE_EVIDENCE="INCOMPLETE_EVIDENCE"; TRUE_CONTRADICTION="TRUE_CONTRADICTION"; UNRESOLVED="UNRESOLVED"


class HypothesisStatus(str, Enum):
    ACTIVE="ACTIVE"; SUPPORTED="SUPPORTED"; FALSIFIED="FALSIFIED"; SUPERSEDED="SUPERSEDED"; UNRESOLVED="UNRESOLVED"


class PeerDisposition(str, Enum):
    SUPPORT="SUPPORT"; QUALIFY="QUALIFY"; CONTRADICT="CONTRADICT"; DUPLICATE_ORIGIN="DUPLICATE_ORIGIN"
    TEMPORAL_VARIANT="TEMPORAL_VARIANT"; CONTEXT_VARIANT="CONTEXT_VARIANT"; UNRELATED="UNRELATED"


class ResearchMode(str, Enum):
    EXPLORER="EXPLORER"; DOMAIN_SPECIALIST="DOMAIN_SPECIALIST"; HISTORIAN="HISTORIAN"; DEPLOYMENT_SPECIFIC="DEPLOYMENT_SPECIFIC"
    ARCHITECTURE_MAPPER="ARCHITECTURE_MAPPER"; INDEPENDENT_VALIDATOR="INDEPENDENT_VALIDATOR"; SKEPTIC="SKEPTIC"; RED_TEAM="RED_TEAM"
    SOURCE_DEDUP="SOURCE_DEDUP"; CONTRADICTION_ANALYST="CONTRADICTION_ANALYST"; RECONCILER="RECONCILER"; SYNTHESIS="SYNTHESIS"


@dataclass(frozen=True)
class ActorContext:
    project_id: str
    role: str
    agent_instance_id: str
    capabilities: frozenset[str] = frozenset()

    def can_accept_model(self) -> bool:
        return self.role.upper() == "PRIMARY" and "WRITE_ACCEPTED_STATE" in self.capabilities


@dataclass(frozen=True)
class Applicability:
    environment: str | None = None
    software_version: str | None = None
    protocol_version: str | None = None
    deployment_id: str | None = None
    configuration_profile: str | None = None
    terminology_namespace: str | None = None
    workflow_context: str | None = None
    actor_context: str | None = None
    observed_at: str | None = None
    published_at: str | None = None
    effective_from: str | None = None
    effective_until: str | None = None
    temporal_status: TemporalStatus = TemporalStatus.UNKNOWN

    def __post_init__(self):
        for name in ("observed_at", "published_at", "effective_from", "effective_until"):
            _parse_ts(getattr(self, name))


@dataclass(frozen=True)
class EntityRecord:
    entity_id: str; canonical_name: str; entity_type: str; aliases: tuple[str,...]=(); metadata: Mapping[str,object]=field(default_factory=dict)

@dataclass(frozen=True)
class RelationshipRecord:
    relationship_id: str; subject_entity_id: str; predicate: str; object_entity_id: str; applicability: Applicability=Applicability(); confidence: int=50

@dataclass(frozen=True)
class EventRecord:
    event_id: str; event_type: str; entity_ids: tuple[str,...]; occurred_at: str; applicability: Applicability=Applicability(); evidence_refs: tuple[str,...]=()

@dataclass(frozen=True)
class DeploymentContextRecord:
    deployment_id: str; environment: str; software_version: str | None; configuration_refs: tuple[str,...]=(); effective_from: str | None=None; effective_until: str | None=None

@dataclass(frozen=True)
class TermAliasRecord:
    term: str; canonical_entity_id: str; alias_type: str; valid_from: str | None=None; valid_until: str | None=None

@dataclass(frozen=True)
class OpenQuestionRecord:
    question_id: str; question: str; decision_impact: float; dependency_fanout: float; expected_cost: float; expected_information_gain: float; status: str="OPEN"

    @property
    def priority(self) -> float:
        if self.expected_cost <= 0: raise EpistemicError("expected_cost must be > 0")
        return self.expected_information_gain * self.decision_impact * self.dependency_fanout / self.expected_cost


