# Scheduled Agent Launch and Provider Admission Protocol v1

## Purpose

This protocol governs agent runs started by ChatGPT Scheduled Tasks, Work events, or another approved scheduler. It solves two different problems that must not be conflated:

1. **Project-context continuity** — a scheduled agent must start with the exact project identity, repository/forum/artifact namespace, role and bootstrap contract captured when the task was configured.
2. **Provider admission/backpressure** — scheduled starts must not create an uncontrolled thundering herd that is rejected by the model/provider before project bootstrap can run.

A scheduled launch is not authorized merely because its prompt names a project. The launch context is routing evidence. Normal local identity, role, capability, bootstrap and mutation gates remain authoritative.

## Project-bound context capture

When a dynamic scheduled task is created from within a project, capture a `ScheduledTaskRoute` from the project's current `AGENT_BOOTSTRAP.json`. The route carries at least:

- exact `project_id`;
- authorized `role_id`;
- routing-contract version;
- authoritative forum namespace;
- artifact namespace;
- repository full name and stable repository ID when bound;
- local contract path and bootstrap-order path;
- task identity and admission-policy identity.

The route must be generated from the local contract rather than inferred from the conversation title, topic, recent chat, semantic similarity, current working directory, or a different project's state.

`ScheduledTaskRoute.render_scheduler_prompt(...)` produces a machine-readable `ORG_AGENT_MESH_PROJECT_LAUNCH_CONTEXT` block. That block is intended to be embedded in the scheduled task instruction so the future run receives the project context even when ordinary conversation context is absent.

Each dynamic occurrence should carry a stable `occurrence_id` when the scheduler can provide one. Retries of the same occurrence keep the same occurrence/task identity and idempotency semantics.

## Startup verification

A scheduled project-bound run follows:

`SCHEDULE TRIGGER -> ADMISSION -> PROVIDER ACCEPTED -> PARSE LAUNCH CONTEXT -> VERIFY LOCAL CONTRACT -> IDENTITY LOCK -> ROLE/BINDING -> READY BARRIER -> WORK`

Before mutation, the agent must compare the launch context against the target project's local contract. Verify project ID, routing-contract version, forum namespace, artifact namespace, repository identity/ID when present, and role authorization.

If the context is missing, ambiguous, malformed, or conflicts with the local contract:

- do not guess another project;
- do not silently fall back to topic similarity;
- do not mutate any candidate project;
- report `LAUNCH_CONTEXT_MISMATCH` or the more specific identity error;
- leave the logical task unadvanced.

Interactive human launches may continue to use current human project intent. Generic unbound launches continue to use the universal routing protocol. Scheduled project-bound launches use the captured launch context as the initial project-intent evidence and still pass all ordinary local gates.

## Provider admission and backpressure

A provider can reject a run before agent code executes. Therefore model-side leases, manager backpressure and bootstrap logic alone cannot prevent launch overload.

The conformant architecture has a pre-provider admission layer owned by the scheduler/dispatcher or another external component. The reference implementation is `org_agent_mesh.launch_admission`.

Default policy goals:

- limit concurrent starts;
- enforce minimum spacing between starts;
- deterministically stagger recurring jobs to avoid synchronized wake-ups;
- use bounded exponential backoff with deterministic jitter after retryable provider failures;
- preserve the same logical occurrence/idempotency identity across retries;
- cap attempts and surface terminal failure rather than retry forever.

`TOO_MANY_REQUESTS`, `RATE_LIMITED`, temporary provider unavailability, and timeout before bootstrap are retryable launch failures. They are **not task execution failures**.

When the hosting scheduler does not expose a programmable admission hook before model invocation, apply the same policy at configuration/orchestration time: stagger schedules, avoid identical wake-up times, prefer a bounded dispatcher pattern, and retain a reconciliation path for missed/rejected occurrences. Agent code cannot retrospectively prevent a provider rejection that happened before the agent started.

## Launch state machine

Reference launch state:

`PENDING -> ADMITTED -> PROVIDER_ACCEPTED -> BOOTSTRAP_READY -> COMPLETED`

Retry path:

`ADMITTED -> RETRY_WAIT -> ADMITTED`

Terminal path:

`PENDING/ADMITTED -> TERMINAL_FAILURE`

The project task registry must not advance the task's execution state merely because a scheduler fired. Advancement is permitted only after `BOOTSTRAP_READY`. This prevents a rejected provider call from being mistaken for completed or failed project work.

A retry after `TOO_MANY_REQUESTS` therefore leaves the project task logically pending.

## Deterministic staggering

`deterministic_launch_offset_seconds(project_id, task_id, window_seconds)` maps a project/task pair into a stable offset. Use it to spread recurring jobs across an admission window rather than launching every project at the same minute.

The offset is a load-distribution aid, not authorization and not a substitute for the runtime concurrency/backoff gate.

## Duplicate and late starts

Schedulers may retry after uncertain delivery. Every occurrence must therefore remain idempotent:

- repeated provider starts for one occurrence use the same logical occurrence ID;
- canonical writes retain normal idempotency/CAS guards;
- an occurrence already at `BOOTSTRAP_READY` or later must not begin a second independent mutation stream;
- stale or duplicate launches should become safe no-ops or explicit recovery/reconciliation work.

## Project switching

A scheduled project-bound launch may not switch projects because the task text later resembles another project. A project change requires a new route/context capture or an explicit return to the universal unbound routing flow.

## Observability and learning

Record, when observable:

- admission decision and wait reason;
- provider rejection category;
- attempt count and next eligible time;
- launch-context verification outcome;
- time to `BOOTSTRAP_READY`;
- duplicate occurrence detection;
- final completion/failure disposition.

Provider throttling and context-mismatch incidents are valid swarm-learning evidence. They do not automatically become doctrine; normal evidence/validation/promotion rules still apply.

## Required implementation truth

The repository contains a tested reference admission controller and project-bound launch-context serializer/validator. Full prevention of provider-side request rejection additionally requires the actual scheduler/host to enforce admission before invoking the model. Where ChatGPT's scheduler does not expose that hook, deterministic schedule staggering plus retry/reconciliation is the deployable mitigation; the repository must not claim it controls provider infrastructure that it cannot execute before model start.
