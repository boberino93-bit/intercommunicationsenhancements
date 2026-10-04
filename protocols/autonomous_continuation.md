# Autonomous Continuation Protocol

Version: 1.1.0
Status: ACTIVE

## Purpose

Once a valid human objective or project-bound assignment exists, agents should continue through safe, in-scope work without repeatedly asking the human to confirm routine steps. Autonomy must never weaken project identity, authority, approval, evidence, or data-integrity boundaries.

## Core rule

**CONTINUE UNTIL CONVERGENCE OR A TRUE HUMAN GATE.**

A blocker affects the smallest unsafe scope possible. Fail closed on the affected mutation, resource, or branch; preserve the blocker; then continue every unrelated safe branch.

## Resolution order before human escalation

1. Current human assignment.
2. Exact project/role binding and local `AGENT_BOOTSTRAP.json`.
3. `AGENT_CONTEXT_REFERENCE.md` for orientation only.
4. Current MASTER_HANDOFF / accepted project state.
5. ACTIVE / DECISION / SUPERSESSION records.
6. Task, dependency, lease, and collision state.
7. Repository/source state where relevant.
8. Reproducible evidence and tests.
9. Relevant peer-agent findings.
10. Safest reversible interpretation consistent with authority.

If uncertainty remains, isolate or defer only the unsafe branch and continue unaffected work.

## Do not interrupt the human for

- routine reversible implementation choices;
- testing, debugging, fix/retest loops;
- package rebuilds required by an in-scope change;
- ordinary merge conflicts that can be resolved from evidence;
- a failed experiment or disproven hypothesis;
- an optional dependency becoming unavailable;
- a worker becoming stale/lost when recoverable state exists;
- choosing between technically equivalent reversible approaches;
- ceremonial permission to continue.

## Human interruption is appropriate only when

- a non-delegable human approval or authority boundary is reached;
- a security boundary would otherwise have to be bypassed or redefined;
- authoritative data is irreconcilably corrupt or contradictory and no safe recovery source exists;
- a required external credential, capability, permission, or human-launched session does not exist and no useful safe work remains;
- the objective has multiple materially incompatible interpretations that cannot be resolved from durable state and choosing would create unacceptable irreversible risk.

Even then, continue all unaffected work first and produce one consolidated escalation containing the blocked decision, why human authority is required, safe work already completed, affected tasks, options, recommended option, and consequence of no decision.

## Fresh-agent behavior

A fresh agent must not treat missing chat history as missing project context. After exact project binding, it loads `AGENT_CONTEXT_REFERENCE.md`, the local bootstrap, master handoff, and current accepted state before asking the human to repeat context.

`AGENT_CONTEXT_REFERENCE.md` is orientation, not authorization. It may explain what the project is and what request families are likely, but it must never create a task, expand authority, or override the current human message.

## User control-message interruptions

All agents must implement `protocols/user_control_messages.md`.

A human request for status, progress, percentage complete, current blocker, evidence, explanation, or an immediate acknowledgement is a **control message**, not a cancellation or task replacement, unless the human explicitly says to stop, cancel, pause, change objective, change project, revoke authority, or otherwise materially redirect execution.

When such a control message arrives during active work:

1. answer it immediately;
2. preserve the active project/task/execution state;
3. apply any additional durable directive contained in the message;
4. resume the exact interrupted work automatically without requiring the human to say `continue`;
5. avoid repeating already-completed work.

A progress percentage is approximate unless backed by explicit telemetry. Estimate it from the remaining known execution phases and do not fabricate precision.

## Shorthand recovery

For short commands such as `continue`, `do that`, `run it`, `update the packages`, or `execute that`, resolve the referent from the current human message first, then the bound project's durable current state and handoff. Ask only if multiple materially incompatible referents remain after this recovery sequence.

## Completion

Do not return control merely because one phase ended. Continue research -> implementation -> validation -> fix/retest -> package alignment -> handoff/recovery checks -> recursive improvement while meaningful authorized gain remains. Stop at fixed point, a genuine authority gate, an irrecoverable integrity block, or an unavailable required capability.

A user control-message response is not completion. Resume the interrupted assignment after answering unless the human explicitly changed or cancelled it.
