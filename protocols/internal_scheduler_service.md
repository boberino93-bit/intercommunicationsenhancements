# Internal Spawn Scheduler Service v1

## Purpose

The Internal Spawn Scheduler is an independent control-plane clock for creating governed worker-launch requests without relying on an already-running model session to remember to continue.

It exists to separate five facts that were previously easy to conflate:

1. a schedule boundary became due;
2. a spawn ticket was created;
3. a host/provider accepted a launch request;
4. a mapped ChatGPT frontend execution was actually observed;
5. a worker session actually started and reached bootstrap readiness.

None of those facts implies the next one unless the required receipt exists.

## Bootstrap service contract

The service is part of the bootstrap control plane through:

- `governance/INTERNAL_SPAWN_SCHEDULER_POLICY.json`;
- `governance/INTERNAL_SPAWN_SCHEDULES.json`;
- `governance/SCHEDULER_SYNCHRONIZATION_DIRECTIVE.json`;
- `governance/SCHEDULER_FRONTEND_BINDINGS.json`;
- `governance/SCHEDULER_FRONTEND_RECEIPT_POLICY.json`;
- `schemas/scheduled_spawn_ticket.schema.json`;
- `schemas/frontend_execution_receipt.schema.json`;
- `org_agent_mesh.internal_scheduler`;
- `org_agent_mesh.scheduler_reconciliation`;
- `org_agent_mesh.frontend_execution_receipts`;
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

Scheduler synchronization does not bypass `org_agent_mesh.schedule_activation`. Capacity availability is admission evidence, not activation authority. A disabled mapped Scheduled Task stays disabled until a fresh explicit current human enablement request passes the activation gate. Missing or unavailable mapped frontend identities require explicit human replacement authorization; stale execution evidence is report-only and is not replacement authority.

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

## Frontend mapped execution receipts

A backend ticket for `CHATGPT_FRONTEND_MAPPED` is an expectation, not proof that ChatGPT actually executed the mapped task. `FRONTEND_EXECUTION_EXPECTED` must therefore remain unverified until the frontend execution ledger supplies an identity-bound observation.

Only the declared `Bootstrap Spawn Bridge` reconciler may publish frontend execution receipts. Ordinary capacity workers may observe and report drift but may not mint scheduler execution proof.

For every frontend occurrence the reconciler can directly observe, receipt construction must use `org_agent_mesh.frontend_execution_receipts` and bind all of:

- exact `occurrence_id`;
- backend `job_id`;
- declared `binding_id`;
- exact `frontend_automation_id`;
- canonical `scheduled_for`;
- directly observed frontend `last_run_time` as `observed_run_at`;
- the reconciler observation timestamp.

Title similarity, conversation ID, an enabled flag, expected schedule time, a backend spawn ticket, or a successful scheduler workflow is never sufficient execution proof.

Receipt publication is append-only and non-authoritative. Prefer the registered same-project AgentBus/Artifactory coordination route. If that route is unavailable, use only an already-authorized verified same-project degraded persistence route. Never overwrite a prior receipt and never fabricate a receipt when the frontend execution state is unavailable. If the observation cannot be persisted, report `FRONTEND_RECEIPT_PERSISTENCE_BLOCKED`; if the run cannot be observed, report `FRONTEND_EXECUTION_UNVERIFIED`.

A receipt proves only that the declared frontend automation was observed running for the bound occurrence. It conveys no spawn authority, mutation authority, project authority, claim, lease, or completion state.

## Provider admission and bootstrap

A host implementation must use the existing pre-provider admission rules in `org_agent_mesh.launch_admission` and `protocols/scheduled_agent_launch.md` before invoking the model/provider.

Provider rejection before bootstrap is `LAUNCH_PROVIDER_ADMISSION_FAILED` or the more specific admission result. It does not advance project task state.

A host start receipt proves only that the host reports a session start. A frontend execution receipt proves only observed frontend execution. The worker must still validate its project context, role, HOLD/STOP state, claims, authorization, and reach its ordinary bootstrap-ready barrier before protected project work.

## State integrity and observability

Every occurrence should preserve, when observable:

- `scheduled_for`;
- `observed_at`;
- job ID;
- occurrence ID;
- ticket ID;
- requested role set;
- execution surface;
- declared frontend binding ID and frontend automation ID when mapped;
- frontend identity health;
- frontend last-run observation when available;
- frontend execution receipt disposition when mapped;
- adapter result;
- host start receipt;
- provider/admission disposition;
- bootstrap-ready disposition;
- final bounded-work outcome.

Scheduler state mutation and worker execution state are separate ledgers. An unexpected change to a ChatGPT task's enabled state must be reported as scheduler-state drift. Non-destructive reconciliation may repair only fields permitted by the synchronization directive; disabled-to-enabled transitions always remain behind the global activation gate.

## Failure semantics

Normal service outcomes include:

- `NO_DUE_OCCURRENCE`;
- `SPAWN_TICKET_PENDING`;
- `SPAWN_ADAPTER_UNAVAILABLE`;
- `SPAWN_ADAPTER_REJECTED`;
- `DISPATCH_ACCEPTED_START_UNVERIFIED`;
- `SESSION_STARTED_VERIFIED`;
- `FRONTEND_EXECUTION_EXPECTED`;
- `FRONTEND_EXECUTION_UNVERIFIED`;
- `FRONTEND_EXECUTION_RECEIPT_REJECTED`;
- `FRONTEND_RECEIPT_PERSISTENCE_BLOCKED`;
- `ENABLE_AUTHORIZATION_REQUIRED`;
- `REPLACEMENT_AUTHORIZATION_REQUIRED`;
- `STALE_EXECUTION_REPORTED`;
- `CAPACITY_LIMIT_DEFERRED`;
- `LAUNCH_PROVIDER_ADMISSION_FAILED`.

`TASK_FAILED` is reserved for a genuine execution fault that prevents the service from even evaluating the checked-in schedule/policy or emitting an auditable disposition.
