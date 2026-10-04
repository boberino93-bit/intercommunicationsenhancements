# IPG3 Compatibility and Shadow-Mode Migration

Status: **NON-AUTHORITATIVE DESIGN**

This document defines how Protocol 2.4 / Message v2 can be evaluated against IPG3 without changing current runtime authority, deployment packages, or accepted project state.

## Principle

Migration must be observational before it becomes authoritative.

Current Message v2 remains canonical. A shadow projection may derive a Message v3 draft representation from an accepted v2 message, but the projection cannot publish, mutate project state, consume approvals, execute tools, commit side effects, or become accepted state.

## Required invariants

A v2 -> v3 projection must preserve at minimum:

- project identity;
- logical sender identity;
- execution-instance identity;
- recipients;
- message kind and priority;
- correlation and causation;
- reply/supersession relationships;
- idempotency identity;
- expiry;
- evidence and artifact references;
- acknowledgement intent;
- source payload semantics.

A projection that cannot preserve a material v2 invariant must fail rather than guess.

## Deliberate information gaps

Message v2 does not provide authenticated principal identity, delegation contract identity, approval identity, event sequence, provenance records, cryptographic signatures, or side-effect receipts.

Shadow mode therefore represents those values as null/empty rather than fabricating them.

This is a core migration rule:

> absence of G3 evidence must remain absence, not be backfilled from confidence or conversational context.

## Semantic class mapping

Current mapping used by `shadow_projection.py`:

- CLAIM -> WORK
- FINDING -> EVIDENCE
- BLOCKER -> CONTROL
- REQUEST -> WORK
- REVIEW_REQUEST -> REVIEW
- REVIEW_DISPOSITION -> REVIEW
- CONTRADICTION -> EVIDENCE
- HANDOFF -> CONTROL
- DECISION -> DECISION
- SUPERSESSION -> CONTROL
- SERVICE_CHECKPOINT -> OBSERVABILITY
- RELEASE_CLOSE -> CONTROL

Unknown future v2 kinds project to CONTROL for observation only and require explicit review before any authoritative migration.

## Shadow pipeline

1. Current runtime validates Message v2 using Protocol 2.4.
2. Accepted v2 message is provided read-only to the shadow projector.
3. Projector validates v2 shape and refuses cross-project ordinary AgentBus traffic.
4. Projector constructs the proposed v3 envelope.
5. Payload and envelope fingerprints are calculated deterministically.
6. `assert_semantic_projection` verifies protected v2 semantics survived.
7. Shadow output may be stored in disposable test evidence or telemetry.
8. Shadow output is never consumed by the current control plane.

## Migration telemetry

A future shadow runner should measure:

- percentage of accepted v2 messages that project successfully;
- projection failures by reason;
- unrepresentable semantics;
- null G3 fields by category;
- deterministic fingerprint mismatches;
- size overhead;
- processing overhead;
- message-kind mapping ambiguity;
- candidate provenance information available vs missing.

## Promotion stages

### Stage 0 — Design only

Schemas and validators live under `design/`. No runtime or deployment effect.

### Stage 1 — Offline shadow replay

Replay captured non-sensitive Message v2 fixtures through the projector. No live attachment.

### Stage 2 — Live read-only shadow

Accepted v2 traffic may be mirrored into an isolated shadow store. Current Message v2 remains the only authoritative input.

### Stage 3 — Dual validation

Selected message classes must satisfy both current v2 rules and candidate v3 invariants. Actions still execute through v2/control-plane authority.

### Stage 4 — Controlled v3-native pilot

One isolated project may produce v3-native messages for a bounded set of non-destructive operations. A v2 compatibility projection remains available for observation and rollback.

### Stage 5 — Protocol promotion

Only after benchmark, adversarial, recovery, interoperability, packaging, and reproducibility gates pass may IPG3 move from `design/` into authoritative protocol/runtime locations and receive an official protocol version.

## Rollback rule

At every pre-promotion stage, disabling shadow mode must restore the exact G2 behavior without data migration or loss of current authoritative state.

## Compatibility is not authority

An A2A, broker, Slack, GitHub, AGNTCY, or other external adapter may carry or translate an IPG3 envelope in the future. Transport compatibility does not grant project authority. Every imported request must still pass local identity, capability, approval, scope, replay, and effect controls.
