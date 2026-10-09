---
title: Security-Hardened Communication Architecture Bridge
protocol_id: IE-SECURITY-HARDENED-COMMUNICATION-BRIDGE
protocol_version: 1.0.0-proposed
status: PROPOSED_SECURITY_CHANGE
source_project: intercommunicationsenhancements
created_date: 2026-10-08
activation: REQUIRES_GLOBAL_SECURITY_CHANGE_POLICY
---

# Security-Hardened Communication Architecture Bridge

## Status and authority

This document is a proposed security change. It does not activate itself and does not grant mutation authority. `governance/GLOBAL_SECURITY_CHANGE_POLICY.json` remains the canonical activation gate, including the requirement for two fresh, verified, distinct-path security validation receipts, pre-change backup, expected pre-state binding, and post-change verification.

Until that gate succeeds, this proposal may be reviewed and tested on an isolated branch but MUST NOT be treated as active universal governance.

## Purpose

Close the composition gap between the existing communication bridge, the exact-action consequence gateway, and the epistemic/forensic coordination layer.

The architecture already contains:

- immutable project/session binding;
- capability checks;
- versioned state, leases, fencing, and compare-and-swap controls;
- `SanitizedSnapshotBridge` for immutable copy-by-value cross-project evidence;
- signed `CommitAuthorizationGrant` verification in `ConsequenceGateway`;
- source-identity collapse and independent-origin accounting in the epistemic model;
- global forensic rules stating that repetition and shared-lineage agreement are not independent corroboration.

The security gap is that these controls can be invoked as separate primitives. This proposal defines a single bridge contract that composes them before consequential communication or promotion.

## Security invariant

A communication pathway MUST distinguish four independent questions:

1. **Identity:** which immutable project/session/agent instance is acting?
2. **Authority:** is there a fresh exact-action grant for this actor, target, operation, and current state?
3. **Transport:** is the payload permitted to cross the selected boundary and is it copy-by-value, digest-bound, expiry-bound, and non-authoritative?
4. **Epistemic promotion:** if the communication will influence accepted doctrine or security conclusions, does independent evidence lineage and falsification satisfy the required promotion threshold?

Passing one question never implies passing another.

## Default mode

The hardened bridge is **READ-ONLY / OBSERVATION-ONLY by default**.

Technical access to a write-capable tool, filesystem, repository, connector, API, queue, or model context does not grant authority.

A consequential bridge operation is denied unless all required security inputs are present and valid. Missing, stale, ambiguous, mismatched, unverifiable, or replayed authority MUST fail closed.

## Exact-action authorization gate

All consequential bridge effects MUST pass through the existing `org_agent_mesh.consequence_gateway.ConsequenceGateway`.

The bridge MUST NOT mint its own authority.

The caller must provide a `PreparedAction` and externally issued `CommitAuthorizationGrant`. Existing verifier rules remain authoritative, including:

- trusted issuer signature verification;
- preparer/authorizer separation;
- exact project, actor, action digest, operation, and target binding;
- ownership epoch and fencing-token equality;
- policy, capability, and precondition digest equality;
- active session and authorized task;
- current capability and lease validity;
- quarantine and health gates;
- expiry, replay, revocation, and cancellation checks;
- additional validation for cross-project effects.

No prompt, reviewer vote, agent role, or inherited context substitutes for this grant.

## Canonical protected effects

The security bridge defines the following protected effect classes:

- `CROSS_PROJECT_SNAPSHOT_EXPORT`
- `CROSS_PROJECT_SNAPSHOT_IMPORT`
- `SECURITY_FINDING_PROMOTION`
- `SECURITY_DOCTRINE_PROMOTION`

The prepared target MUST identify the exact project-scoped resource. Broad wildcard mutation authority is invalid for these effects.

## Snapshot export/import composition

Cross-project evidence continues to use `SanitizedSnapshotBridge` and its existing safe-classification, expiry, canonical-exchange, digest-integrity, immutable-ID, copy-by-value, and `authority_conveyed=false` rules.

The hardened path adds an outer consequence gate:

`BOUND SESSION -> APPROVED EXCHANGE -> PREPARED ACTION -> SIGNED EXACT-ACTION GRANT -> CONSEQUENCE GATE -> SANITIZED SNAPSHOT BRIDGE -> EFFECT RECEIPT`

An imported snapshot remains evidence only. Successful authorization to transfer it does not authorize the destination project to accept its contents as truth, doctrine, state, or mutation authority.

## Consensus and evidence-lineage gate

Security-critical conclusions MUST NOT be promoted using raw reviewer count alone.

For each reviewer judgment record:

