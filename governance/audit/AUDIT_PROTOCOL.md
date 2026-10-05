# Agent Self-Audit Protocol

Status: ACTIVE
Framework: `governance/audit/templates/AGENT_SELF_AUDIT_FRAMEWORK.md`
Framework version: 1.0.0

## Trigger

When an Intercommunication Enhancements architecture agent is asked to self-evaluate, audit itself, assess its performance or capability, review its behavior/compliance, or perform an equivalent introspective assessment, it MUST resolve and execute the current canonical framework.

Failure to retrieve the canonical framework fails closed as `AUDIT_FRAMEWORK_UNAVAILABLE`. The agent must not improvise a replacement framework.

## Required flow

AUDIT REQUEST -> identify agent and role -> resolve canonical framework -> load role extension -> capture relevant context -> evaluate -> classify material evidence -> generate scores/findings/corrective recommendations -> serialize record -> validate schema and integrity -> append new ledger record -> update ledger head -> return human-readable assessment.

## Ledger invariant

Audit history is append-only. Agents may append, reference, compare, and supersede conclusions through a new record. They may not silently edit or delete historical audit records, rewrite scores/evidence, or retroactively change provenance classifications.

Corrections create a new record and reference the earlier record with `supersedes_record` when applicable.

## Integrity

Every record uses deterministic canonical JSON hashing. Each record carries `record_hash` and `previous_record_hash`. `governance/audit/LEDGER_HEAD.json` anchors the expected record count and current head hash so tail truncation can be detected.

## Provenance

Material audit assertions use exactly one of: `OBSERVED`, `RETRIEVED`, `REPORTED_BY_AGENT`, `INFERRED`, `EXPECTED`, `UNVERIFIED`.

## Identity and role

Agent identity, agent instance, assigned role, role version, project, task, and parent/controller where applicable are recorded independently. A role assertion is not identity proof and does not establish authority.

## Framework evolution

Audit execution and framework modification are separate operations. A record may recommend changes, but only the currently designated framework is authoritative. Framework evolution follows `PROPOSED -> REVIEWED -> APPROVED -> VERSIONED -> ACTIVE`.

## Authority boundary

`Finding != Recommendation != Authorization != Execution`.

An audit record, score, finding, recommendation, comparison, recurring pattern, or framework suggestion never authorizes the recommended operational change. Existing mutation and security controls remain fully applicable.

## Regression-learning integration

Validated audit records may be consumed as non-authoritative evidence by the regression-learning subsystem. The audit record's provenance and framework version must be preserved, and consumption never expands authority.
