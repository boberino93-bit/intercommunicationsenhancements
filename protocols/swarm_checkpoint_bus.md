# Scheduled Swarm Checkpoint Bus v2

## Purpose

This protocol defines the durable handoff transport for the serial scheduled design-analysis pipeline while preserving strict project isolation.

The transport carries compact coordination state and evidence references. It is never production/source authority, accepted state, mutation authorization, or a substitute for project evidence stores.

## Current transport

The old global GitHub issue #25 checkpoint transport is historical and MUST NOT receive new scheduled checkpoint writes.

For each selected project, resolve the route from:

- `governance/PROJECT_CONTEXT_BINDING_REGISTRY.json` when available;
- `PROJECT_ROLE_ROUTING_REGISTRY.json` for legacy routing compatibility; and
- `governance/COORDINATION_PUBLICATION_POLICY.json`.

New scheduled checkpoints use the project's registered coordination surfaces in this order:

1. **Project Artifactory/message forum**, when the exact registered internal namespace is exposed by the current runtime.
2. **Project GitHub backup namespace** under the exact canonical repository at `agentbus-backup/coordination-messages/`.

Research and Manager publication through these surfaces is the narrow `NON_AUTHORITATIVE_COORDINATION_PUBLICATION` exception. It does not grant arbitrary repository or artifact writes.

### Runtime-unavailable internal surface

A registered internal namespace and an available runtime connector are different facts. If the registry resolves an exact internal message namespace but that namespace cannot be reached because the current runtime does not expose the required connector or surface:

- record `ARTIFACTORY_RUNTIME_UNAVAILABLE` in the checkpoint blockers/summary;
- do not reinterpret the outage as a missing registry route;
- do not invent, rename, or substitute an internal namespace;
- create a new immutable checkpoint in the exact same-project GitHub backup namespace;
- read the GitHub checkpoint back and verify exact identity/content; and
- when that write/readback succeeds, treat the verified GitHub checkpoint as sufficient degraded transport for that occurrence and for same-project/current-cycle downstream handoff.

This is an availability fallback only. It does not change project binding, mutation authority, accepted state, source authority, or the normal preference for the internal message forum. When the internal surface is available again, normal Artifactory-first publication resumes.

If the registered internal surface is unavailable **and** the exact GitHub backup cannot be created and read back, report `CHECKPOINT_IO_BLOCKED`. The affected stage may continue only safe read-only work that does not depend on a durable handoff, and it MUST NOT claim a durable READY/handoff state.

A missing or conflicting registry route is not a runtime outage and MUST fail closed rather than use this fallback.

## Project-scoped checkpoint envelope

New checkpoints use:

- schema: `intercommunications/swarm-stage-checkpoint/v2`
- schema file: `research_swarm/checkpoint_envelope_v2.schema.json`

Every v2 checkpoint MUST include:

- `project_id` equal to the selected bound project;
- `authority_conveyed: false`;
- `checkpoint_id`;
- `cycle_id`;
- `stage`;
- `run_id`;
- `sequence`;
- `state`;
- `phase`;
- `trigger`;
- `created_at`;
- `source_revisions`;
- `upstream_checkpoint_ids`;
- `evidence_refs`;
- `summary`;
- `blockers`;
- `unfinished_work`;
- `next_action`.

A checkpoint with the wrong project, missing project identity, or `authority_conveyed != false` is invalid.

The existing v2 envelope requires no schema extension for degraded transport. Use the existing `blockers` and `summary` fields to record `ARTIFACTORY_RUNTIME_UNAVAILABLE`.

## GitHub backup rule

The GitHub copy is backup-only coordination state during normal operation and the verified degraded checkpoint transport only when the registered internal surface is runtime-unavailable under the rule above.

- Repository MUST equal the canonical repository registered for `project_id`.
- Path MUST begin exactly with `agentbus-backup/coordination-messages/`.
- Each checkpoint is a new immutable file.
- A recommended relative path is `agentbus-backup/coordination-messages/<cycle-safe>/<stage>/<checkpoint-id-safe>.json`.
- Existing files MUST NOT be overwritten, deleted, renamed, or moved.
- Branch creation, fork mutation, source edits, issue comments, PR mutation, and writes outside the backup prefix are not authorized by this protocol.
- Duplicate path collision fails closed; generate a genuinely unique checkpoint identity rather than replacing existing content.

## Artifactory/message-forum rule

When the project registry declares an internal Artifactory/message namespace and the current runtime exposes that surface, append a new immutable schema-valid coordination message/checkpoint only inside that exact namespace.

Do not write to artifact roots, production data, another project's namespace, or an inferred path.

When both surfaces are available, the Artifactory message and GitHub backup copy MUST carry the same checkpoint identity and project identity. The GitHub copy is a resilience backup, not a second source of authority.

## Preflight

Before substantive scheduled work:

