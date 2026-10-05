from __future__ import annotations

from hashlib import sha256
import json
from typing import Mapping, Sequence


FRAMEWORK_NAME = "AGENT_SELF_AUDIT_FRAMEWORK"
ACTIVE_FRAMEWORK_VERSION = "1.0.0"
CANONICAL_FRAMEWORK_PATH = "governance/audit/templates/AGENT_SELF_AUDIT_FRAMEWORK.md"

PROVENANCE_CLASSES = {
    "OBSERVED",
    "RETRIEVED",
    "REPORTED_BY_AGENT",
    "INFERRED",
    "EXPECTED",
    "UNVERIFIED",
}

REQUIRED_SCORE_KEYS = {
    "context_reconstruction",
    "reasoning_quality",
    "cross_domain_synthesis",
    "ambiguity_handling",
    "edge_case_detection",
    "authorization_discipline",
    "provenance_discipline",
    "role_boundary_compliance",
    "handoff_quality",
    "tool_verification",
    "security_reasoning",
    "self_correction",
}

ROLE_EXTENSIONS = {
    "PRIMARY": (
        "orchestration", "decision_integration", "context_consolidation",
        "delegation_correctness", "final_answer_integrity", "authorization_gating",
    ),
    "MANAGER": (
        "task_decomposition", "researcher_allocation", "duplication_prevention",
        "escalation_behavior", "result_reconciliation", "dependency_tracking",
    ),
    "RESEARCH": (
        "source_quality", "evidence_completeness", "hypothesis_separation",
        "reproducibility", "uncertainty_reporting", "research_handoff_quality",
    ),
    "RESEARCHER": (
        "source_quality", "evidence_completeness", "hypothesis_separation",
        "reproducibility", "uncertainty_reporting", "research_handoff_quality",
    ),
    "SECURITY": (
        "adversarial_analysis", "privilege_path_analysis", "policy_compliance",
        "exploit_identification", "false_positive_control", "remediation_quality",
    ),
    "AUDIT": (
        "adversarial_analysis", "privilege_path_analysis", "policy_compliance",
        "exploit_identification", "false_positive_control", "remediation_quality",
    ),
}

AUDIT_TRIGGER_PHRASES = (
    "self-evaluate",
    "self evaluate",
    "audit yourself",
    "audit itself",
    "self-audit",
    "self audit",
    "assess your performance",
    "assess its performance",
    "review your behavior",
    "review its behavior",
    "evaluate your compliance",
    "evaluate its compliance",
    "capability assessment",
    "behavioral review",
)


class SelfAuditError(ValueError):
    pass


def is_self_audit_request(text: str) -> bool:
    normalized = " ".join(text.lower().split())
    return any(phrase in normalized for phrase in AUDIT_TRIGGER_PHRASES)


def role_extension(role: str) -> tuple[str, ...]:
    return ROLE_EXTENSIONS.get(role.strip().upper(), tuple())


