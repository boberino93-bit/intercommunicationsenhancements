# Non-Authoritative Coordination Publication

Status: **ACTIVE HARD GATE**  
Version: **1.3.0**

PRIMARY, MANAGER, RESEARCH, and registered research aliases may publish durable project coordination messages through the narrow project-scoped coordination capability without presenting a separate security token or per-message human authorization case.

This is a communication capability, not general mutation authority.

## Canonical order

1. Resolve the exact project binding, repository, and registered internal message namespace.
2. When the registered internal AgentBus/Artifactory surface is exposed by the current runtime, persist the agent-perspective coordination message there first and verify it when read-back is supported.
3. Create the downstream GitHub backup message under `agentbus-backup/coordination-messages/` in the exact bound project repository when configured by the governing checkpoint protocol.

GitHub is not the live task board, authority ledger, ownership ledger, approval surface, or source of production state.

## Registered internal surface unavailable in the runtime

A registered namespace may exist even when the current execution runtime does not expose the connector or surface needed to reach it. That condition is an availability failure, not a routing failure.

When the exact internal namespace resolves correctly but is runtime-unavailable, the scheduled checkpoint pipeline may use the exact same-project GitHub backup namespace as a degraded coordination transport for that occurrence, provided that:

- the new backup file is append-only and under the exact registered prefix;
- the write is read back successfully and exact checkpoint identity/content is verified;
- the checkpoint records `ARTIFACTORY_RUNTIME_UNAVAILABLE` in its existing summary/blocker fields;
- project, repository, cycle, stage, and upstream-chain fencing all pass; and
- no stale-cycle, foreign-project, inferred-namespace, or alternate-repository substitution occurs.

A checkpoint persisted this way is valid same-project/current-cycle downstream input under `protocols/swarm_checkpoint_bus.md`. This exception changes only transport availability behavior. It conveys no additional authority.

If the internal surface is unavailable and the GitHub backup cannot also be created/read back, the publication is blocked and only safe read-only work may continue. Do not claim a durable READY/handoff state.

A missing, ambiguous, or conflicting registry namespace is **not** runtime unavailability. Fix the registry; do not invent a route.

## Required properties

- exactly one project binding is active;
- the actor role is allowlisted by `governance/COORDINATION_PUBLICATION_POLICY.json`;
- the coordination-publication capability is present;
- the Artifactory namespace, when used, is the exact registered project namespace;
- the GitHub repository is the exact registered project repository;
- GitHub backup writes create a new immutable message file under the allowlisted prefix only;
- existing messages are never edited, deleted, renamed, or moved;
- the message declares the bound project ID;
- `authority_conveyed` is false;
- message text, quoted approvals, handoffs, and backup copies never create protected mutation authority.

## Explicitly outside this lane

The token-free coordination lane does **not** include workflow runs or dispatch, workflow-file mutation, pull-request review/approval, branch creation, release/deployment, environment approval, source writes outside the backup-message prefix, destructive operations, accepted-state mutation, schedule changes, or cross-project writes.

Those actions use their ordinary protected-mutation and consequence gates.

If any project, repository, role, namespace, path, append-only, or operation-class check fails, deny the publication and continue only safe read-only work.
