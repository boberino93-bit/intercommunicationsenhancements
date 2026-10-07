# User Control-Message Protocol

Version: 1.1.0
Status: ACTIVE
Scope: UNIVERSAL / ALL PROJECTS / ALL PERSISTENT ROLES

## Purpose

Human messages can interrupt an agent's current execution without cancelling or replacing the active assignment. Agents must distinguish **control messages** from **task-changing messages** so the human can ask for status, explanation, evidence, or an immediate acknowledgement without destroying execution continuity.

## Core invariant

**A USER MESSAGE DOES NOT STOP AN ACTIVE ASSIGNMENT UNLESS THE USER EXPLICITLY SAYS NOT TO CONTINUE OR OTHERWISE CHANGES EXECUTION STATE.**

The canonical compatibility wording remains explicit:

**A USER CONTROL MESSAGE IS NOT A CANCELLATION.**

For a control message, **answer the control message immediately**, then **resume the interrupted work automatically** unless the message explicitly changes execution state. **A control-message response is not task completion.**

When a valid assignment is already active, the universal post-response default is:

> **ANSWER THE USER, THEN CONTINUE WHERE YOU LEFT OFF.**

The agent must not require a follow-up `continue` message. Silence, thanks, praise, criticism, a question, a screenshot, a reaction, or a request for explanation is not a stop condition.

The formal default is:

`USER_MESSAGE -> RESPOND -> APPLY_ANY_MATERIAL_DIRECTIVE -> RESUME_PRIOR_EXECUTION_CURSOR`

`NO_EXPLICIT_NONCONTINUATION_DIRECTIVE -> CONTINUE_WHERE_YOU_LEFT_OFF`

This applies to ordinary control messages, clarifications, corrections, commentary, status questions, evidence questions, brainstorming, and incidental side discussion. If a message materially corrects the work but does not explicitly stop it, incorporate the correction and resume from the nearest valid cursor under the corrected state.

If no valid active assignment exists, do not invent one. This protocol preserves continuation; it does not manufacture objectives or authority.

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
- `That's great.`
- `Why did that happen?`
- `Look at this screenshot.`
- `I think this part is wrong.`

Natural-language wording is not authoritative by itself. Classify by intent.

## Immediate-response contract

For a control message, respond before continuing tool or implementation work. Keep the response focused on what the user asked for and, when useful, include the relevant subset of:

1. current active objective;
2. approximate percentage complete when requested;
3. material work completed;
4. current blocker or uncertainty;
5. immediate next step;
6. whether the active assignment remains in progress.

A percentage is an estimate, not fabricated telemetry. Base it on the remaining known execution phases or explicitly label it approximate.

## Automatic resume contract

After satisfying the user message:

1. preserve the current project binding, role, task identity, execution instance, generation/run identifiers, claims, leases, branch, and durable handoff state unless normal expiry/recovery rules require otherwise;
2. restore the pre-interruption execution cursor from current chat state and durable project state;
3. apply any material correction or directive from the message;
4. continue the exact previously authorized work, or the nearest still-valid continuation of it, without asking for routine confirmation;
5. do not duplicate work already completed before the interruption;
6. checkpoint any material new directive contained in the interruption before resuming when the protocol requires durable state;
7. continue until convergence or a true human gate under `protocols/autonomous_continuation.md`.

## Explicit non-continuation / execution-changing messages

Do not automatically resume the old objective unchanged when the human explicitly:

- says `do not continue` or equivalent;
- says `stop`, `cancel`, `abort`, or equivalent;
- says to pause, wait, hold, or end the work;
- replaces the objective with a materially different task;
- changes project scope or target project;
- revokes authority or a previously granted action;
- changes a safety, security, data-integrity, or approval boundary;
- explicitly reprioritizes work such that the previous task is no longer current.

For a partial change, preserve unaffected work and reclassify only the affected branch.

A non-continuation directive must be explicit in intent. Agents must not infer cancellation from tone, brevity, topic drift, lack of the word `continue`, or the fact that the human asked a question.

## Compound interruptions

A single human message may contain both a control request and a new durable directive. In that case:

1. answer the control request immediately;
2. persist or incorporate the new directive at the correct authority surface;
3. reconcile it with the current active assignment;
4. resume the prior work with the new directive applied unless the directive explicitly cancels, pauses, holds, redirects, replaces it, or says not to continue.

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

A response to the user is not task completion. The agent returns to the interrupted assignment immediately after answering unless an explicit non-continuation/change condition above applies or a true human gate has been reached.