def canonical_record_hash(record: Mapping[str, object]) -> str:
    payload = dict(record)
    payload.pop("record_hash", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_score_mapping(scores: object, required_keys: set[str] | tuple[str, ...], missing_error: str) -> None:
    if not isinstance(scores, Mapping) or not set(required_keys).issubset(scores.keys()):
        raise SelfAuditError(missing_error)
    for key in required_keys:
        value = scores[key]
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 10:
            raise SelfAuditError("AUDIT_SCORE_OUT_OF_RANGE")


def validate_record(record: Mapping[str, object], *, expected_framework_version: str = ACTIVE_FRAMEWORK_VERSION) -> None:
    if record.get("framework_name") != FRAMEWORK_NAME:
        raise SelfAuditError("AUDIT_FRAMEWORK_NAME_MISMATCH")
    if record.get("framework_version") != expected_framework_version:
        raise SelfAuditError("AUDIT_FRAMEWORK_VERSION_MISMATCH")
    if not str(record.get("audit_record_id", "")).startswith("AUDIT-"):
        raise SelfAuditError("AUDIT_RECORD_ID_INVALID")
    if not record.get("agent_id") or not record.get("agent_role") or not record.get("agent_instance"):
        raise SelfAuditError("AUDIT_AGENT_IDENTITY_INCOMPLETE")

    _validate_score_mapping(record.get("scores"), REQUIRED_SCORE_KEYS, "AUDIT_REQUIRED_SCORES_MISSING")

    role_scores = record.get("role_scores")
    if not isinstance(role_scores, Mapping):
        raise SelfAuditError("AUDIT_ROLE_SCORES_REQUIRED")
    required_role_scores = role_extension(str(record.get("agent_role", "")))
    if required_role_scores:
        _validate_score_mapping(
            role_scores,
            required_role_scores,
            "AUDIT_REQUIRED_ROLE_SCORES_MISSING",
        )
    elif role_scores:
        raise SelfAuditError("AUDIT_UNKNOWN_ROLE_EXTENSION_MUST_BE_EMPTY")

    overall = record.get("overall_score")
    if not isinstance(overall, (int, float)) or isinstance(overall, bool) or not 0 <= overall <= 10:
        raise SelfAuditError("AUDIT_OVERALL_SCORE_INVALID")

    evidence = record.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise SelfAuditError("AUDIT_EVIDENCE_REQUIRED")
    for item in evidence:
        if not isinstance(item, Mapping) or item.get("provenance") not in PROVENANCE_CLASSES or not item.get("ref"):
            raise SelfAuditError("AUDIT_EVIDENCE_INVALID")

    expected_hash = record.get("record_hash")
    if not isinstance(expected_hash, str) or expected_hash != canonical_record_hash(record):
        raise SelfAuditError("AUDIT_RECORD_HASH_MISMATCH")


def verify_chain(records: Sequence[Mapping[str, object]]) -> bool:
    previous_id = None
    previous_hash = None
    seen_ids: set[str] = set()
    for index, record in enumerate(records):
        validate_record(record)
        record_id = str(record["audit_record_id"])
        if record_id in seen_ids:
            return False
        seen_ids.add(record_id)
        if index == 0:
            if record.get("previous_audit_record") is not None or record.get("previous_record_hash") is not None:
                return False
        else:
            if record.get("previous_audit_record") != previous_id:
                return False
            if record.get("previous_record_hash") != previous_hash:
                return False
        previous_id = record_id
        previous_hash = record["record_hash"]
    return True


def validate_append(existing_records: Sequence[Mapping[str, object]], new_record: Mapping[str, object]) -> None:
    if not verify_chain(existing_records):
        raise SelfAuditError("AUDIT_EXISTING_CHAIN_INVALID")
    validate_record(new_record)
    if any(record.get("audit_record_id") == new_record.get("audit_record_id") for record in existing_records):
        raise SelfAuditError("AUDIT_RECORD_ID_REPLAY_DENIED")
    if existing_records:
        head = existing_records[-1]
        if new_record.get("previous_audit_record") != head.get("audit_record_id"):
            raise SelfAuditError("AUDIT_PREVIOUS_RECORD_MISMATCH")
        if new_record.get("previous_record_hash") != head.get("record_hash"):
            raise SelfAuditError("AUDIT_PREVIOUS_HASH_MISMATCH")
    else:
        if new_record.get("previous_audit_record") is not None or new_record.get("previous_record_hash") is not None:
            raise SelfAuditError("AUDIT_GENESIS_LINK_INVALID")


def validate_ledger_transition(
    existing_records: Sequence[Mapping[str, object]],
    candidate_records: Sequence[Mapping[str, object]],
) -> None:
    if not verify_chain(existing_records):
        raise SelfAuditError("AUDIT_EXISTING_CHAIN_INVALID")
    if len(candidate_records) < len(existing_records):
        raise SelfAuditError("AUDIT_HISTORY_SHRINK_DENIED")
    if not verify_chain(candidate_records):
        raise SelfAuditError("AUDIT_CANDIDATE_CHAIN_INVALID")
    for index, historical in enumerate(existing_records):
        candidate = candidate_records[index]
        if candidate.get("audit_record_id") != historical.get("audit_record_id"):
            raise SelfAuditError("AUDIT_HISTORY_REORDER_OR_REPLACE_DENIED")
        if candidate.get("record_hash") != historical.get("record_hash"):
            raise SelfAuditError("AUDIT_HISTORICAL_RECORD_MUTATION_DENIED")


def ledger_head(records: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not verify_chain(records):
        raise SelfAuditError("AUDIT_CHAIN_INVALID")
    if not records:
        return {"record_count": 0, "head_record_id": None, "head_record_hash": None}
    head = records[-1]
    return {
        "record_count": len(records),
        "head_record_id": head["audit_record_id"],
        "head_record_hash": head["record_hash"],
    }


def verify_anchored_head(records: Sequence[Mapping[str, object]], anchor: Mapping[str, object]) -> bool:
    try:
        actual = ledger_head(records)
    except SelfAuditError:
        return False
    return (
        actual["record_count"] == anchor.get("record_count")
        and actual["head_record_id"] == anchor.get("head_record_id")
        and actual["head_record_hash"] == anchor.get("head_record_hash")
    )
