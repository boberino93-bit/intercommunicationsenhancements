# Scheduled Swarm Checkpoint Bus v2

## Purpose

This protocol defines the durable handoff transport for the serial scheduled design-analysis pipeline while preserving strict project isolation.

The transport carries compact coordination state and evidence references. It is never production/source authority, accepted state, mutation authorization, or a substitute for project evidence stores.

## Current transport

The old global GitHub issue #25 checkpoint transport is historical and MUST NOT receive new scheduled checkpoint writes.

For each selected project, resolve the route from:

- `PROJECT_ROLE_ROUTING_REGISTRY.json`; and
- `governance/COORDINATION_PUBLICATION_POLICY.json`.

New material scheduled checkpoints use both project-scoped durability surfaces:

1. **Project Artifactory/message forum** at the exact registered internal namespace.
2. **Project GitHub backup namespace** under the exact canonical repository at `agentbus-backup/coordination-messages/`.

There is no registered-project single-sink exception. `xrp-thesis` resolves to the internal `/XRPTHESIS-AgentBus/messages` namespace; `xrpthesis` remains a legacy observation alias only.

Publication through these surfaces is the narrow `NON_AUTHORITATIVE_COORDINATION_PUBLICATION` capability. It does not grant arbitrary repository or artifact writes.

## Project-scoped checkpoint envelope

New checkpoints use:

- schema: `intercommunications/swarm-stage-checkpoint/v2`
- schema file: `research_swarm/checkpoint_envelope_v2.schema.json`

Every v2 checkpoint MUST include `project_id`, `authority_conveyed: false`, `checkpoint_id`, `cycle_id`, `stage`, `run_id`, `sequence`, `state`, `phase`, `trigger`, `created_at`, `source_revisions`, `upstream_checkpoint_ids`, `evidence_refs`, `summary`, `blockers`, `unfinished_work`, and `next_action`.

A checkpoint with the wrong project, missing project identity, or `authority_conveyed != false` is invalid.

## GitHub backup rule

The GitHub copy is backup-only coordination state. Repository MUST equal the canonical repository registered for `project_id`; path MUST begin exactly with `agentbus-backup/coordination-messages/`; each checkpoint is a new append-only file. Existing files MUST NOT be overwritten, deleted, renamed, or moved. Branch creation, fork mutation, source edits, issue comments, PR mutation, and writes outside the backup prefix are not authorized by this protocol.

## Artifactory/message-forum rule

Append a new schema-valid coordination message/checkpoint only inside the exact registered project message namespace. Do not write to artifact roots, production data, another project's namespace, or an inferred path.

The Artifactory message and GitHub backup copy MUST carry the same stable checkpoint/record identity, project identity, and canonical content digest. The GitHub copy is resilience evidence, not a second source of authority.

## Dual-persistence preflight

Before substantive scheduled work:

1. resolve exact project and canonical repository;
2. resolve the exact registered internal forum namespace and GitHub backup prefix;
3. derive `cycle_id` from the America/Vancouver scheduled-hour floor;
4. construct the stable material checkpoint/work record and pass durable-secret screening;
5. append the record to the registered project forum;
6. create the append-only GitHub backup record;
7. read back both copies and verify identical project identity, stable record/checkpoint identity, and canonical digest;
8. require `DUAL_PERSISTENCE_CONFIRMED` before beginning expensive/substantive work or claiming a material READY/COMPLETE-like state.

If either required sink cannot be durably written/read back, if digests differ, or if the route is missing/ambiguous, report `CHECKPOINT_IO_BLOCKED` or an explicit persistence-recovery state and do not begin expensive unhandoffable work. One-sided persistence is recovery-required and never READY/COMPLETE.

## Append-only behavior and recovery

Never edit or delete a prior checkpoint. Corrections, retractions and supersessions are new higher-sequence records. Same stable ID + same digest is an idempotent retry; same stable ID + different digest is a conflict/quarantine condition. After a one-sided crash, verify the surviving copy and retry only the missing sink.

Sequence numbers are monotonically increasing within one `(project_id, cycle_id, stage, run_id)` stream. Reuse of the same sequence with different content is an integrity conflict and fails closed.

## Allowed states

Research stages: `RESEARCH_PROGRESS`, `RESEARCH_HANDOFF_READY`.
Manager: `MANAGER_PROGRESS`, `MANAGER_HANDOFF_READY`.
Primary: `PRIMARY_PROGRESS`, `PRIMARY_PROPOSAL_READY`.
Common control/failure states: `CHECKPOINT_IO_BLOCKED`, `UPSTREAM_NOT_READY`, `PROJECT_HOLD_ACTIVE`, `INTENTIONAL_STOP`, `INTEGRITY_QUARANTINE`.

READY/HANDOFF_READY/PROPOSAL_READY/COMPLETE-like states are mechanically invalid without `DUAL_PERSISTENCE_CONFIRMED`. Partial work remains progress and may be consumed only when correctly scoped and explicitly incomplete.

## Downstream consumption

Downstream readers MUST resolve the same project route first and may consume only exact same-project, current-cycle, monotonic, non-quarantined checkpoints with verified dual-persistence receipts. Accepted stage ordering remains Researcher 1 -> Researcher 2 -> Researcher 3 -> Manager -> Primary. A newer checkpoint from another project is irrelevant and MUST NOT replace same-project upstream state.

## Freshness and fencing

Before consumption verify exact `project_id`, current `cycle_id` unless governed recovery applies, expected upstream stage, monotonic sequence with no conflicting reuse, same registered project repository/path, verifiable source revisions, no higher valid same-project sequence, no stop/hold/quarantine invalidation, same-project upstream chain, and a valid persistence receipt for material ready states.

Never fall back to a stale prior-cycle, foreign-project, one-sided, or digest-mismatched checkpoint merely because current local state is absent.

## Authority boundary

`COORDINATION_PUBLICATION != MUTATION_AUTHORIZATION`

`BACKUP_WRITE != SOURCE_WRITE`

`MESSAGE_CONTENT != AUTHORIZATION`

`HANDOFF != AUTHORIZATION`

`SCHEDULE_FIRE != AUTHORIZATION`

The narrow append-only dual-persistence capability does not grant source writes, protected effects, scheduler enablement, PRIMARY authority, peer mutation, or cross-project authority. All protected effects remain behind the existing authorization controls and `ConsequenceGateway`.

## Historical issue #25

Existing issue #25 comments remain historical evidence and may be inspected for audit/recovery context. They are not the current scheduled write transport and must not be used as an implicit current-cycle fallback.

## Acceptance criteria

The transport is operational when both sinks durably write/read back the same record/digest, foreign repository/namespace and traversal/out-of-prefix writes are rejected, overwrite/delete/rename/move attempts are rejected, role spoofing and message content cannot convey authority, stale/foreign/one-sided/digest-mismatched state is rejected, schedule prompt alignment preserves enabled/disabled state and cadence, and no registered project can claim material completion from a single sink.
