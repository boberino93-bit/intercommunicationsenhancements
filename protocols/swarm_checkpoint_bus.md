# Scheduled Swarm Checkpoint Bus v2

## Purpose

This protocol defines the durable handoff transport for the serial scheduled design-analysis pipeline while preserving strict project isolation.

The transport carries compact coordination state and evidence references. It is never production/source authority, accepted state, mutation authorization, or a substitute for project evidence stores.

## Current transport

The old global GitHub issue #25 checkpoint transport is historical and MUST NOT receive new scheduled checkpoint writes.

For each selected project, resolve the route from:

- `PROJECT_ROLE_ROUTING_REGISTRY.json`; and
- `governance/COORDINATION_PUBLICATION_POLICY.json`.

New scheduled checkpoints use the project's own registered coordination surfaces:

1. **Project Artifactory/message forum**, when a registered internal namespace exists.
2. **Project GitHub backup namespace** under the exact canonical repository at `agentbus-backup/coordination-messages/`.

Research and Manager publication through these surfaces is the narrow `NON_AUTHORITATIVE_COORDINATION_PUBLICATION` exception. It does not grant arbitrary repository or artifact writes.

For `xrp-thesis`, no internal Artifactory namespace is currently registered. Do not invent one. Its eligible coordination transport is the registered project-local GitHub backup namespace only.

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

## GitHub backup rule

The GitHub copy is backup-only coordination state.

- Repository MUST equal the canonical repository registered for `project_id`.
- Path MUST begin exactly with `agentbus-backup/coordination-messages/`.
- Each checkpoint is a new immutable file.
- A recommended relative path is `agentbus-backup/coordination-messages/<cycle-safe>/<stage>/<checkpoint-id-safe>.json`.
- Existing files MUST NOT be overwritten, deleted, renamed, or moved.
- Branch creation, fork mutation, source edits, issue comments, PR mutation, and writes outside the backup prefix are not authorized by this protocol.
- Duplicate path collision fails closed; generate a genuinely unique checkpoint identity rather than replacing existing content.

## Artifactory/message-forum rule

When the project registry declares an internal Artifactory/message namespace, append a new immutable schema-valid coordination message/checkpoint only inside that exact namespace.

Do not write to artifact roots, production data, another project's namespace, or an inferred path.

The Artifactory message and GitHub backup copy MUST carry the same checkpoint identity and project identity. The GitHub copy is a resilience backup, not a second source of authority.

## Preflight

Before substantive scheduled work:

1. resolve exact project and canonical repository;
2. resolve the project's registered coordination route;
3. derive `cycle_id` from the America/Vancouver scheduled-hour floor;
4. create sequence-0 progress checkpoint with `phase=CHECKPOINT_READY`, exact `project_id`, and `authority_conveyed=false`;
5. append it to the project Artifactory/message forum when one exists;
6. create the immutable GitHub backup file under the registered backup prefix;
7. read back every required written copy and verify exact checkpoint identity/content;
8. only then begin expensive/substantive work.

If the project has a registered Artifactory route and either required copy cannot be durably written/read back, report `CHECKPOINT_IO_BLOCKED` and do not begin expensive unhandoffable work.

For projects with no registered Artifactory namespace, verified GitHub backup persistence is sufficient; absence of an Artifactory namespace is not permission to invent one.

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

## Downstream consumption

Downstream readers MUST resolve the same project route first and may consume only checkpoints whose `project_id` equals the current selected project.

Accepted upstream states remain:

- Researcher 2: Researcher 1 `RESEARCH_PROGRESS` or `RESEARCH_HANDOFF_READY`;
- Researcher 3: Researcher 2 `RESEARCH_PROGRESS` or `RESEARCH_HANDOFF_READY`;
- Manager: Researcher 3 `RESEARCH_PROGRESS` or `RESEARCH_HANDOFF_READY`;
- Primary: Manager `MANAGER_PROGRESS` or `MANAGER_HANDOFF_READY`.

A newer checkpoint from another project is irrelevant and MUST NOT replace a same-project upstream checkpoint.

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

1. a subordinate stage can append a same-project forum checkpoint where available;
2. it can create/read back an immutable same-project GitHub backup file only under the registered prefix;
3. foreign repository and foreign namespace writes are rejected;
4. traversal/out-of-prefix paths are rejected;
5. overwrite/delete/rename/move attempts are rejected;
6. role spoofing cannot turn subordinate publication into Primary publication;
7. message content cannot convey mutation authority;
8. downstream reads reject foreign-project and stale-cycle state;
9. schedule prompt alignment preserves every task's enabled/disabled state and cadence;
10. no agent gains scheduler-enable or general repository-write authority from this protocol.
