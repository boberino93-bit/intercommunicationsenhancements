# Scheduled Continuation Integrity Protocol v1

## Purpose

This protocol prevents a scheduled worker from ending a bounded assignment merely because one action, tool path, persistence path, protected mutation, or invocation boundary is encountered while useful safe in-scope work remains.

It does **not** grant mutation authority, bypass HOLD/PAUSE/STOP, permit PRIMARY or MASTER creation, expand project scope, create a second work unit, or weaken any human authorization requirement.

## Core invariant

A local blocker blocks the affected action or branch only.

Before a scheduled worker finalizes with `HUMAN_DECISION_REQUIRED`, `CAPABILITY_BLOCKED`, `CHECKPOINT_IO_BLOCKED`, `AUTHORIZATION_REQUIRED`, or another non-completion blocker, it MUST evaluate whether useful safe work remains inside the already selected project, role, and bounded work unit.

If safe work remains, the worker MUST continue that safe work until one of these conditions is true:

1. the bounded work unit reaches natural completion or a useful invocation-boundary checkpoint;
2. all remaining work genuinely depends on a non-delegable human decision or authorization;
3. authoritative HOLD/PAUSE/STOP/STOP_TREE state requires stopping;
4. a required external capability is unavailable and no safe fallback or preparatory work remains;
5. continuing would cross project, role, claim, lease, fence, confidentiality, safety, or mutation-authority boundaries; or
6. execution resources are exhausted after preserving the best available resumable handoff/checkpoint.

Routine uncertainty, a blocked write, a missing optional tool, unavailable preferred transport, an unanswered non-critical question, inability to perform one protected side effect, or the end of a single scheduler invocation is not by itself a valid reason to abandon the bounded work unit.

## Inter-occurrence continuation

Execution-resource or invocation limits may end one worker invocation without ending the underlying bounded work unit.

When useful safe work remains at an invocation boundary, the worker SHOULD publish the best permitted `WARM_HANDOFF_READY` or equivalent resumable checkpoint containing at least:

- project and role;
- bounded work-unit identity;
- claim/lease/fence state and expiry when applicable;
- exact completed work and evidence/provenance;
- unresolved work;
- blocked branches and authorization/capability requirements;
- `remaining_safe_work = true`;
- exact next safe action;
- revalidation requirements;
- supersession/stop conditions.

A later compatible scheduled worker MUST inspect unresolved valid continuation handoffs before selecting lower-priority fresh work. It SHOULD accept and resume the unfinished bounded work unit when all of the following hold:

1. the project remains active and admissible;
2. the handoff is current, valid, and not superseded;
3. role compatibility is satisfied;
4. required claim/lease/fence ownership can be validly acquired or continued under normal rules;
5. no higher-priority P0-P3 item legitimately preempts the continuation;
6. no HOLD/PAUSE/STOP, safety, confidentiality, project-isolation, or authorization boundary prohibits continuation.

Acceptance MUST be recorded as `WARM_HANDOFF_ACCEPTED` or equivalent before protected/exclusive continuation work when canonical handoff rules require it.

A scheduler occurrence must not create duplicate continuation work. If another live worker already owns the valid claim/lease for the work unit, the new occurrence must not compete for it and should route to other admissible work.

A continuation handoff transfers context and evidence only. It never transfers mutation authority, human authorization, identity authentication, or stale claims/leases/fences.

## Authorization-blocked mutation

When a desired mutation lacks valid authorization:

- refuse only that mutation;
- preserve the exact authorization case or action digest when one exists;
- continue read-only investigation, comparison, analysis, testing, validation, reconciliation, dependency inspection, contradiction resolution, evidence gathering, and preparation that is independently permitted;
- when useful, prepare a patch, diff, specification, test plan, migration plan, reviewed dossier, exact command/action plan, or other non-mutating deliverable so the authorized step can be executed without repeating prior work;
- do not represent prepared work as applied work;
- do not ask the human for authorization until the remaining safe preparatory work that materially improves the decision or execution has been completed.

A blocked mutation plus useful safe progress normally ends as `WORK_ADVANCED` with an explicit pending authorization/blocker, not as an immediate `HUMAN_DECISION_REQUIRED`.

`HUMAN_DECISION_REQUIRED` is appropriate only when the next material step genuinely requires a human choice and no useful safe in-scope work remains.

## Capability and transport degradation

If the preferred capability or transport is unavailable:

1. attempt only canonical permitted fallbacks;
2. continue safe read-only/local work that does not depend on the unavailable capability;
3. prepare durable or compact handoff material through any permitted channel;
4. classify the unavailable capability separately from project-work outcome.

`CAPABILITY_BLOCKED` or `CHECKPOINT_IO_BLOCKED` must not erase useful work already completed. If useful work advanced despite the degradation, record `WORK_ADVANCED` as the work disposition and retain the blocker as a secondary condition.

## Questions and ambiguity

A worker must not stop merely because a clarification could improve the result. If a safe reversible assumption can be made without changing authority, scope, project identity, or material user intent, record the assumption and continue. If one branch truly needs human input, block that branch and continue other safe portions of the same bounded work unit.

Do not invent missing authorization, identity, security facts, project bindings, or irreversible choices.

## Finalization proof

Before ending a scheduled worker invocation, record or internally establish the following compact finalization facts when observable:

- `bounded_work_unit`;
- `work_disposition`;
- `blocked_actions`;
- `safe_fallbacks_considered`;
- `safe_fallbacks_completed`;
- `remaining_safe_work`;
- `continuation_handoff_required`;
- `continuation_handoff_ref` when available;
- `remaining_human_gate`;
- `remaining_external_capability_gate`;
- `control_state`;
- `checkpoint_or_handoff_ref` when available.

A blocker-based terminal outcome requires `remaining_safe_work = false`.

If `remaining_safe_work = true`, finalization of the invocation is permitted only when an authoritative control state, safety boundary, lease/fence conflict, or resource/invocation exhaustion requires stop, and the best permitted resumable checkpoint/handoff has been preserved when practical. In that case the bounded work unit remains incomplete and eligible for successor recovery; it must not be falsely recorded as completed.

## Scope preservation

Continuation integrity never authorizes:

- switching to a second project merely to stay busy;
- claiming another bounded work unit after the selected unit is complete;
- extending a claim or lease without normal rules;
- bypassing mutation authorization;
- bypassing a project HOLD/PAUSE/STOP;
- creating or promoting PRIMARY/MASTER;
- starting a full swarm;
- enabling a disabled scheduled task without the applicable scheduler-state authorization.

The goal is completion of safe work already in scope, not expansion of scope.

## Required startup relationship

Every scheduled Researcher or Manager/Reviewer worker must load this protocol together with `protocols/autonomous_continuation.md` and `protocols/scheduled_agent_launch.md` before work selection or finalization decisions.

Before selecting fresh work, a scheduled worker must inspect valid unresolved continuation handoffs that are visible through canonical state and give resumable higher-priority unfinished work appropriate preference under the rules above.

The scheduled-task prompt, bootstrap service, and scheduler policy should all point to the same continuation-integrity contract so a future prompt rewrite cannot silently remove the requirement.
