# Scheduled Swarm Checkpoint Bus v1

## Purpose

This protocol defines the durable handoff transport for the serial scheduled design-analysis pipeline:

`RESEARCHER_1 -> MANAGER -> PRIMARY`

It exists to prevent a completed stage from becoming unusable because the scheduled invocation cannot reach a project-native AgentBus/Library write surface. The checkpoint bus carries compact coordination state and references to authoritative evidence; it does not replace project evidence stores, production source truth, or human authorization gates.

## Canonical transport for this pipeline

For the current serial pipeline, the canonical scheduled-stage checkpoint transport is:

- repository: `boberino93-bit/intercommunicationsenhancements`
- GitHub issue: `#25` (`[swarm] Serial pipeline checkpoint bus`)
- transport: append-only top-level issue comments through the connected GitHub app/API
- schema: `research_swarm/checkpoint_envelope.schema.json`

Agents MUST NOT edit or delete prior checkpoint comments. Corrections and supersessions are new higher-sequence comments.

This issue is authoritative only for scheduled stage handoff state. Technical evidence remains authoritative at its project-native source (for example Duo Open repository revisions, AgentBus artifacts/messages, device traces, test outputs, or other explicitly governed project evidence).

## No production/source authority expansion

Writing a checkpoint comment to issue #25 is coordination-state publication, not production/source mutation. It does not grant a Researcher or Manager authority to modify `main`, production code, releases, credentials, scheduler enablement, or any other protected effect.

Scheduled-task enablement remains HUMAN-ONLY. This protocol never authorizes enabling, re-enabling, resuming, or creating replacement recurring tasks.

## Cycle identity

The serial pipeline uses one cycle per local wall-clock hour in `America/Vancouver`. The canonical `cycle_id` is the offset-aware local hour floor for the scheduled occurrence, formatted as:

`YYYY-MM-DDTHH:00:00±HH:MM`

Examples:

- Researcher at 04:00, Manager at 04:20, and Primary at 04:40 all belong to the same 04:00 cycle.
- A run that starts late retains the cycle identity of its scheduled occurrence when known; it does not silently adopt the next hour.
- An interactive human-triggered recovery run MUST use `trigger = USER_INTERACTIVE` and either identify the exact `recovery_of_cycle_id` or clearly state that it is not repairing an existing scheduled cycle.

## Checkpoint envelope

Each durable checkpoint comment contains exactly one machine-readable checkpoint envelope following `research_swarm/checkpoint_envelope.schema.json` and includes at minimum:

- `schema`
- `checkpoint_id`
- `cycle_id`
- `stage`
- `run_id`
- `sequence`
- `state`
- `phase`
- `trigger`
- `created_at`
- `source_revisions`
- `upstream_checkpoint_ids`
- `evidence_refs`
- `summary`
- `blockers`
- `unfinished_work`
- `next_action`
- `readback_verified`

`checkpoint_id` MUST be unique and stable for the comment, preferably `<cycle_id>/<stage>/<run_id>/<sequence>` with characters normalized for transport safety.

Sequence numbers are monotonically increasing within one `(cycle_id, stage, run_id)` stream. A writer MUST NOT reuse a sequence number for different content.

## Allowed states

Stage progress/final states:

- `RESEARCH_PROGRESS`
- `RESEARCH_HANDOFF_READY`
- `MANAGER_PROGRESS`
- `MANAGER_HANDOFF_READY`
- `PRIMARY_PROGRESS`
- `PRIMARY_PROPOSAL_READY`

Cross-stage failure/control states:

- `CHECKPOINT_IO_BLOCKED`
- `UPSTREAM_NOT_READY`
- `INTENTIONAL_STOP`
- `INTEGRITY_QUARANTINE`

A final READY state is permitted only when that stage's output is coherently complete enough for downstream use. Partial work MUST remain a `*_PROGRESS` checkpoint and be explicitly labeled incomplete.

## Mandatory checkpoint preflight

Before substantive stage work, every scheduled invocation MUST prove checkpoint transport availability.

1. Resolve identity, governance, project binding, current cycle, and issue #25.
2. Read the issue and current-cycle checkpoints.
3. Append a compact sequence-0 `*_PROGRESS` checkpoint with `phase = CHECKPOINT_READY`.
4. Read the issue comments back and verify the exact new checkpoint is observable.
5. Set `readback_verified = true` only after successful readback.
6. Only then begin the expensive/substantive bounded work unit.

If write or readback fails, do not begin substantive work. Return/report `CHECKPOINT_IO_BLOCKED` with the exact failure. If the bus itself cannot be written, the failure may exist only in the task output; never falsely claim it was durably persisted.

## Rolling persistence