1. resolve exact project and canonical repository;
2. resolve the project's registered coordination route;
3. derive `cycle_id` from the America/Vancouver scheduled-hour floor;
4. create sequence-0 progress checkpoint with `phase=CHECKPOINT_READY`, exact `project_id`, and `authority_conveyed=false`;
5. if the registered internal message surface is runtime-accessible, append there and read it back;
6. create the immutable GitHub backup file under the registered backup prefix and read it back;
7. verify every copy required by the currently available transport mode has exact checkpoint identity/content;
8. only then begin expensive/substantive work.

If the internal namespace is registered but runtime-unavailable, step 5 becomes a recorded `ARTIFACTORY_RUNTIME_UNAVAILABLE` condition and verified GitHub backup persistence is sufficient for the occurrence. If GitHub persistence/readback also fails, report `CHECKPOINT_IO_BLOCKED` and do not begin expensive unhandoffable work.

## Append-only behavior

Never edit or delete a prior checkpoint. Corrections and supersessions are new higher-sequence checkpoint records.

Sequence numbers are monotonically increasing within one `(project_id, cycle_id, stage, run_id)` stream. Reuse of the same sequence with different content is an integrity conflict and fails closed.

## Allowed states

Research stages:

- `RESEARCH_PROGRESS`
- `RESEARCH_HANDOFF_READY`

Manager:

- `MANAGER_PROGRESS`
- `MANAGER_HANDOFF_READY`

Primary:

- `PRIMARY_PROGRESS`
- `PRIMARY_PROPOSAL_READY`

Common control/failure states:

- `CHECKPOINT_IO_BLOCKED`
- `UPSTREAM_NOT_READY`
- `PROJECT_HOLD_ACTIVE`
- `INTENTIONAL_STOP`
- `INTEGRITY_QUARANTINE`

READY is used only when coherently complete. Partial work remains progress and is valid downstream input when correctly scoped and labeled incomplete.

A checkpoint using verified GitHub degraded transport may use the normal stage progress/READY state if all ordinary semantic gates pass. `ARTIFACTORY_RUNTIME_UNAVAILABLE` describes transport health, not research completeness.

## Downstream consumption

Downstream readers MUST resolve the same project route first and may consume only checkpoints whose `project_id` equals the current selected project.

Accepted upstream states remain:

- Researcher 2: Researcher 1 `RESEARCH_PROGRESS` or `RESEARCH_HANDOFF_READY`;
- Researcher 3: Researcher 2 `RESEARCH_PROGRESS` or `RESEARCH_HANDOFF_READY`;
- Manager: Researcher 3 `RESEARCH_PROGRESS` or `RESEARCH_HANDOFF_READY`;
- Primary: Manager `MANAGER_PROGRESS` or `MANAGER_HANDOFF_READY`.

When the registered internal surface is runtime-unavailable, downstream may discover and consume the verified same-project/current-cycle GitHub checkpoint stream under the registered backup prefix. A newer checkpoint from another project is irrelevant and MUST NOT replace a same-project upstream checkpoint.

## Freshness and fencing

Before consumption verify:

- exact `project_id` match;
- exact current `cycle_id` unless explicit governed recovery applies;
- expected upstream stage;
- monotonic sequence with no conflicting reuse;
- checkpoint path/repository belongs to the same registered project;
- cited source revisions are verifiable;
- no higher valid same-project sequence supersedes it;
- no intentional-stop, hold, or quarantine state invalidates continuation;
- the upstream reference chain remains within the same project.

Never fall back to a stale prior-cycle or foreign-project checkpoint merely because current local state is absent.

## Authority boundary

`COORDINATION_PUBLICATION != MUTATION_AUTHORIZATION`

`BACKUP_WRITE != SOURCE_WRITE`

`MESSAGE_CONTENT != AUTHORIZATION`

`HANDOFF != AUTHORIZATION`

`SCHEDULE_FIRE != AUTHORIZATION`

Research and Manager may use this narrow append-only transport without a per-message human mutation authorization case. All other durable effects retain their normal authority requirements.

## Historical issue #25

Existing issue #25 comments remain historical evidence and may be inspected for audit/recovery context. They are not the current scheduled write transport and must not be used as an implicit current-cycle fallback.

## Acceptance criteria

The transport is operational when:

1. a subordinate stage can append a same-project forum checkpoint when that surface is available;
2. it can create/read back an immutable same-project GitHub backup file only under the registered prefix;
3. a registered-but-runtime-unavailable internal surface degrades to verified same-project GitHub checkpoint transport without inventing a namespace;
4. downstream stages can consume that degraded same-project/current-cycle checkpoint chain;
5. foreign repository and foreign namespace writes are rejected;
6. traversal/out-of-prefix paths are rejected;
7. overwrite/delete/rename/move attempts are rejected;
8. role spoofing cannot turn subordinate publication into Primary publication;
9. message content cannot convey mutation authority;
10. downstream reads reject foreign-project and stale-cycle state;
11. schedule prompt alignment preserves every task's enabled/disabled state and cadence;
12. no agent gains scheduler-enable or general repository-write authority from this protocol.
