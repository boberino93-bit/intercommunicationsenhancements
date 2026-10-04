# Agent State Continuity and Master Handoff Standard v1

Status: ACTIVE reference-framework standard.

## Purpose

This standard minimizes restart and handoff time when an agent session ends, expires, crashes, is replaced, or yields work to another human-launched agent. Every participating project keeps one compact current-state index named `MASTER_HANDOFF.json` plus append-only agent state snapshots.

The master handoff is a continuity accelerator. It does not replace the project's canonical message board, accepted decision log, task registry, source repository, or project-specific authority model.

## Required project files

Every project must provide:

1. `MASTER_HANDOFF.json` — the compact current-state index a new agent reads during startup.
2. `.interagent/handoffs/` — append-only per-agent checkpoint records when repository-local state is supported. Projects whose canonical coordination store is an internal Artifactory/Library must persist the equivalent snapshot in that canonical store and may mirror it into the repository.
3. A bootstrap pointer to this standard and the project's `MASTER_HANDOFF.json`.

A project may use an additional internal canonical path for the master handoff. When GitHub is non-canonical, the internal copy is authoritative and the repository copy is a recovery/source mirror. The two copies must carry the same `generation`, `updated_at_utc`, and `source_revision` when synchronized.

## Authority roles and execution modes

Persistent authority roles are:

- `PRIMARY`
- `MANAGER`
- `RESEARCH`

`RECOVERY`, `QA`, `BUILD`, and other bounded functions are execution modes, not additional persistent authority roles. A mode never changes the authority ceiling of the bound role.

## Agent-instance identity

Every running agent must bind both:

- a logical `agent_id`; and
- a unique `agent_instance_id` for that execution/session.

Leases, task ownership, READY records, and handoff checkpoints that can affect mutation authority must include the execution-instance identity. A replacement instance may not renew or release the prior instance's lease merely because it has the same logical `agent_id`.

## Manual checkpoint workflow

Agents must manually update continuity state after any material state transition, including:

- accepting or claiming meaningful work;
- completing a meaningful unit of work;
- changing project files, schemas, packages, release state, or runtime policy;
- accepting or rejecting an integration decision;
- discovering a blocker that changes the next action;
- handing work to another agent;
- before intentionally yielding or ending the session;
- after recovering from a failed or interrupted operation.

Do not create noise for unchanged heartbeat/liveness events. The goal is a small number of high-value checkpoints that let the next agent resume without rereading the whole project.

For each checkpoint:

1. Write an append-only agent snapshot containing the bound project, role, execution mode, `agent_id`, `agent_instance_id`, current task, completed work, unresolved work, blockers, evidence/source refs, last verified repository revision, and exact continuation instructions.
2. Manually update `MASTER_HANDOFF.json` to summarize the new project state and point to the snapshot.
3. Increment `generation` monotonically.
4. Preserve prior expired-agent summaries; never rewrite history to make an abandoned lane appear completed.
5. When the project uses an internal canonical Artifactory/Library, persist and read back the canonical record before treating a repository mirror as synchronized.

## Expired or missing agents

An agent is `EXPIRED` only when there is positive evidence such as lease expiry, explicit handoff/termination, or a project-specific liveness rule. Another agent must not invent work the expired instance did not checkpoint.

When an instance expires unexpectedly:

- preserve its last checkpoint unchanged;
- mark the instance `EXPIRED` or `STALE` in the master record;
- record the evidence used to make that determination;
- move unfinished work into `pending_actions` with a new owner only after normal project authority permits reassignment;
- never transfer a live lease until the lease has expired or been validly released.

## New-agent startup

Before claiming or mutating project work, a new agent must:

1. bind project identity, repository identity, authority role, execution mode, and its unique `agent_instance_id`;
2. read the project's canonical `MASTER_HANDOFF.json`;
3. read only the snapshot(s), board records, decisions, and source revisions referenced by the relevant handoff entries;
4. validate that the master record belongs to the bound project and that referenced source revisions/authority paths are plausible;
5. reconcile any obvious stale or expired agent state without assuming ownership;
6. then classify the requested task and proceed through the project's normal gates.

This ordering intentionally uses the master handoff as an index so replacement agents do not have to scan the entire historical board before becoming useful.

## Required `MASTER_HANDOFF.json` behavior

The record must remain compact and bounded. It should contain current state, not an unbounded transcript.

Required top-level concepts are:

- schema/version;
- project identity;
- monotonically increasing generation;
- last update time and updater instance;
- current project objective;
- current source/release revision;
- active agent instances;
- expired/replaced agent instances with last-known state;
- active workstreams;
- blockers;
- pending actions in priority order;
- recent decisions/evidence references;
- latest checkpoint references;
- canonical authority and mirror information.

Keep detailed narrative, large evidence, logs, and full conversation history outside the master record and reference them instead.

## Swarm interaction

`.swarm/` is project-local operational/recovery state. It is not a second accepted-decision authority. Swarm READY, lease, health, and convergence records must be reconcilable to the project identity and master handoff, while accepted project truth continues to follow the project's canonical coordination authority.

Swarm admission requires:

- project/role/instance binding;
- task classification proving swarm participation is required;
- master handoff loaded;
- package/source parity;
- capacity admission;
- recovery state valid;
- manager/primary gates required by the local project.

## Failure policy

If project identity, master-handoff identity, source authority, role, instance ownership, or required approval is ambiguous, fail closed before mutation. Read-only diagnosis is allowed.

## Optimization objective

The success metric is not the number of messages written. It is the time and context a replacement agent needs to reach a correct, mutation-safe understanding of:

- what was being done;
- what is already complete;
- what remains;
- what is blocked;
- which evidence matters;
- which exact next action is safe.

A well-maintained master handoff should let a replacement agent reach that point by reading one compact record plus a small set of referenced artifacts.
