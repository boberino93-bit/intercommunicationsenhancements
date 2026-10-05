# Project Work Hold / Resume Protocol

Version: 1.0.0  
Status: ACTIVE CONTROL-PLANE CONTRACT  
Scope: ALL REGISTERED PROJECTS / ALL AGENTS / ALL SCHEDULED OCCURRENCES

## Purpose

Give an authenticated registered human principal a durable **stop-work order** that can freeze one project without cancelling, deleting, failing, or retiring it. A hold preserves the reason, timing, metadata, partial state, and eventual resume policy while allowing the wider swarm to continue useful work on other unheld projects.

Canonical current-state projection: `governance/PROJECT_WORK_CONTROL.json`  
Event schema: `schemas/project_work_control_event.schema.json`  
Append-only control transport: top-level comments on `boberino93-bit/intercommunicationsenhancements` issue #25 using the `PROJECT_WORK_CONTROL` prefix.

## Core invariant

**AUTHENTICATED HUMAN HOLD > SCHEDULE > MASTER > PRIMARY > SUBORDINATE.**

A valid active human project hold cannot be overridden by a timer, schedule occurrence, liveness recovery, MASTER, PRIMARY, Manager, Researcher, parent agent, child agent, claim, lease, task contract, or project priority calculation.

A HOLD is **not** cancellation, task completion, failure, stale liveness, deletion, archival, or abandonment.

## Issuing a hold

A hold event contains at minimum:

- unique `event_id` and stable `hold_order_id`;
- exact `project_id`;
- `action=HOLD`;
- authenticated registered principal claim and non-secret authentication reference;
- authorization case/package-child reference;
- issue/effective time;
- optional expiry time;
- resume policy: `MANUAL` or explicitly authorized `AUTO_AT_EXPIRY`;
- reason code;
- human-readable reason;
- optional structured metadata useful to future agents;
- `preserve_partial_state=true`.

Do not store credentials, passwords, government identifiers, dates of birth, family names, challenge secrets, or other unnecessary personal data in hold metadata.

A valid control-bus event becomes effective as soon as an agent validates it, even if the current-state registry projection has not yet been updated. The registry is the convenient canonical projection; the append-only event stream preserves chronology and auditability.

If a plausible hold signal is visible but cannot yet be authenticated/validated, fail closed on **new mutations in that project while verifying**. Do not let an unauthenticated signal authorize any other action.

## Required behavior when an active agent observes a hold

At bootstrap, before claiming new project work, after every authoritative forum/control-plane read, and between bounded work units:

1. load/reconcile `PROJECT_WORK_CONTROL.json` and newer valid `PROJECT_WORK_CONTROL` events;
2. if the bound project is held, stop beginning new work immediately;
3. allow only the smallest atomic/integrity-preserving step necessary to avoid corrupting already-started durable state;
4. checkpoint useful partial findings, exact execution cursor, leases/fences, evidence refs, blockers, and next safe action when practical;
5. mark the project execution as `PROJECT_HOLD_ACTIVE`, not failed/cancelled/stale;
6. release or fence mutable ownership as the local project protocol requires;
7. do not spawn replacements, recover 'stale' workers, perform new research, mutate source, publish production state, or continue the held objective;
8. a global/portfolio agent may immediately continue with a different unheld project.

The hold must survive agent restarts, conversation changes, scheduler occurrences, and missing local chat context because every fresh bootstrap re-reads the control plane.

## Scheduled tasks

A scheduled task is not itself disabled merely because one project is held unless the human explicitly disables that scheduler task.

Every scheduled occurrence must load this protocol and `PROJECT_WORK_CONTROL.json` before project selection and recheck hold state between bounded work units.

- A portfolio/general swarm task must exclude held projects from routing and continue on another unheld project when useful work exists.
- A project-specific scheduled occurrence whose only project is held must append/read back a compact hold checkpoint when possible and become a safe no-op for that occurrence.
- A held project must not be classified as unavailable due to provider failure, stale due to no heartbeat, or eligible for blind respawn.
- Hold expiry or resume never enables a scheduler task that is separately disabled. Scheduler activation remains human-only.

This dynamic bootstrap/control check is preferred over rewriting automation definitions for every hold because it applies immediately to all current and future scheduled agents and preserves scheduler configuration.

## Time-bounded holds

`MANUAL` is the default resume policy.

For `MANUAL`, expiry means `HOLD_EXPIRED_PENDING_HUMAN_RESUME`; the project remains logically held until an authenticated human RESUME event is validated.

`AUTO_AT_EXPIRY` is allowed only when the authenticated human explicitly selected it in the original or extended hold order. At the exact expiry, the logical project hold may lapse automatically. This does not grant mutation authority and does not enable any disabled scheduler task.

## Extend and resume

`EXTEND_HOLD` and `RESUME` must reference the stable `hold_order_id` and use a fresh authorization case/package child. A RESUME does not erase the hold history; it supersedes the active hold in the derived current-state projection.

A resume restores eligibility for future work. It does **not** resurrect consumed mutation authorization, old leases, stale claims, disabled scheduled tasks, or superseded task revisions.

## Metadata

Useful non-secret hold metadata may include:

- reason and context;
- expected review date;
- external dependency being awaited;
- risk/safety category;
- related issue/PR/evidence references;
- work packages that were active when held;
- explicit restart prerequisites;
- preferred resume policy.

Future agents must preserve this metadata in handoffs and should use it to avoid repeating work that the hold was intended to prevent.

## Precedence and local continuation

An active project hold is an explicit exception to the normal `continue from where you were` rule **for that project only**. The agent stops that held branch but continues unrelated safe work elsewhere when available.

This protocol does not weaken identity, authentication, authorization, repository, production, safety, or data-integrity boundaries. The stricter applicable rule wins.
