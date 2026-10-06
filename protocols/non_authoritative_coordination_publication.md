# Non-Authoritative Coordination Publication

Status: **ACTIVE HARD GATE**  
Version: **1.2.0**

PRIMARY, MANAGER, RESEARCH, and registered research aliases may publish durable project coordination messages through the narrow project-scoped coordination capability without presenting a separate security token or per-message human authorization case.

This is a communication capability, not general mutation authority.

## Canonical order

1. Persist the agent-perspective coordination message to the project's registered internal AgentBus/Artifactory message namespace.
2. Verify the internal record when the surface supports read-back.
3. Optionally create a downstream GitHub backup message file under `agentbus-backup/coordination-messages/` in the exact bound project repository.

GitHub is not the live task board, authority ledger, ownership ledger, approval surface, or source of current agent state.

## Required properties

- exactly one project binding is active;
- the actor role is allowlisted by `governance/COORDINATION_PUBLICATION_POLICY.json`;
- the coordination-publication capability is present;
- the Artifactory namespace is the exact registered project namespace;
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

XRP uses `/XRPTHESIS-AgentBus/messages` as its canonical internal message namespace. Its GitHub repository is downstream source/backup.
