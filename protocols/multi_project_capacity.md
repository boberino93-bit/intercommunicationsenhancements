# Multi-Project Capacity Coordination Protocol

## Purpose

Prevent a multi-project agent ecosystem from consuming repository/artifact write capacity as though every project were isolated.

This protocol turns the previous local “stay 20% below the limit” behavior into a shared, fail-closed capacity model. Each project remains autonomous and owns its own repository. Projects exchange only compact advisory capacity signals so schedulers, Managers, and Primaries can see high-level pressure and needs without sharing mutable project state.

## Core invariants

1. **Twenty percent is reserved capacity.** When a verified hard limit exists, normal automation must target a safe ceiling of `floor(hard_limit * 0.80)`.
2. **Unknown never means unlimited.** If either the hard limit or current usage cannot be verified, that resource is `UNKNOWN`. Nonessential writes are deferred until capacity is measured or Primary explicitly handles the essential write.
3. **No peer mutation.** A project may read a peer capacity signal or receive an approved bounded exchange snapshot. It must never modify another project merely because that peer is under pressure.
4. **Canonical state remains local.** Capacity coordination does not create shared mutable accepted state. Every project publishes its own signal from its own authority boundary.
5. **Recovery history is preserved.** Optimization is achieved by batching, digest deduplication, and transition-driven checkpoints—not by deleting or rewriting immutable evidence.
6. **Capacity signals are advisory.** A peer signal can change scheduling priority or recommend read-only work; it cannot grant authority, approve a release, or authorize a cross-project write.

## Capacity states

For a known positive hard limit:

- `GREEN`: utilization < 60%.
- `AMBER`: utilization >= 60% and < 75%. Prefer batching.
- `PRESERVE`: utilization >= 75% but still below the 80% safe ceiling. Suppress discretionary writes and coalesce checkpoints.
- `RESERVE_ONLY`: usage is at or above the 80% safe ceiling but below the provider hard limit. Only essential canonical writes may consume the reserved 20%.
- `EXHAUSTED`: usage is at or above the verified hard limit. Writes are blocked until capacity is restored/reset.
- `UNKNOWN`: hard limit or usage is not verified. Treat nonessential writes as unsafe.

Percentages are based on the verified provider/configured hard limit, never an inferred maximum.

## Limit evidence

A resource may describe limits for `COMMITS`, `UPLOADS`, `BYTES`, `ARTIFACTS`, or `API_WRITES`.

Allowed evidence classifications:

- `EXPLICIT_CONFIG`: a project/provider configuration states the limit.
- `PROVIDER_OBSERVED`: an authoritative provider response exposes the limit.
- `ERROR_DERIVED`: an error gives useful boundary evidence, but agents must not invent precision the error did not provide.
- `UNKNOWN`: no defensible hard limit is available.

A 413, 429, quota rejection, connector refusal, or similar failure is evidence of pressure. It does not by itself prove an exact maximum unless the provider response explicitly supplies one.

## Write classes

Every repository/artifact write should be classified before emission:

- `ESSENTIAL_CANONICAL`: required to preserve accepted state, a critical blocker, recovery integrity, release integrity, or a human-required decision. May enter the reserved 20% but may not exceed the verified hard limit.
- `COALESCED_CHECKPOINT`: one batched write containing multiple already-durable local changes/findings. Allowed below the safe ceiling, including `PRESERVE`, if it does not cross 80%.
- `DISCRETIONARY`: routine progress chatter, redundant snapshots, intermediate status, duplicate artifacts, or otherwise deferrable persistence.

Rules:

- `GREEN` / `AMBER`: writes are allowed if the projected usage remains at or below the safe ceiling.
- `PRESERVE`: defer `DISCRETIONARY`; allow only coalesced checkpoints that remain within the safe ceiling plus essential writes.
- `RESERVE_ONLY`: allow only essential canonical writes.
- `EXHAUSTED`: block writes.
- `UNKNOWN`: defer nonessential writes; essential canonical writes are permitted only because refusing them could destroy canonical continuity, and Primary must continue trying to establish the real limit.

