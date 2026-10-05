# Scheduled Agent Launch and Provider Admission Protocol v1

## Purpose

This protocol governs agent runs started by ChatGPT Scheduled Tasks, Work events, or another approved scheduler. It solves three problems that must not be conflated:

1. **Project-context continuity** — a scheduled project agent must start with the exact project identity, repository/forum/artifact namespace, role and bootstrap contract captured when the task was configured.
2. **Provider admission/backpressure** — scheduled starts must not create an uncontrolled thundering herd that is rejected by the model/provider before project bootstrap can run.
3. **Supervisory lifecycle continuity** — a schedule firing must not revive deliberately paused/stopped work, bypass USER/MASTER/PRIMARY authority, or incorrectly bind the roaming MASTER to a project.

A scheduled launch is not authorized merely because its prompt names a project. The launch context is routing evidence. Normal local identity, role, capability, bootstrap, supervisory-state, and mutation gates remain authoritative.

Every scheduled swarm run must load `protocols/supervisory_governance.md` and `governance/SWARM_SUPERVISION_POLICY.json` in addition to the recurring/successor protocols required by its role.

## Project-bound context capture

When a dynamic scheduled task is created from within a project, capture a `ScheduledTaskRoute` from the project's current `AGENT_BOOTSTRAP.json`. The route carries at least:

- exact `project_id`;
- authorized `role_id`;
- routing-contract version;
- authoritative forum namespace;
- artifact namespace;
- repository full name and stable repository ID when bound;
- local contract path and bootstrap-order path;
- task identity and admission-policy identity;
- current assignment revision when available;
- intentional-stop/respawn disposition when available.

The route must be generated from the local contract rather than inferred from the conversation title, topic, recent chat, semantic similarity, current working directory, or a different project's state.

`ScheduledTaskRoute.render_scheduler_prompt(...)` produces a machine-readable `ORG_AGENT_MESH_PROJECT_LAUNCH_CONTEXT` block. That block is intended to be embedded in the scheduled task instruction so the future run receives the project context even when ordinary conversation context is absent.

Each dynamic occurrence should carry a stable `occurrence_id` when the scheduler can provide one. Retries of the same occurrence keep the same occurrence/task identity and idempotency semantics.

## MASTER exception: global roaming launch

The MASTER is not project-bound. A MASTER schedule must preserve:

- `project_id = null`;
- `roaming = true`;
- `chat_project = null`;
- global lifecycle-supervision scope;
- existing mutation/consequence boundaries.

A project event, highest-priority project, or project-specific work selected after startup must never cause the MASTER conversation itself to become project-bound. The MASTER may supervise project trees globally while remaining a global/Recents conversation.

## ChatGPT Project placement

For non-roaming project agents, use the canonical project mapping in `governance/SWARM_SUPERVISION_POLICY.json` through `org_agent_mesh.chat_project_routing.ChatProjectRouter` when the host exposes a supported API/UI adapter.

Placement rules:

1. prefer direct creation inside the expected ChatGPT Project;
2. otherwise use a bounded move fallback;
3. verify the detected project after the external effect;
4. fail closed on unknown project mappings rather than guessing;
5. do not claim successful placement from code-path completion alone;
6. absence of a host-side placement capability is a deployment limitation, not authority to fabricate success.

If the scheduler binds an immutable existing conversation and does not expose a conversation-move/project-assignment primitive, preserve the scheduled task but report project-placement status as externally unverified/unavailable. Do not change project identity or mutation scope to compensate.

## Startup verification

A scheduled project-bound run follows:

`SCHEDULE TRIGGER -> ADMISSION -> PROVIDER ACCEPTED -> PARSE LAUNCH CONTEXT -> VERIFY LOCAL CONTRACT -> LOAD SUPERVISORY STATE -> IDENTITY LOCK -> ROLE/BINDING -> PROJECT PLACEMENT VERIFY WHEN SUPPORTED -> READY BARRIER -> WORK`

A scheduled MASTER run follows:

`SCHEDULE TRIGGER -> ADMISSION -> PROVIDER ACCEPTED -> VERIFY ROAMING MASTER IDENTITY -> LOAD SUPERVISORY STATE -> READY BARRIER -> PORTFOLIO WORK`

Before mutation, the agent must compare the launch context against the target project's local contract. Verify project ID, routing-contract version, forum namespace, artifact namespace, repository identity/ID when present, and role authorization.

Before starting or replacing a logical execution, the agent or dispatcher must also reconcile intentional-stop state. If the prior execution has `allow_respawn = false`, the schedule firing is not restart authority. Restart requires explicit User authorization or a materially newer assignment revision from an authorized MASTER/PRIMARY according to the supervisory protocol.

