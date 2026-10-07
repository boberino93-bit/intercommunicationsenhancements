# Scheduled Continuation Integrity Protocol v1

## Purpose

This protocol prevents a scheduled worker from ending a bounded assignment merely because one action, tool path, persistence path, or protected mutation is blocked when useful safe in-scope work remains.

It does **not** grant mutation authority, bypass HOLD/PAUSE/STOP, permit PRIMARY or MASTER creation, expand project scope, create a second work unit, or weaken any human authorization requirement.

## Core invariant

A local blocker blocks the affected action or branch only.

Before a scheduled worker finalizes with `HUMAN_DECISION_REQUIRED`, `CAPABILITY_BLOCKED`, `CHECKPOINT_IO_BLOCKED`, `AUTHORIZATION_REQUIRED`, or another non-completion blocker, it MUST evaluate whether useful safe work remains inside the already selected project, role, and bounded work unit.

If safe work remains, the worker MUST continue that safe work until one of these conditions is true:

1. the bounded work unit reaches a natural completion or useful checkpoint;
2. all remaining work genuinely depends on a non-delegable human decision or authorization;
3. authoritative HOLD/PAUSE/STOP/STOP_TREE state requires stopping;
4. a required external capability is unavailable and no safe fallback or preparatory work remains;
5. continuing would cross project, role, claim, lease, fence, confidentiality, safety, or mutation-authority boundaries; or
6. execution resources are exhausted after preserving the best available handoff/checkpoint.

Routine uncertainty, a blocked write, a missing optional tool, unavailable preferred transport, an unanswered non-critical question, or inability to perform one protected side effect is not by itself a valid reason to terminate the entire bounded work unit.

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
- `remaining_human_gate`;
- `remaining_external_capability_gate`;
- `control_state`;
- `checkpoint_or_handoff_ref` when available.

A blocker-based terminal outcome requires `remaining_safe_work = false`.

If `remaining_safe_work = true`, finalization is premature unless an authoritative control state, safety boundary, lease/fence conflict, or resource exhaustion requires immediate stop.

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

The scheduled-task prompt, bootstrap service, and scheduler policy should all point to the same continuation-integrity contract so a future prompt rewrite cannot silently remove the requirement.
