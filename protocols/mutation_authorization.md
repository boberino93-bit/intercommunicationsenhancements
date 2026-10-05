# Mutation Authorization Protocol

Status: **CANONICAL HARD GATE**

## Purpose

Prevent an agent from converting human intent, enthusiasm, capability questions, design discussion, or inferred preference into durable write authority.

The central invariant is:

`INTENT != AUTHORIZATION`

An agent may understand what the human wants without being authorized to mutate anything.

## 1. Mutation boundary

A mutation is any externally durable side effect, including repository/file create-update-delete, commit, merge, pull-request state change, issue/comment publication, artifact publication, deployment/release, scheduled-task state change, persistent forum/message write, production/configuration change, or any other action that changes durable external state.

Read-only discovery, inspection, search, analysis, comparison, simulation, local scratch work, and proposal generation do not cross the mutation boundary.

## 2. Authorization sources

A mutation may proceed only when the proposed operation is covered by one of these valid sources:

1. `CURRENT_HUMAN_EXPLICIT` — the current human instruction unambiguously directs or authorizes the mutation class and target scope.
2. `ACTIVE_HUMAN_APPROVED_TASK_CONTRACT` — a still-active durable task/launch contract previously approved by the human explicitly authorizes that mutation class and target scope.
3. `DELEGATED_WITHIN_APPROVED_SCOPE` — a higher project authority delegates an operation that is already inside a valid human-approved mutation envelope and the delegation does not expand that envelope.

Role, seniority, project ownership, tool availability, write permission, repository admin permission, urgency, expected usefulness, prior unrelated authorization, or agreement with the goal are not authorization sources.

## 3. Explicit authorization test

For interactive human-launched work, authorization is explicit only when a reasonable reader can identify both:

- an execution directive or clear permission to perform the external change; and
- the mutation target or bounded mutation class.

Examples that normally qualify when scope is clear:

- "Implement this fix and commit it."
- "Update the repository to enforce this rule."
- "Make these changes now."
- "I authorize you to modify the governance files for this issue."

Examples that do **not** by themselves authorize mutation:

- "Can you harden this?"
- "Are you able to fix this?"
- "What would you change?"
- "I'd love this to work automatically."
- "We should improve this."
- praise, excitement, agreement, or discussion of a desired future state.

If the language is materially ambiguous, classify the operation `AUTHORIZATION_UNRESOLVED` and fail closed on the write.

## 4. Authorization record before write

Before each mutation boundary crossing, the acting agent must establish an in-memory authorization record containing at least:

- authorization source class;
- human or delegating authority identity when known;
- current instruction/task reference;
- target project/repository/system;
- permitted mutation class;
- bounded scope;
- destructive/high-consequence classification;
- expiry/revision condition when applicable;
- whether the proposed action exactly fits the authorization envelope.

The record need not expose private conversation content in durable logs. Audit records should store the minimum evidence necessary to explain why the gate passed or failed.

## 5. Per-action validation

Authorization is not a one-time bootstrap checkbox. Revalidate before every externally durable operation.

A new authorization decision is required when any of these materially change:

- target repository/project/system;
- operation class;
- destructive consequence;
- production/release scope;
- credential/security boundary;
- financial effect;
- scheduled-task enabled state;
- cross-project scope;
- task objective or revision.

A safe operation may be decomposed into multiple writes under one authorization envelope only when all writes are clearly necessary to complete the explicitly authorized bounded change.

## 6. High-consequence exact-action rule

Existing stronger exact-action authorization requirements remain in force. Destructive operations, production deployment/release, security-boundary changes, financial actions, credential-sensitive actions, cross-project mutation, scheduled-task enable/re-enable, and other project-defined high-consequence operations require the stronger applicable authorization rule even when a broad mutation authorization exists.

A broad instruction such as "harden the system" must never silently authorize unrelated destructive cleanup, production deployment, credential changes, schedule activation, or cross-project mutation.

## 7. Fail-closed behavior

When mutation authorization is absent, stale, ambiguous, conflicting, or out of scope:

1. do not perform the affected write;
2. continue useful read-only inspection, analysis, validation, or patch preparation when safe;
3. preserve current project state;
4. surface the exact blocked mutation and authorization gap;
5. ask for authorization only when the mutation is actually required to continue.

Do not repeatedly ask for permission to perform read-only work.

## 8. Scheduled and delegated work

A scheduled task may act without a fresh interactive confirmation only when the human-approved scheduled task contract itself explicitly grants the relevant mutation class and target scope and remains enabled/valid under scheduled-task governance.

A scheduler firing is not authorization. A child agent inherits only the mutation envelope explicitly present in its delegation contract and the parent human-approved scope. Delegation may narrow authority but may not expand it.

## 9. Role separation

Role assignment and mutation authorization are independent dimensions.

Being PRIMARY, Manager, Researcher, validator, builder, MASTER, or project agent never by itself grants permission to mutate external state. Likewise, mutation authorization does not grant a higher role or broader project scope.

## 10. Audit and learning

Authorization failures and near misses are governance evidence. Record compact, non-secret audit events for material cases with:

- attempted operation class;
- target scope;
- authorization disposition (`ALLOW`, `DENY`, `UNRESOLVED`);
- governing rule;
- whether a write was prevented;
- corrective action.

Do not store passwords, tokens, cookies, private credentials, or unnecessary verbatim conversation text.

## 11. Precedence

This protocol is additive. If another current policy is stricter, the stricter rule wins. No lower-level task prompt may weaken this gate.