If project context is missing, ambiguous, malformed, or conflicts with the local contract:

- do not guess another project;
- do not silently fall back to topic similarity;
- do not mutate any candidate project;
- report `LAUNCH_CONTEXT_MISMATCH` or the more specific identity error;
- leave the logical task unadvanced.

If supervisory state indicates intentional stop without valid restart authority:

- do not create a replacement execution;
- do not mark the stopped execution as provider failure or stale liveness;
- report `INTENTIONAL_STOP_NO_RESPAWN` in the launch audit state;
- leave the scheduled occurrence reconciled as a safe no-op unless a newer authorized assignment exists.

Interactive human launches may continue to use current human project intent. Generic unbound launches continue to use the universal routing protocol. Scheduled project-bound launches use the captured launch context as the initial project-intent evidence and still pass all ordinary local gates.

## Provider admission and backpressure

A provider can reject a run before agent code executes. Therefore model-side leases, manager backpressure, supervisory checks and bootstrap logic alone cannot prevent launch overload.

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

Intentional-stop reconciliation path:

`PENDING -> INTENTIONAL_STOP_NO_RESPAWN`

Terminal path:

`PENDING/ADMITTED -> TERMINAL_FAILURE`

The project task registry must not advance the task's execution state merely because a scheduler fired. Advancement is permitted only after `BOOTSTRAP_READY`. This prevents a rejected provider call from being mistaken for completed or failed project work.

A retry after `TOO_MANY_REQUESTS` therefore leaves the project task logically pending. An intentional stop remains intentionally stopped unless valid restart authority exists.

## Deterministic staggering

`deterministic_launch_offset_seconds(project_id, task_id, window_seconds)` maps a project/task pair into a stable offset. Use it to spread recurring jobs across an admission window rather than launching every project at the same minute.

The offset is a load-distribution aid, not authorization and not a substitute for the runtime concurrency/backoff gate.

## Duplicate and late starts

Schedulers may retry after uncertain delivery. Every occurrence must therefore remain idempotent:

- repeated provider starts for one occurrence use the same logical occurrence ID;
- canonical writes retain normal idempotency/CAS guards;
- an occurrence already at `BOOTSTRAP_READY` or later must not begin a second independent mutation stream;
- stale or duplicate launches should become safe no-ops or explicit recovery/reconciliation work;
- intentionally stopped executions must not be classified as stale merely because heartbeat/liveness ceased;
- a child of a stopped parent must not be spawned by a later timer.

## Supervisory control during execution

Scheduled agents must check authoritative control state between bounded work units. Valid `REDIRECT`, `PAUSE`, `STOP`, or `STOP_TREE` actions take precedence over continuing the old assignment. Useful partial state should be preserved before termination when practical.

PRIMARY/Manager control is limited to its own project tree. MASTER lifecycle supervision is global. User control remains highest authority. These lifecycle powers do not expand repository-write, destructive-action, credential, release, production, or other consequence authority.

## Project switching

A scheduled project-bound launch may not switch projects because the task text later resembles another project. A project change requires a new route/context capture or an explicit return to the universal unbound routing flow.

MASTER is the exception only in the sense that it starts unbound/global and may inspect/supervise multiple projects; it still does not inherit cross-project mutation authority merely from being MASTER.

## Observability and learning

Record, when observable:

- admission decision and wait reason;
- provider rejection category;
- attempt count and next eligible time;
- launch-context verification outcome;
- supervisory-state/intentional-stop reconciliation;
- assignment revision used for restart decisions;
- project-placement expected/detected result when supported;
- time to `BOOTSTRAP_READY`;
- duplicate occurrence detection;
- final completion/failure/intentional-stop disposition.

Provider throttling, context mismatch, unintended respawn attempts, or placement-verification failures are valid swarm-learning evidence. They do not automatically become doctrine; normal evidence/validation/promotion rules still apply.

## Required implementation truth

The repository contains a reference admission controller, project-bound launch-context serializer/validator, supervisory lifecycle implementation, respawn guard, and ChatGPT Project routing adapter contract. Full prevention of provider-side request rejection additionally requires the actual scheduler/host to enforce admission before invoking the model. Actual ChatGPT Project movement additionally requires a supported host-side API or UI adapter. Where the host does not expose those hooks, deterministic schedule staggering, retry/reconciliation, correct identity scoping, intentional-stop checks after provider admission, and explicit external-effect status are the deployable mitigations. The repository must not claim control over provider or UI infrastructure it cannot actually exercise.
