# Agent Self-Audit Framework — Archived v1.0.0

`framework_name: AGENT_SELF_AUDIT_FRAMEWORK`

`framework_version: 1.0.0`

`history_status: IMMUTABLE_VERSION_SNAPSHOT`

This file is the versioned historical snapshot corresponding to the ACTIVE framework introduced with the Agent Self-Audit Ledger. The active source of truth is `governance/audit/templates/AGENT_SELF_AUDIT_FRAMEWORK.md` while version 1.0.0 remains active.

## Common core dimensions

Cognitive: context reconstruction, reasoning quality, cross-domain synthesis, ambiguity handling, edge-case detection, contradiction detection, evidence calibration, hallucination resistance.

Operational: instruction compliance, tool-use discipline, execution verification, state-awareness, failure handling, recovery behavior, handoff quality.

Security: authorization discipline, scope discipline, role-boundary compliance, privilege-escalation resistance, delegation validation, mutation safeguards, provenance discipline, human-control preservation.

Swarm: role understanding, upstream reporting, downstream delegation, inter-agent communication, handoff completeness, duplicate-work avoidance, conflict handling, shared-context utilization.

Self-governance: recognition of uncertainty/limitations, correction after errors, recommendation-vs-authorization distinction, inference-vs-observation distinction, and identification of weaknesses in own behavior.

## Provenance classes

`OBSERVED`, `RETRIEVED`, `REPORTED_BY_AGENT`, `INFERRED`, `EXPECTED`, `UNVERIFIED`.

## Role extensions

PRIMARY: orchestration, decision integration, context consolidation, delegation correctness, final-answer integrity, authorization gating.

MANAGER: task decomposition, researcher allocation, duplication prevention, escalation behavior, result reconciliation, dependency tracking.

RESEARCH / RESEARCHER: source quality, evidence completeness, hypothesis separation, reproducibility, uncertainty reporting, research handoff quality.

SECURITY / AUDIT: adversarial analysis, privilege-path analysis, policy compliance, exploit identification, false-positive control, remediation quality.

## Authority invariant

`Finding != Recommendation != Authorization != Execution`.
