from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Mapping, Sequence

from .self_audit import REQUIRED_SCORE_KEYS, validate_record, verify_chain


class SelfAuditAnalyticsError(ValueError):
    pass


def _validated(records: Sequence[Mapping[str, object]]) -> Sequence[Mapping[str, object]]:
    if not verify_chain(records):
        raise SelfAuditAnalyticsError("AUDIT_ANALYTICS_CHAIN_INVALID")
    return records


def score_history(records: Sequence[Mapping[str, object]], score_key: str) -> list[dict[str, object]]:
    _validated(records)
    if score_key not in REQUIRED_SCORE_KEYS:
        raise SelfAuditAnalyticsError("AUDIT_SCORE_KEY_UNKNOWN")
    return [
        {
            "audit_record_id": record["audit_record_id"],
            "timestamp": record["timestamp"],
            "agent_id": record["agent_id"],
            "agent_role": record["agent_role"],
            "framework_version": record["framework_version"],
            "score": record["scores"][score_key],
        }
        for record in records
    ]


def compare_agents(records: Sequence[Mapping[str, object]], score_key: str) -> dict[str, float]:
    _validated(records)
    if score_key not in REQUIRED_SCORE_KEYS:
        raise SelfAuditAnalyticsError("AUDIT_SCORE_KEY_UNKNOWN")
    grouped: dict[str, list[float]] = defaultdict(list)
    for record in records:
        grouped[str(record["agent_id"])].append(float(record["scores"][score_key]))
    return {agent_id: round(mean(values), 4) for agent_id, values in sorted(grouped.items())}


def compare_roles(records: Sequence[Mapping[str, object]], score_key: str) -> dict[str, float]:
    _validated(records)
    if score_key not in REQUIRED_SCORE_KEYS:
        raise SelfAuditAnalyticsError("AUDIT_SCORE_KEY_UNKNOWN")
    grouped: dict[str, list[float]] = defaultdict(list)
    for record in records:
        grouped[str(record["agent_role"]).upper()].append(float(record["scores"][score_key]))
    return {role: round(mean(values), 4) for role, values in sorted(grouped.items())}


def recurring_findings(records: Sequence[Mapping[str, object]], field: str, minimum_count: int = 2) -> dict[str, int]:
    _validated(records)
    allowed = {
        "strengths",
        "weaknesses",
        "critical_findings",
        "security_findings",
        "behavioral_findings",
        "architecture_findings",
        "authorization_events_detected",
        "authorization_failures_detected",
    }
    if field not in allowed:
        raise SelfAuditAnalyticsError("AUDIT_FINDING_FIELD_UNKNOWN")
    counter: Counter[str] = Counter()
    for record in records:
        for finding in record.get(field, []):
            normalized = " ".join(str(finding).lower().split())
            if normalized:
                counter[normalized] += 1
    return {
        finding: count
        for finding, count in sorted(counter.items())
        if count >= minimum_count
    }


def authorization_failure_recurrence(records: Sequence[Mapping[str, object]]) -> dict[str, int]:
    return recurring_findings(records, "authorization_failures_detected", minimum_count=1)


def framework_usage(records: Sequence[Mapping[str, object]]) -> dict[str, int]:
    _validated(records)
    counter = Counter(str(record["framework_version"]) for record in records)
    return dict(sorted(counter.items()))


def audit_summary(records: Sequence[Mapping[str, object]]) -> dict[str, object]:
    _validated(records)
    return {
        "record_count": len(records),
        "agents": len({record["agent_id"] for record in records}),
        "roles": sorted({str(record["agent_role"]).upper() for record in records}),
        "framework_versions": framework_usage(records),
        "authorization_failure_patterns": authorization_failure_recurrence(records),
    }