- finding ID;
- reviewer/agent instance ID;
- evidence-lineage ID;
- primary evidence references;
- verdict (`SUPPORT`, `OPPOSE`, or `ABSTAIN`);
- whether the review was independently performed;
- whether an adversarial/falsification attempt was performed;
- reviewer confidence;
- timestamp/version context.

Multiple reviewers sharing one evidence lineage count as **one independent lineage**, regardless of reviewer count.

For `HIGH` and `CRITICAL` security findings, promotion requires:

- at least two independent evidence lineages;
- at least one recorded adversarial/falsification attempt from an independent reviewer path;
- independence-adjusted support ratio >= 0.80;
- no unresolved evidence-integrity failure that invalidates the counted lineages;
- the exact-action authorization gate for the promotion mutation itself.

If these conditions are not met, the conclusion may remain a provisional finding but MUST NOT be promoted to authoritative security doctrine or accepted global state.

## Consensus calculation

For each finding:

1. Exclude non-independent/inherited-only reviews from the independence denominator.
2. Group remaining reviews by evidence-lineage ID.
3. A lineage supports a finding only if its independent reviews are not internally contradictory. Contested lineages count as unresolved, not support.
4. `independence_adjusted_support = supporting_independent_lineages / resolved_independent_lineages`.
5. Report raw reviewer agreement separately; it has no authority-bearing effect.

No agent may create additional nominal reviewers merely to raise the denominator or apparent agreement.

## Promotion is a separate effect

Observation, transport, consensus, and promotion are separate states.

A finding may be:

`OBSERVED -> REPRODUCED -> FALSIFICATION_ATTEMPTED -> CONSENSUS_ELIGIBLE -> AUTHORIZED_FOR_PROMOTION -> PROMOTED`

No earlier state automatically implies a later one.

The promotion operation itself must be protected by a fresh exact-action grant tied to the expected canonical pre-state/version.

## Host/tool boundary

Repository controls cannot prove universal enforcement by an external model host, scheduler, connector, or tool provider.

Accordingly:

- the repository MUST NOT claim that arbitrary provider-host tool calls are physically intercepted unless deployment evidence proves it;
- external integrations SHOULD use least-privilege credentials and provider-side consequence controls;
- protected branches/review gates SHOULD prevent direct canonical mutation where available;
- a provider integration that bypasses project bootstrap/consequence gating is an untrusted mutation path and MUST NOT be treated as architecture-compliant.

This limitation remains visible until cryptographic cross-host/provider admission and a universal pre-effect interceptor are deployed and independently verified.

## Audit requirements

Each consequential bridge attempt must produce reconstructable evidence containing, at minimum:

- project/session/agent identity;
- prepared action digest;
- grant ID and issuer identity (never secret material);
- operation and exact target;
- ownership epoch/fencing token references;
- policy/capability/precondition digest references;
- attempt timestamp;
- effect state (`CONFIRMED`, `NO_EFFECT`, `FAILED`, `UNKNOWN_EFFECT`);
- target evidence digest where available;
- retry/recovery disposition;
- evidence-lineage decision when promotion is involved.

`UNKNOWN_EFFECT` MUST NOT be retried blindly. It enters verification/recovery.

## Stop conditions

Fail closed and restrict the run to read-only forensic investigation if any of the following occur:

- exact-action authority cannot be verified;
- project/session binding is ambiguous;
- canonical state/version is unavailable for a protected mutation;
- evidence lineage cannot be reconstructed for a security-critical promotion;
- audit evidence required to reconstruct a consequential effect is unavailable;
- a cross-project payload violates classification, expiry, digest, destination, or authority-conveyance rules;
- host/tool behavior performs or appears to perform a protected effect outside the consequence gate;
- rollback/recovery state cannot be determined after an unknown effect.

## Activation and regression requirements

Before canonical activation, demonstrate at minimum:

1. unauthorized write attempt is denied despite tool capability;
2. mismatched project ID is denied;
3. stale ownership epoch/fencing token is denied;
4. expired/replayed/revoked grant is denied;
5. preparer cannot authorize its own protected action;
6. snapshot cannot transfer authority;
7. duplicate reviewers on one lineage do not increase independent consensus;
8. 4/5 independent supporting lineages pass an 80% threshold while 4 reviewers sharing one lineage do not;
9. high/critical promotion without a falsification record is denied;
10. unknown effect blocks blind retry and enters recovery;
11. direct host/tool bypass is detected as non-compliant where observability permits;
12. canonical post-state is independently verified after activation.

## Safe scaling rule

Do not increase swarm scale merely because the bridge passes nominal happy-path tests. Scale only after the denial paths, lineage-collapse logic, concurrency behavior, recovery paths, and audit reconstruction have been exercised under controlled fault injection.