## Deduplication and coalescing

Before upload/commit:

1. Hash the intended payload.
2. If the digest equals the last persisted payload for that logical artifact/checkpoint, do not write it again.
3. Combine related nonurgent messages, evidence references, checksum updates, and status changes into one checkpoint.
4. Prefer adding capacity metadata to an already-required canonical commit instead of creating a capacity-only commit.
5. Do not publish heartbeat-only commits.
6. Preserve append-only evidence semantics where required; coalescing changes the transport/checkpoint frequency, not the evidence truth.

## Project capacity signal

Each aligned project exposes a compact signal conforming to `schemas/capacity_signal.schema.json`.

Recommended local paths:

- current project-local signal: `.interagent/capacity/current.json`
- transition history: `.interagent/capacity/history/<timestamp>-<state>.json`

`current.json` is refreshed in canonical storage only when one of these is true:

- overall capacity state changes,
- high-level need categories change,
- a hard/safe limit changes,
- Primary explicitly requests a checkpoint,
- the signal can be folded into an already-required commit.

Do not create a standalone repository commit merely to report unchanged usage.

The only cross-project need categories are:

- `REVIEW_REQUIRED`
- `PRIMARY_DECISION`
- `RELEASE_PENDING`
- `CAPACITY_PRESSURE`
- `BLOCKED`

Raw domain findings, secrets, user data, internal accepted-state payloads, or detailed task content are not part of the shared capacity signal.

## Multi-project aggregation

An agent may read multiple peer signals read-only and aggregate them in memory with `aggregate_capacity_signals()`.

The aggregate answers only high-level questions:

- how many projects are in each pressure state,
- which projects require Primary decisions,
- how many projects report each high-level need,
- which projects should favor read-only/batched work.

The aggregate is not a global controller and must not be written into peer repositories.

When a peer signal is absent or exceeds an explicitly configured freshness window, treat that peer's capacity as `UNKNOWN`; do not silently reuse stale capacity assumptions.

## Scheduling behavior

When capacity pressure exists, Managers/Primaries should prefer:

1. read-only research and analysis,
2. local in-memory or working-tree accumulation,
3. batched canonical checkpoints,
4. digest reuse instead of duplicate upload,
5. essential state/recovery/release writes,
6. discretionary chatter last.

A project in `PRESERVE`, `RESERVE_ONLY`, or `UNKNOWN` should advertise `CAPACITY_PRESSURE` when it materially affects scheduling.

## Role duties

### RESEARCH / SPECIALIST

- May inspect peer capacity signals read-only.
- Preserve source project, revision, and measurement time.
- Do not publish routine progress as individual commits when batching is available.
- Report capacity evidence; do not set a hard limit from guesswork.
- Never alter peer capacity state.

### MANAGER / REVIEWER

- Aggregate local write demand and recommend batching/deferral.
- Validate that signals are fresh under an explicit local freshness policy.
- Prefer assigning read-only work when capacity pressure is high.
- Escalate `PRIMARY_DECISION`, `BLOCKED`, or reserve consumption needs.
- Do not convert advisory peer pressure into cross-project authority.

### PRIMARY / ORCHESTRATOR

- Own authoritative local hard-limit configuration/evidence.
- Own exceptions that consume reserved capacity.
- Ensure essential recovery continuity even in `UNKNOWN`.
- Publish only transition/material capacity signals.
- Keep all deployment role packages synchronized when this protocol changes.

## Slack

Slack may display a human-facing multi-project digest, but it is not the inter-project source of truth. Scheduled Slack digests should be derived from current canonical/read-only capacity signals and point back to project evidence.

## Adoption requirement

A project is aligned when it:

1. carries this protocol (or a semantically equivalent project-scoped copy),
2. emits the capacity signal schema,
3. enforces the 20% reserve / unknown-capacity rules,
4. performs digest deduplication and write coalescing,
5. exposes only high-level cross-project needs,
6. keeps peer access read-only,
7. updates its Primary/Manager/Research bootstrap contracts,
8. rebuilds and verifies affected role packages from an exact source revision.
