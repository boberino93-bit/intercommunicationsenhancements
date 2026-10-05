"""v1.8 reliability controls."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
import hashlib, hmac, json, math, os, secrets, time
from collections import defaultdict, deque
from pathlib import Path
from threading import RLock
from typing import Callable, Iterable, Mapping, Sequence

class V18Error(RuntimeError):
    pass

class AdmissionError(V18Error):
    pass

class GovernanceError(V18Error):
    pass

class BreakGlassError(V18Error):
    pass

class SchemaError(V18Error):
    pass

class MigrationError(V18Error):
    pass

class EvidenceError(V18Error):
    pass

class RolloutError(V18Error):
    pass

class RecoveryError(V18Error):
    pass

class TimeReliabilityError(V18Error):
    pass

class CredentialError(V18Error):
    pass

class AssuranceError(V18Error):
    pass

class IntegrityError(V18Error):
    pass

class ReasonCode(str, Enum):
    ADMIT_OK = 'ADMIT_OK'
    QUEUE_FAIRNESS = 'QUEUE_FAIRNESS'
    DEFER_RESOURCE_CAPACITY = 'DEFER_RESOURCE_CAPACITY'
    THROTTLE_ERROR_BUDGET = 'THROTTLE_ERROR_BUDGET'
    SHED_OPTIONAL_WORK = 'SHED_OPTIONAL_WORK'
    PRIORITY_INHERITANCE = 'PRIORITY_INHERITANCE'
    GOVERNANCE_DEADLOCK_SUSPECTED = 'GOVERNANCE_DEADLOCK_SUSPECTED'
    SAFE_MODE_CONTROL_PLANE_INCONSISTENT = 'SAFE_MODE_CONTROL_PLANE_INCONSISTENT'
    REQUIRE_HUMAN_BREAK_GLASS = 'REQUIRE_HUMAN_BREAK_GLASS'
    BREAK_GLASS_AUTH_INVALID = 'BREAK_GLASS_AUTH_INVALID'
    BREAK_GLASS_REPLAY = 'BREAK_GLASS_REPLAY'
    BREAK_GLASS_EXPIRED = 'BREAK_GLASS_EXPIRED'
    BLOCK_SCHEMA_INCOMPATIBLE = 'BLOCK_SCHEMA_INCOMPATIBLE'
    MIGRATION_PAUSED = 'MIGRATION_PAUSED'
    MIGRATION_ROLLBACK = 'MIGRATION_ROLLBACK'
    CAPABILITY_EVIDENCE_UNTRUSTED = 'CAPABILITY_EVIDENCE_UNTRUSTED'
    CAPABILITY_EVIDENCE_ANOMALOUS = 'CAPABILITY_EVIDENCE_ANOMALOUS'
    EVALUATION_CONTAMINATED = 'EVALUATION_CONTAMINATED'
    HOLD_ROLLOUT_REGRESSION = 'HOLD_ROLLOUT_REGRESSION'
    BLOCK_ROLLOUT_RING_SKIP = 'BLOCK_ROLLOUT_RING_SKIP'
    AUTOMATIC_ROLLBACK = 'AUTOMATIC_ROLLBACK'
    BACKUP_CORRUPT = 'BACKUP_CORRUPT'
    RECOVERY_INCOMPLETE = 'RECOVERY_INCOMPLETE'
    REJECT_HANDOFF_STALE = 'REJECT_HANDOFF_STALE'
    CONTROL_LOOP_COOLDOWN = 'CONTROL_LOOP_COOLDOWN'
    ROUTING_CHURN_FREEZE = 'ROUTING_CHURN_FREEZE'
    PAUSE_ERROR_BUDGET_EXHAUSTED = 'PAUSE_ERROR_BUDGET_EXHAUSTED'
    STATE_INTEGRITY_MISMATCH = 'STATE_INTEGRITY_MISMATCH'
    DEPENDENCY_CYCLE = 'DEPENDENCY_CYCLE'
    CLOCK_ROLLBACK = 'CLOCK_ROLLBACK'
    CLOCK_SKEW = 'CLOCK_SKEW'
    SUPPLY_CHAIN_MISMATCH = 'SUPPLY_CHAIN_MISMATCH'
    CREDENTIAL_SCOPE_MISMATCH = 'CREDENTIAL_SCOPE_MISMATCH'
    CREDENTIAL_REVOKED = 'CREDENTIAL_REVOKED'
    CREDENTIAL_EXPIRED = 'CREDENTIAL_EXPIRED'
    ASSURANCE_CASE_INCOMPLETE = 'ASSURANCE_CASE_INCOMPLETE'
    DEGRADED_MODE_DENY = 'DEGRADED_MODE_DENY'

@dataclass(frozen=True)
class ControlDecision:
    decision: str
    reason_code: str
    subsystem: str
    explanation: str
    next_action: str | None = None
    resource_or_slo: str | None = None
    policy_ref: str | None = None

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def ensure_aware(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('timezone-aware datetime required')
    return value.astimezone(timezone.utc)

def iso(value: datetime) -> str:
    return ensure_aware(value).isoformat().replace('+00:00', 'Z')

def parse_iso(value: str) -> datetime:
    return ensure_aware(datetime.fromisoformat(value.replace('Z', '+00:00')))

def canonical_bytes(value) -> bytes:

    def norm(v):
        if isinstance(v, Enum):
            return v.value
        if hasattr(v, '__dataclass_fields__'):
            return norm(asdict(v))
        if isinstance(v, Mapping):
            return {str(k): norm(v[k]) for k in sorted(v)}
        if isinstance(v, (tuple, list)):
            return [norm(x) for x in v]
        if isinstance(v, (set, frozenset)):
            return sorted((norm(x) for x in v))
        if isinstance(v, bytes):
            return v.hex()
        return v
    return json.dumps(norm(value), sort_keys=True, separators=(',', ':')).encode('utf-8')

def digest(value) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()

def sign(value, key: bytes) -> str:
    if not isinstance(key, (bytes, bytearray)) or len(key) < 16:
        raise ValueError('key must be at least 16 bytes')
    return hmac.new(bytes(key), canonical_bytes(value), hashlib.sha256).hexdigest()

def verify_signature(value, signature: str, key: bytes) -> bool:
    try:
        expected = sign(value, key)
    except Exception:
        return False
    return hmac.compare_digest(expected, signature)
