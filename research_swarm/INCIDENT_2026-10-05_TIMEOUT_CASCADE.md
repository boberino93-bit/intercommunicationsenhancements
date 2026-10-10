# Incident: Scheduled Swarm Timeout / Downstream Failure Cascade

Date: 2026-10-05
Status: `RECOVERY CONTRACT IMPLEMENTED; PROJECT OVERLAYS REQUIRE ALIGNMENT`
Scope: recurring scheduled research pipeline across registered projects
First canary investigated: `boberino93-bit/duo-open`

## Observed failure pattern

The task-history surface showed a repeated cross-project pattern:

1. scheduled Research stages ended as `TIMED OUT`;
2. Manager stages then ended as `FAILED` or stopped without useful synthesis;
3. Primary stages then ended as `FAILED` or stopped without a proposal.

The repetition across projects made an independent project-code failure unlikely as the common cause. The shared scheduled handoff/runtime contract was the first system to inspect.

## Root cause

The failure was a **handoff semantics + runtime-boundary mismatch**, not a single project defect.

Earlier scheduled-role contracts could spend the Research execution window doing useful bounded work but still require a terminal `RESEARCH_HANDOFF_READY` marker before Manager would consume anything. If Research reached the host/runtime limit before publishing that final marker, downstream Manager had no accepted current-cycle input and correctly failed closed. Primary then observed no accepted Manager handoff and failed closed as a consequence.

This produced a cascade:

`RESEARCH timeout -> no accepted final handoff -> MANAGER upstream-not-ready -> PRIMARY upstream-not-ready`

Useful partial work could therefore exist while the pipeline still appeared entirely failed.

A second weakness was transport durability. Project-native evidence stores remain authoritative for project facts, but scheduled stage-to-stage coordination needed a small, externally readback-verifiable checkpoint surface that did not depend on one project's internal AgentBus availability.

## Implemented central recovery contract

The canonical schedule is now a three-stage serial pipeline:

- `RESEARCHER_1`: `:00`-`:20`
- `MANAGER`: `:20`-`:40`
- `PRIMARY`: `:40`-next `:00`

Canonical definition: `research_swarm/five_task_schedule.json`.

The scheduled handoff transport is append-only top-level comments on GitHub issue `boberino93-bit/intercommunicationsenhancements#25`, governed by:

- `protocols/swarm_checkpoint_bus.md`
- `research_swarm/checkpoint_envelope.schema.json`

Every stage must perform checkpoint I/O preflight before expensive work:

1. append sequence-0 progress for the current `America/Vancouver` hourly `cycle_id`;
2. re-read the checkpoint bus;
3. verify the exact checkpoint ID/content is externally visible;
4. only then begin substantive work.

After each meaningful bounded unit, the stage publishes a higher-sequence progress checkpoint and verifies readback.

## Partial progress is now a valid handoff

Final READY states remain useful but are no longer required merely to keep the current cycle alive.

Manager accepts:

- `RESEARCH_PROGRESS`
- `RESEARCH_HANDOFF_READY`

Primary accepts:

- `MANAGER_PROGRESS`
- `MANAGER_HANDOFF_READY`

Partial upstream material must remain explicitly labeled incomplete. It may not be silently promoted into a complete dossier/proposal.

This means a runtime timeout after a successfully verified progress checkpoint should degrade the cycle to **partial evidence**, not erase the entire stage.

## Time-budget rule

A scheduled stage must treat checkpoint preservation as part of its runtime budget.

- Do not begin another bounded work unit if doing so risks missing the next handoff boundary.
- Prefer one high-information bounded advance plus durable checkpoint over multiple unfinished advances with no handoff.
- Preserve the newest useful state before `:20`, `:40`, or next `:00` whenever runtime permits.
- READY is truthful completion metadata, not a liveness requirement.

## Freshness and stale-state rules

- Checkpoint streams are keyed by `cycle_id`, stage, and `run_id`.
- Sequence numbers are monotonic within a stream.
- Prior comments are append-only; correction uses a higher sequence.
- A downstream stage consumes only valid current-cycle upstream checkpoints unless an explicit governed carry-forward exists.
- A previous-cycle READY marker is not an implicit substitute for missing current-cycle progress.
- A canary/test comment must never be mistaken for a stage checkpoint.

## Authority boundary

The checkpoint bus is coordination transport only.

It does **not**:

- grant project source mutation authority;
- replace project-native evidence stores;
- grant release/deployment authority;
- grant Class-D consequence authority;
- authorize scheduled-task enablement.

Scheduled-task enablement remains explicit current HUMAN action only. Disabled tasks are deliberate control gates and must not be auto-enabled by recovery, migration, prompt alignment, bootstrap, or health logic.

## Project overlay migration checklist

Each registered project should be checked for drift before its next canary:

1. Remove or clearly supersede any project-local documentation that still describes the old five-role/fan-out schedule.
2. Ensure scheduled roles point to the current central `RESEARCHER_1`, `MANAGER`, and `PRIMARY` prompts.
3. Ensure project overlays describe issue #25 as the scheduled handoff transport while preserving project-native evidence authority.
4. Ensure Manager accepts current-cycle Research progress, not only final READY.
5. Ensure Primary accepts current-cycle Manager progress, not only final READY.
6. Preserve the project's current automation enabled/disabled state during alignment.
7. Require preflight checkpoint append + external readback before expensive work.
8. Reserve end-of-stage time for checkpoint preservation.
9. Reject implicit stale-cycle fallback.
10. Run one project canary and verify a complete checkpoint chain before expanding rollout.

Recommended canary evidence chain:

`RESEARCH_PROGRESS/READY -> MANAGER_PROGRESS/READY -> PRIMARY_PROGRESS/READY`

Each downstream checkpoint must identify the exact upstream checkpoint IDs it consumed.

## Duo Open findings

Duo Open exposed two independent forms of drift during this incident review:

- its project rollout overlay still described the earlier pre-first-run/five-role architecture after the central scheduler had moved to the three-stage serial contract;
- its Fold7 repository uses a baseline-plus-transforms materialization model, so checked-in baseline `app/**` can look older than the latest tested reconstructed runtime unless the build provenance is inspected.

The first issue is directly relevant to the timeout cascade. The second is a project-specific source-of-truth/auditability risk discovered while resuming the Duo screen work; it should not be confused with the scheduler root cause.

## Recovery acceptance criteria

The shared incident is operationally resolved only when project canaries demonstrate all of the following:

- sequence-0 stage checkpoint preflight succeeds and is readback verified;
- useful partial Research work survives a deliberately incomplete stage as `RESEARCH_PROGRESS`;
- Manager consumes that current-cycle progress and persists its own verified checkpoint;
- Primary consumes current-cycle Manager progress and persists its own verified checkpoint;
- stale previous-cycle checkpoints are rejected;
- checkpoint comments are not edited/deleted;
- no automation is enabled or re-enabled without explicit human action;
- project-native evidence limitations are reported rather than invented;
- timeout/failure telemetry distinguishes host timeout from an intentional `UPSTREAM_NOT_READY`, `CHECKPOINT_IO_BLOCKED`, or project-specific defect.

## Current status

The central serial schedule and central role prompts implement the recovery semantics above. Existing saved automations were observed in a disabled state during the incident review and were left disabled.

Remaining work is project-overlay alignment plus canary validation, beginning with Duo Open.
