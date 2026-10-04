# User Control-Message Protocol

Version: 1.0.0
Status: ACTIVE
Scope: UNIVERSAL / ALL PROJECTS / ALL PERSISTENT ROLES

## Purpose

Human messages can interrupt an agent's current execution without cancelling or replacing the active assignment. Agents must distinguish **control messages** from **task-changing messages** so the human can ask for status, explanation, evidence, or an immediate acknowledgement without destroying execution continuity.

## Core invariant

**A USER CONTROL MESSAGE IS NOT A CANCELLATION.**

When a valid assignment is already active, a human message that asks for current status, progress, percentage complete, what the agent is doing, why it is doing it, the current blocker, evidence, or an immediate acknowledgement temporarily interrupts output priority only. It does not release the task, abandon the execution lane, discard leases, reset project binding, or require the human to say `continue` afterward.

The agent must answer the control message immediately and then resume the interrupted work automatically from the exact prior execution state.

## Control-message examples

Treat messages with these intents as control messages unless they also explicitly change the objective:

- `Where are you?`
- `How far are you?`
- `What percentage complete are you?`
- `Tell me what you are doing right now.`
- `Respond immediately and then continue.`
- `What is blocking you?`
- `Why did you make that choice?`
- `Show me the evidence so far.`
- `Give me a status update.`
- `Don't stop; just answer this first.`

Natural-language wording is not authoritative by itself. Classify by intent.

## Immediate-response contract

For a status/progress control message, respond before continuing tool or implementation work. Keep the response concise and include the requested subset of:

1. current active objective;
2. approximate percentage complete when requested;
3. material work completed;
4. current blocker or uncertainty;
5. immediate next step;
6. whether the active assignment remains in progress.

A percentage is an estimate, not fabricated telemetry. Base it on the remaining known execution phases or explicitly label it approximate.

## Automatic resume contract

After satisfying the control message:

1. preserve the current project binding, role, task identity, execution instance, generation/run identifiers, claims, leases, branch, and durable handoff state unless normal expiry/recovery rules require otherwise;
2. restore the pre-interruption execution cursor from current chat state and durable project state;
3. continue the exact previously authorized work without asking for routine confirmation;
4. do not duplicate work already completed before the interruption;
5. checkpoint any material new directive contained in the interruption before resuming;
6. continue until convergence or a true human gate under `protocols/autonomous_continuation.md`.

## Messages that DO change execution

Do not automatically resume the old objective unchanged when the human explicitly:

- says `stop`, `cancel`, `abort`, or equivalent;
- says to pause and wait;
- replaces the objective with a materially different task;
- changes project scope or target project;
- revokes authority or a previously granted action;
- changes a safety, security, data-integrity, or approval boundary;
- explicitly reprioritizes work such that the previous task is no longer current.

For a partial change, preserve unaffected work and reclassify only the affected branch.

## Compound interruptions

A single human message may contain both a control request and a new durable directive. In that case:

1. answer the control request immediately;
2. persist or incorporate the new directive at the correct authority surface;
3. reconcile it with the current active assignment;
4. resume the prior work with the new directive applied unless the directive explicitly cancels or replaces it.

## Cross-project behavior

This protocol is universal interaction behavior, not cross-project mutation authority. It never authorizes an agent to write into another project, switch projects by semantic similarity, or bypass normal project binding. If the human explicitly switches projects, return to the universal routing gate before mutation.

## Scheduled and human-launched agents

The same semantics apply after a valid assignment is established, whether the agent was launched interactively or from an authorized project-bound scheduled occurrence. A status request does not create a new scheduled occurrence or advance task state by itself.

## Recovery after interruption

If the interruption or platform execution boundary causes local context loss, recover in this order:

1. current human message;
2. active project and role binding;
3. active task/claim/lease/generation/run state;
4. MASTER_HANDOFF and accepted project state;
5. relevant ACTIVE / DECISION / SUPERSESSION / checkpoint records;
6. repository branch and exact source revision;
7. last verified execution evidence.

Do not ask the human to repeat recoverable context.

## Completion

A control-message response is not task completion. The agent returns to the interrupted assignment immediately after answering unless an explicit stop/change condition above applies or a true human gate has been reached.
