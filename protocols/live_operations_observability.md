# Live Operations Observability Protocol v1

Status: ACTIVE
Authority: read-only derived observability
Canonical coordination authority: each project's local AgentBus/durable state
GitHub role: source/version control only; never coordination authority

## Purpose

Provide one trustworthy multi-project operations view without creating a second control plane.

The view MUST distinguish:
- registered vs normalized projects;
- executing, waiting/blocked, idle-ready, stale, and unattributed activity;
- active/executing role instances when canonical presence exists;
- waiting-for-Manager and waiting-for-Primary states;
- source revision drift from the latest durable coordination checkpoint;
- projects where GitHub activity exists but no canonical role presence is available.

## Canonical paths

Each project:
- `<AgentBus>/ops/presence/<agent_id>.json` — replaceable ephemeral presence
- `<AgentBus>/ops/current.json` — replaceable derived project view
- append-only AgentBus messages remain canonical for material findings, handoffs, decisions, supersessions, and accepted state

Organization:
- `/Intercommunication enhancements/AgentBus/ops/LIVE_OPERATIONS_SNAPSHOT.json` — replaceable read-only derived organization view

The organization snapshot MUST NOT be used to grant authority, acquire leases, change project truth, infer acceptance, or override project-local state.

## Role presence contract

A role instance SHOULD refresh presence:
1. after project/role binding;
2. when it starts a bounded assignment;
3. when it changes to a waiting, blocked, paused, redirect, stop, or terminal state;
4. before and after a material handoff;
5. at a bounded liveness interval while long-running work continues.

Presence fields:
- `agent_id`
- `project_id`
- `role` (`PRIMARY`, `MANAGER`, `RESEARCH`, or `MASTER`)
- `state`
- `observed_at_utc`
- optional `task_id`
- optional `checkpoint_ref`

Do not create append-only durable messages for unchanged heartbeats. Presence belongs to the cheap/ephemeral plane.

## Project current view contract

`ops/current.json` SHOULD include:
- exact project/repository identity;
- whether the project is registered and normalized;
- currently observed repository head and observation time;
- repository revision acknowledged by the latest durable coordination checkpoint;
- latest coordination checkpoint ref/time;
- fresh role-presence observations;
- blockers;
- `unattributed_activity=true` when external/source activity is visible but cannot safely be attributed to a canonical live role.

## Source ↔ coordination reconciliation

A newer GitHub/source revision does not become coordination truth.

Derived states:
- `IN_SYNC` — observed source revision matches the revision acknowledged by coordination;
- `PENDING_RECONCILIATION` — source advanced and the coordination checkpoint is still inside the reconciliation grace window;
- `SOURCE_AHEAD_OF_COORDINATION` — source advanced and the durable coordination checkpoint is outside the grace window;
- `COORDINATION_REVISION_MISMATCH` — revisions differ but source is not newer than coordination evidence;
- `REVISION_MISMATCH` / `UNKNOWN` — evidence is insufficient.

`SOURCE_AHEAD_OF_COORDINATION` is an observability warning, not proof of a governance failure.

## Freshness

Default role liveness timeout: 1800 seconds.
Default source/coordination reconciliation grace: 900 seconds.

Projects with a nonterminal role older than the liveness timeout are `STALE`.
Never count stale inferred roles as active agents.

## Aggregation invariants

The organization-wide view MUST:
- use exact stable project/repository identity;
- never invent agent instances from commit volume;
- preserve `ACTIVITY_UNATTRIBUTED` when work is visible but role attribution is absent;
- count only fresh canonical role presence as active agents;
- expose stale/missing evidence instead of guessing;
- remain read-only derived state;
- preserve project isolation and cross-project write denial.

Reference implementation: `org_agent_mesh.operations_view`.
Registry: `LIVE_OPERATIONS_REGISTRY.json`.
