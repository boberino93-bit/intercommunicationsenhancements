# Global Completion Integrity Directive

Version: 2.0.0
Status: ACTIVE HARD GATE
Scope: UNIVERSAL / ALL PROJECTS / ALL AGENTS

## Invariant

Work is not complete while the acting agent knows it has left avoidable damage, temporary artifacts, failed-operation residue, inconsistent state, or self-created defects behind.

A successful primary feature is insufficient by itself. Completion requires restoration of integrity across the bounded change surface.

For material externally relevant agent work, completion and handoff readiness additionally require verified dual durable persistence. A record is not durable merely because one sink accepted it.

## Completion sweep

Before declaring completion, inspect the bounded change surface for accidental or abandoned artifacts, partial writes, stale implementation notes, broken links, retry residue, regressions, inconsistent state, and other known defects created by the work.

For material work, also reconcile the project-local Message Forum and the canonical project GitHub backup. Confirm that both sinks contain the same stable `record_id` and canonical content digest.

## Completion states

- `COMPLETE`: objective met, verification passed, no known avoidable self-created residue remains, and every material externally relevant work record needed to support completion has reached `DUAL_PERSISTENCE_CONFIRMED`.
- `INCOMPLETE_REMEDIATION_REQUIRED`: known avoidable residue remains or a material work record is one-sided/recoverable and remediation is still possible within authority.
- `INCOMPLETE_BLOCKED`: residue remains or dual persistence cannot be completed because a real authority, capability, routing, safety, or integrity boundary blocks remediation.

An agent must not label work complete when cleanup is knowingly outstanding.

`READY`, `HANDOFF_READY`, `COMPLETE`, `PROPOSAL_READY`, `MANAGER_REVIEW_READY`, `PRIMARY_REVIEW_READY`, `RESEARCH_HANDOFF_READY`, `MANAGER_HANDOFF_READY`, and `PRIMARY_PROPOSAL_READY` are mechanically blocked for material work until a receipt bound to the same project, record ID, and digest is `DUAL_PERSISTENCE_CONFIRMED`.

A single successful sink, queued write, unverified backup, stale or unrelated receipt, mismatched digest, or historical checkpoint without a matching receipt cannot satisfy the barrier.

## Dual-persistence recovery semantics

- same project + same `record_id` + same digest: safe idempotent retry;
- same project + same `record_id` + different digest: conflict quarantine;
- Forum only: recovery required, not ready;
- GitHub only: recovery required, not ready;
- two sinks with different digests: quarantine;
- corrections: append a new record that references the superseded record; never rewrite history;
- recovery and reconciliation are coordination functions and never create protected-effect authority.

## Remediation duty

When safe and authorized, remediate self-created damage before completion. If remediation is blocked, preserve evidence, identify the exact blocker, route it to the correct owner, and report `INCOMPLETE_BLOCKED`.

This directive does not expand authority. All normal project, authorization, hold, lease, fence, audit, Reliability Kernel, security, and `ConsequenceGateway` controls continue to apply.

## Post-change verification

Verify both the intended state and the absence of known avoidable self-created degradation in the bounded change surface. For material work, verification includes a read-only dual-plane reconciliation result with zero one-sided records, zero digest mismatches, and zero record-ID/digest conflicts for the relevant scope.

## Inheritance

PRIMARY, MANAGER, RESEARCH, MASTER, scheduled, recovery, child, builder, validator, and newly seeded agents inherit this directive. Local policy may strengthen it but may not weaken it.
