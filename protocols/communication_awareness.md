# Communication Awareness and Visibility Assessment

Every agent must distinguish **where project communications are supposed to live** from **what this execution can actually see right now**. Repository folders, handoffs, conversation context and snapshots are evidence sources; none of them become the authoritative live forum merely because they are visible.

## When this assessment is mandatory

Run the assessment:

1. during bootstrap after project + role routing resolves and before the agent claims awareness of surrounding project activity;
2. whenever the human asks whether the agent can see, hear, observe, follow, or knows about communications happening around it;
3. after a recovered, replaced, hung, or newly spawned agent resumes work;
4. after a project/context switch or any forum-routing change;
5. before relying on communications that could materially change the next project action.

## Source hierarchy

For the resolved project, inspect sources in this order:

1. `PROJECT_IDENTITY_LOCK.json` and the current human project intent;
2. `PROJECT_ROLE_ROUTING_REGISTRY.json` and local `AGENT_BOOTSTRAP.json`;
3. direct runtime access to the registered `forum_locator.authority + forum_locator.namespace`;
4. the declared `forum_locator.repository_view`, if one exists;
5. registered handoff / accepted-state paths;
6. current conversation context.

The source hierarchy is about truthfulness, not write authority. Communications visibility never expands mutation scope.

## Visibility classes

An agent must classify its current visibility as exactly one of:

- `DIRECT` — direct access to the authoritative internal-artifactory forum for the resolved project has been verified. This is still **partial** unless the runtime can prove the entire registered project-forum scope is available without filtering.
- `LIVE_MIRROR` — no direct forum access is verified, but the registry-declared live repository mirror is visible. This is not the authoritative forum.
- `STALE_MIRROR` — a registry-declared live mirror is visible but its freshness check failed.
- `SNAPSHOT_ONLY` — only a registry-declared snapshot/backup is visible. It is historical evidence and must never be described as live awareness.
- `HANDOFF_ONLY` — accepted state or handoff material is visible, but no forum view has been observed.
- `NONE` — no registered project communication source has been observed.
- `CONFLICT` — a directly visible forum or namespace disagrees with the resolved project identity. This blocks mutation until identity is reconciled.

## Full-visibility rule

Default to `PARTIAL_UNLESS_PROVEN`.

An agent may claim full visibility only of the **registered project forum**, and only when all of the following are verified:

- direct access to `INTERNAL_ARTIFACTORY`;
- exact namespace match with the resolved project;
- runtime evidence that the entire registered project-forum scope is available without filtering.

Even then, do not generalize that claim to “all communications everywhere,” Slack, other projects, private chats, unregistered channels, or any system not explicitly included in the verified scope.

## Freshness assessment

For repository mirrors and snapshots, determine freshness from an explicit mirror/snapshot manifest, synchronization marker, timestamp, accepted-state pointer, or equivalent evidence when available. If freshness cannot be proven, report it as unverified. Never infer freshness from filename ordering alone when a stronger source exists.

## Required acknowledgement

After assessment, emit or internally persist a record equivalent to:

`COMMUNICATIONS ASSESSED: project=<project_id>; role=<role_id>; forum=<forum_namespace>; access=<DIRECT|LIVE_MIRROR|STALE_MIRROR|SNAPSHOT_ONLY|HANDOFF_ONLY|NONE|CONFLICT>; coverage=<coverage>; confidence=<HIGH|MEDIUM|LOW>; full_forum_visibility=<true|false>; mutation_blocked=<true|false>`

When answering a human visibility question, explain in plain language:

- the project and forum you resolved;
- what you can actually access now;
- whether that access is direct, mirrored, snapshot-only, handoff-only, or absent;
- what you cannot verify;
- whether any conflict blocks safe mutation.

## Fail-closed conditions

Mutation must stop if direct forum identity conflicts with the resolved project/namespace, or if project identity itself is unresolved. A missing live forum does not authorize guessing another project’s message board. Snapshot and handoff visibility may support recovery and historical reasoning but must remain explicitly labeled as such.
