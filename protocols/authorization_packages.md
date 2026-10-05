# Predetermined Authorization Package Protocol

Version: 1.0.0  
Status: ACTIVE HARD GATE

## Purpose

Allow a human to approve a **predetermined bounded package** of related mutations in one authenticated decision without creating ambient session-wide authority.

This is an optimization layer over `protocols/mutation_authorization.md`, not an exception to it.

## Model

A package contains a fixed package ID, immutable package digest, expiry, authenticated principal, and an enumerated list of child authorization cases. Every child has an exact target, mutation class, bounded scope, consequence class, action digest, and consumption state.

Human approval binds the exact package ID + digest. After approval:

- no child may be added;
- no child target may change;
- no child consequence class may change;
- no child action digest may change;
- each child remains single-use;
- unused children authorize nothing outside their exact entries;
- package expiry invalidates all unused children.

A package is **not** session authorization, project-wide authority, or permission to perform any future action that seems related.

## High-consequence packages

If any child is high-consequence, independent external principal proof is required. One proof may cover multiple high-consequence children only when the proof itself binds the exact package ID and package digest. Otherwise each high-consequence child must obtain its own proof.

The package must not weaken production, root-governance, destructive-operation, schedule-enable, financial, credential, or security checks.

## Good package examples

- a migration that names every repository and every intended governance/bootstrap file change;
- a release package naming the exact artifact, target environment, deployment, verification, and rollback actions;
- a scheduler package naming the exact task IDs, prompt revisions, enablement transitions, timezone, and schedule values;
- a project-hold control package naming the exact project, HOLD event, registry projection update, and verification write.

## Invalid package examples

- `make whatever fixes are needed forever`;
- `all future commits in this project`;
- `anything the Primary believes is necessary`;
- a package whose target list or action list is filled in after approval;
- a consumed package reused for a later push.

## Execution

Before the first mutation, freeze the child list and package digest. Each mutation is matched to exactly one unconsumed child case. After verified completion, consume that child. If an action materially changes, deny that child and request a new package/case rather than silently widening scope.

Delegation may execute an exact child case but cannot expand the package or manufacture human approval.

## Interaction with scheduled agents

A scheduled occurrence may prepare a package for human approval. A schedule firing cannot approve it. A package may pre-authorize exact future scheduled-task configuration changes only when the human approved those exact task IDs and exact fields. It does not grant future scheduled occurrences mutation authority.

## Audit and privacy

Record package/case IDs, digests, target/action classes, authentication disposition, consumption, and verification references. Do not store secrets or unnecessary personal authentication data.