After each meaningful bounded work unit, append a higher-sequence progress checkpoint. Also checkpoint before the stage boundary (`:20` for Researcher, `:40` for Manager, next `:00` for Primary) whenever runtime permits.

Do not begin another bounded unit when doing so would jeopardize preserving the current material result.

A later checkpoint references earlier evidence instead of duplicating bulky payloads. The bus should remain compact.

## Downstream consumption

### Manager

Manager accepts the newest valid current-cycle Researcher checkpoint whose state is either:

- `RESEARCH_PROGRESS`, or
- `RESEARCH_HANDOFF_READY`.

Manager MUST NOT require a final READY marker if a valid current-cycle progress checkpoint exists. It MUST clearly label incomplete upstream material.

### Primary

Primary accepts the newest valid current-cycle Manager checkpoint whose state is either:

- `MANAGER_PROGRESS`, or
- `MANAGER_HANDOFF_READY`.

Primary MUST NOT require a final READY marker if a valid current-cycle progress checkpoint exists. It MUST clearly label incomplete upstream material and MUST NOT claim `PRIMARY_PROPOSAL_READY` unless the proposal is coherently complete.

## Freshness and fencing

Downstream stages MUST verify all of the following before consumption:

- exact `cycle_id` match unless an explicit governed carry-forward is present;
- expected upstream `stage`;
- monotonic sequence and no conflicting reuse of `(run_id, sequence)`;
- cited source revisions exist or are otherwise verifiable;
- the checkpoint is not superseded by a higher valid sequence;
- intentional-stop or quarantine state has not invalidated the work;
- upstream checkpoint references form a coherent chain.

A stale prior-cycle checkpoint MUST NOT be silently used merely because the current cycle has no output.

## Late upstream deltas

A stage may continue past its nominal boundary only when the host runtime permits and governance allows it. Any later material delta is a higher-sequence checkpoint in the same cycle.

Manager MUST re-read the Researcher stream immediately before publishing `MANAGER_HANDOFF_READY`. Primary MUST re-read the Manager stream immediately before publishing `PRIMARY_PROPOSAL_READY`. If a newer material upstream checkpoint appeared, merge it or explicitly defer it; do not silently finalize against known stale input.

Once a downstream final checkpoint has been published, a still-later upstream delta does not rewrite history. It is recorded as a later checkpoint and either triggers an explicit superseding downstream checkpoint when runtime safely allows or becomes carry-forward input for the next cycle.

## Failure classification

Do not collapse all failures into a generic stage failure. At minimum distinguish:

- `WORK_FAILED`: substantive stage work failed;
- `CHECKPOINT_IO_BLOCKED`: durable handoff transport failed;
- `UPSTREAM_NOT_READY`: no valid current-cycle upstream checkpoint exists;
- `GITHUB_CONNECTOR_BLOCKED`: required GitHub access is unavailable;
- `INTEGRITY_QUARANTINE`: ownership/provenance/fencing integrity is uncertain;
- `INTENTIONAL_STOP`: canonical lifecycle control forbids continuation.

A run may have successful substantive analysis and still have `CHECKPOINT_IO_BLOCKED`; in that case downstream MUST treat the result as unavailable until it is durably recovered.

## Interactive Primary / recovery runs

A manually opened or human-triggered Primary session is not automatically the scheduled Primary occurrence. If it participates in recovery it MUST:

- use `trigger = USER_INTERACTIVE`;
- identify `recovery_of_cycle_id` when repairing a scheduled cycle;
- consume only real durable upstream checkpoints;
- never fabricate a missing Manager or Researcher checkpoint;
- preserve the same authority boundaries as scheduled Primary;
- publish a new append-only recovery/superseding checkpoint rather than rewriting old comments.

## Source of truth boundaries

The checkpoint bus answers: "what durable stage state is available for this scheduled cycle?"

It does not answer by itself:

- whether a technical claim is true;
- whether code on `main` is current;
- whether a device test passed;
- whether an agent owns a project lane;
- whether a human authorized a protected action.

Those remain governed by the applicable project, repository, evidence, claim/fence, and consequence-control mechanisms.

## Acceptance criteria

The transport patch is considered operational when all of these are demonstrated:

1. a scheduled stage can append and read back a checkpoint without mutating production source;
2. Manager can consume current-cycle `RESEARCH_PROGRESS` when READY is absent;
3. Primary can consume current-cycle `MANAGER_PROGRESS` when READY is absent;
4. stale prior-cycle state is rejected;
5. conflicting sequence reuse fails closed;
6. transport outage is detected before expensive work;
7. late higher-sequence upstream state is re-read before finalization;
8. automation prompt alignment preserves each task's existing enabled/disabled state;
9. no agent gains scheduler-enable authority from this protocol.
