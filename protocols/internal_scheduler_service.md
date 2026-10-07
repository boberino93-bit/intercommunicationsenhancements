# Internal Spawn Scheduler Service v1

## Purpose

The Internal Spawn Scheduler is an independent control-plane clock for creating governed worker-launch requests without relying on an already-running model session to remember to continue.

It exists to separate four facts that were previously easy to conflate:

1. a schedule boundary became due;
2. a spawn ticket was created;
3. a host/provider accepted a launch request;
4. a worker session actually started and reached bootstrap readiness.

None of those facts implies the next one unless the required receipt exists.

## Bootstrap service contract

The service is part of the bootstrap control plane through:

- `governance/INTERNAL_SPAWN_SCHEDULER_POLICY.json`;
- `governance/INTERNAL_SPAWN_SCHEDULES.json`;
- `schemas/scheduled_spawn_ticket.schema.json`;
- `org_agent_mesh.internal_scheduler`;
- the independent host clock in `.github/workflows/internal-spawn-scheduler.yml`.

The service may run without an active ChatGPT conversation. The bootstrap describes and constrains it; the host clock actually executes it. A bootstrap document by itself is not a daemon.

## Delegated spawn authority

The user's explicit 2026-10-07 instruction authorizes this scheduler service to create and dispatch bounded spawn requests according to the checked-in schedule registry.

That delegation is intentionally narrow:

- allowed worker roles: `research`, `manager`;
- exactly one role is selected by the spawned worker through ordinary demand-driven admission;
- at most one worker may be requested per occurrence;
- PRIMARY creation is prohibited;
- MASTER creation is prohibited;
- autonomous full-swarm start is prohibited;
- a spawn ticket grants no repository, production, financial, credential, destructive, or other protected mutation authority;
- project binding, claims, leases, fencing, consequence gates, and mutation authorization still apply after launch.

The service does not gain permission to enable, re-enable, disable, or reschedule existing ChatGPT Scheduled Tasks. Those remain under their separate human activation gate.

## Scheduling semantics

The reference registry uses deterministic hourly minute offsets. Each due boundary produces a deterministic `occurrence_id` and `ticket_id`.

Missed boundaries use `COALESCE_TO_LATEST`. The scheduler never creates one worker for every historical missed interval after downtime.

Repeated host invocations for the same boundary must preserve the same occurrence identity. The host adapter must treat that identity idempotently.

## Host adapter boundary

`org_agent_mesh.internal_scheduler` can produce tickets without any model/provider integration. Real worker creation requires a host adapter exposed through the deployment environment.

The reference adapter uses:

- `ORG_AGENT_MESH_SPAWN_ENDPOINT` — HTTPS endpoint owned by the deployment host;
- `ORG_AGENT_MESH_SPAWN_TOKEN` — bearer credential supplied by the host secret store.

The adapter submits the full spawn ticket and requires an affirmative response plus a non-empty `spawn_receipt` before it records `SESSION_STARTED_VERIFIED`.

If the endpoint or credential is absent, the correct result is `SPAWN_ADAPTER_UNAVAILABLE`. This is a deployment limitation, not `TASK_FAILED` and not proof that a worker started.

If the host accepts the dispatch but does not provide a start receipt, record `DISPATCH_ACCEPTED_START_UNVERIFIED`.

## Provider admission and bootstrap

A host implementation must use the existing pre-provider admission rules in `org_agent_mesh.launch_admission` and `protocols/scheduled_agent_launch.md` before invoking the model/provider.

Provider rejection before bootstrap is `LAUNCH_PROVIDER_ADMISSION_FAILED` or the more specific admission result. It does not advance project task state.

A host start receipt proves only that the host reports a session start. The worker must still validate its project context, role, HOLD/STOP state, claims, authorization, and reach its ordinary bootstrap-ready barrier before protected project work.

## State integrity and observability

Every occurrence should preserve, when observable:

- `scheduled_for`;
- `observed_at`;
- job ID;
- occurrence ID;
- ticket ID;
- requested role set;
- adapter result;
- host start receipt;
- provider/admission disposition;
- bootstrap-ready disposition;
- final bounded-work outcome.

Scheduler state mutation and worker execution state are separate ledgers. An unexpected change to a ChatGPT task's enabled state must be reported as scheduler-state drift rather than repaired by this service.

## Failure semantics

Normal service outcomes include:

- `NO_DUE_OCCURRENCE`;
- `SPAWN_TICKET_PENDING`;
- `SPAWN_ADAPTER_UNAVAILABLE`;
- `SPAWN_ADAPTER_REJECTED`;
- `DISPATCH_ACCEPTED_START_UNVERIFIED`;
- `SESSION_STARTED_VERIFIED`;
- `LAUNCH_PROVIDER_ADMISSION_FAILED`.

`TASK_FAILED` is reserved for a genuine execution fault that prevents the service from even evaluating the checked-in schedule/policy or emitting an auditable disposition.
