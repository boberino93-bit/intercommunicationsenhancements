# Bootstrap Internal Scheduler Service v1

Status: **CANDIDATE / HOST-ADAPTER REQUIRED FOR REAL SESSION CREATION**

## Purpose

Provide a scheduler inside the swarm bootstrap/control plane that owns temporal intent independently of any one ChatGPT Scheduled Task occurrence. The service can determine that work is due, reconcile missed boundaries, issue an idempotent spawn ticket, apply provider-admission/backoff policy, and preserve the occurrence in durable state.

The service deliberately separates four facts:

1. **WORK_DUE** — the internal clock says an occurrence should exist.
2. **SPAWN_TICKET_ISSUED** — the control plane has created an idempotent request for a worker.
3. **PROVIDER_ACCEPTED / SESSION_STARTED** — a host adapter has actually created or admitted a model execution.
4. **BOOTSTRAP_READY** — that execution passed project identity, supervisory, routing, and bootstrap gates and may advance project task state.

`SPAWN_TICKET_ISSUED` is never equivalent to `SESSION_STARTED`.

## Runtime

Reference implementation: `org_agent_mesh.internal_scheduler.BootstrapInternalScheduler`.

The scheduler service may remain resident when the host process is persistent. In stateless hosts, every bootstrap may restore the latest durable scheduler snapshot, run one deterministic `tick(now)`, persist any newly issued tickets, and yield. Either mode produces the same occurrence identity for the same schedule boundary.

## Internal schedules

An internal schedule carries at minimum:

- `schedule_id`;
- exact `project_id`;
- bounded `task_id`;
- admissible non-PRIMARY `role_id`;
- recurrence interval;
- `next_due_at` as timezone-aware time;
- enabled/disabled state;
- catch-up policy;
- maximum outstanding ticket count.

The scheduler MUST NOT infer project identity from topic similarity, conversation title, or a recent repository. Exact project routing still comes from canonical bootstrap/routing state.

## Independent scheduling semantics

The scheduler is independent in the following precise sense:

- it does not require an external Scheduled Task boundary in order to decide that an internal occurrence is due;
- missed boundaries are reconciled from durable `next_due_at` state;
- occurrence IDs are deterministic and idempotent;
- the scheduler can issue a spawn ticket whenever an enabled internal schedule becomes due;
- provider retry/backoff state survives the originating timer boundary when persisted by the host.

It is **not** independent of the physical host needed to create a new ChatGPT/model execution. If the host exposes no supported spawn/session API, the correct state is `HOST_SPAWN_ADAPTER_REQUIRED`. The system must never fabricate a session or claim that a ticket created one.

## Host spawn adapter

A host adapter is a narrow boundary implementing the equivalent of:

`submit(SpawnTicket) -> HostLaunchReceipt`

The adapter may call an approved scheduler/provider/work API to request a real execution. It must return the same `ticket_id`, a provider result, and whether an external session actually started.

The adapter does not receive mutation authority from the ticket. All normal launch-context, project, provider-admission, supervisory, claim/lease/fence, and consequence gates remain in force.

If the ChatGPT host later exposes a supported session-spawn primitive, that primitive belongs behind this adapter rather than inside research/manager agents.

## Admission and backpressure

Before host submission, use `org_agent_mesh.launch_admission` or an equivalent pre-provider admission controller. Preserve:

- maximum inflight starts;
- minimum start spacing;
- deterministic staggering when useful;
- bounded exponential backoff with deterministic jitter;
- the same occurrence identity across retry;
- maximum attempts and terminal failure;
- separation of provider launch failure from project work failure.

`TOO_MANY_REQUESTS`, `RATE_LIMITED`, `TEMPORARY_PROVIDER_UNAVAILABLE`, and `TIMEOUT_BEFORE_BOOTSTRAP` are launch/admission failures and must not be recorded as completed project work.

## Catch-up policy

Default recurring research/capacity policy is `COALESCE_TO_LATEST`.

After outage or delayed execution, do not produce one new worker for every missed historical hourly boundary unless historical replay itself has evidentiary value. Supported dispositions are:

- `COALESCE_TO_LATEST` — issue one occurrence for the newest due boundary;
- `SKIP_OBSOLETE` — discard obsolete work and advance to the useful current boundary;
- `REPLAY_REQUIRED` — replay one historical occurrence at a time only when each interval is materially required.

The default maximum outstanding ticket count is one per schedule to prevent restart stampedes.

## Activation and human authority

This service does not erase the existing human schedule-activation gate.

- Disabled -> enabled requires explicit current human action.
- Configuration maintenance must preserve enabled/disabled state.
- A scheduler tick cannot re-enable a disabled schedule.
- A failed or missed occurrence cannot re-enable a disabled schedule.
- Logical restart authority is distinct from scheduler activation authority.

The scheduler itself may be loaded on bootstrap as infrastructure, while individual work schedules remain independently human-gated.

## PRIMARY and full-swarm boundary

The internal scheduler MUST NOT create or self-promote a PRIMARY agent.

It also MUST NOT silently convert one due occurrence into a full swarm. A full swarm remains human-started under current governance. The scheduler may issue bounded RESEARCH or MANAGER/REVIEWER worker tickets only for already-authorized schedule definitions.

If a due objective requires a full swarm, record `HUMAN_SWARM_START_REQUIRED` rather than manufacturing many tickets.

## Persistence

Persist the scheduler snapshot and material transitions through the project-authorized durable state path. The reference snapshot includes schedules, tickets, and explicit invariants.

A durable ticket should preserve:

- schedule and occurrence identity;
- project/task/role;
- scheduled boundary and creation time;
- ticket state;
- launch attempt count;
- provider result and retry deadline;
- explicit `session_started` boolean;
- `authority_conveyed=false`.

If the registered internal AgentBus/Artifactory surface is unavailable at runtime, follow `protocols/non_authoritative_coordination_publication.md` and the current degraded same-project GitHub fallback policy when applicable.

## Bootstrap integration

Bootstrap implementations should load this protocol and scheduler configuration after project-context/identity binding and governance hard gates are available, but before recurring-work dispatch. A startup tick is safe because it can only create internal execution intent; it does not itself grant protected mutation authority.

Recommended bootstrap sequence:

`PROJECT CONTEXT -> IDENTITY/GOVERNANCE -> RESTORE INTERNAL SCHEDULER -> TICK -> ISSUE/RECONCILE TICKETS -> HOST ADMISSION -> PROVIDER ACCEPTED -> NORMAL AGENT BOOTSTRAP -> BOOTSTRAP_READY -> WORK`

## Observability

For each material occurrence preserve, when observable:

- `scheduled_for`;
- `observed_at`;
- `ticket_created_at`;
- admission attempt count;
- provider result;
- external execution/session ID when the host supplies one;
- `session_started`;
- `bootstrap_ready`;
- project/work outcome;
- blocker or retry deadline.

This directly addresses the failure class where a scheduler boundary was observed but no completed worker run was recorded.

## Required truthfulness

The bootstrap scheduler can force creation of a **spawn ticket** from its own clock. It can force creation of an actual external model session only when an authorized host adapter exposes that capability. Without such an adapter, the scheduler remains useful for deterministic temporal governance, missed-trigger recovery, diagnosis, and admission, but it must report `HOST_SPAWN_ADAPTER_REQUIRED` rather than claiming a worker exists.
