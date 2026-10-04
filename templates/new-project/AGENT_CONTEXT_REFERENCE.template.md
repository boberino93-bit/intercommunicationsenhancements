# {{PROJECT_NAME}} — Fresh Agent Context Reference

Version: 1.0.0
Status: ACTIVE ORIENTATION
Authority: ORIENTATION_ONLY
Project ID: `{{PROJECT_ID}}`

## Purpose

This file lets a newly launched agent understand this project when chat history is sparse or absent. It is not authorization to invent work, widen scope, switch projects, or mutate state.

## Project identity

- Project: `{{PROJECT_NAME}}`
- Project ID: `{{PROJECT_ID}}`
- Repository: initially UNBOUND until explicitly connected
- Canonical coordination authority: the project's internal Artifactory/AgentBus namespace

## Human operating expectation

Once the human gives a valid objective, continue through safe in-scope research, implementation, testing, debugging, package alignment, handoff, and recursive improvement without repeated routine confirmation. Recover known context from durable project state before asking the human to repeat it.

Fail closed only on the affected unsafe mutation or branch whenever possible. Preserve the blocker and continue unrelated safe work.

Escalate only for a genuine non-delegable human authority decision, an irrecoverable data-integrity problem, a security-boundary decision, or a required external capability that cannot be obtained and blocks all relevant progress.

## What this project is about

`{{PROJECT_PURPOSE}}`

## Likely request families

Populate this section during project creation with the principal categories of work the human is likely to request. Keep the description broad enough for orientation but specific enough that a contextless agent can understand project vocabulary and shorthand.

## Shorthand interpretation

- `this project` means the project identified above once exact binding is established.
- `continue` means recover the latest valid in-scope active task/handoff and proceed.
- `do that` or `execute that` means resolve the referent from the current human message first, then durable task/handoff state.
- `run the swarm` means use this project's accepted swarm/bootstrap contract; it is not permission to invent agents, roles, or cross-project authority.
- `update the packages` means assess and synchronize affected PRIMARY/MANAGER/RESEARCH packages within existing authority.

If multiple materially incompatible referents remain after current-message and durable-state recovery, block only the unsafe branch and ask the minimum necessary question.

## Fresh-agent startup

1. Verify exact project identity.
2. Load `AGENT_BOOTSTRAP.json`.
3. Load this reference as orientation only.
4. Load MASTER_HANDOFF and accepted Artifactory state.
5. Recover the current objective/task.
6. Verify role, write scope, approvals, dependencies, collisions, versions, and leases.
7. Execute autonomously within authority.
8. Persist material state.
9. Continue until convergence or a true human gate.

## Safety boundary

Likely intent is never authority. Never switch projects or write across project boundaries based only on semantic similarity.
