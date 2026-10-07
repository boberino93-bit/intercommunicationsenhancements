# Required GitHub `main` ruleset

## Status

`REQUIRED_EXTERNAL_REPOSITORY_CONFIGURATION`

The repository currently has no GitHub ruleset protecting `main`. The connected GitHub automation interface available to the swarm can read rulesets but cannot create or modify repository rulesets. This document is therefore an enforceable target specification, not a claim that the GitHub-side control has already been installed.

Runtime scheduler evidence is intentionally separated from canonical `main`. The dedicated branch `scheduler-evidence` is the only degraded GitHub destination for new scheduler mutation-journal evidence and mapped frontend execution receipts after the 2026-10-07 cutover. Runtime evidence authority on that branch does not grant any write or bypass authority on `main`.

## Target: `main`

Apply the primary repository ruleset to branch `main`.

## Required controls for `main`

1. Require changes to reach `main` through a pull request.
2. Require the following successful status checks before merge:
   - `Scheduler dispatch regression`;
   - `Root change authority guard`;
   - `Build and validate agent deployment packages`.
3. Require the branch to be up to date with `main` before merge when GitHub supports this without deadlocking repository workflows.
4. Block force pushes to `main`.
5. Block deletion of `main`.
6. Do not permit status-check bypass by scheduler workers, researchers, managers, recovery actors, ordinary automation identities, or the runtime scheduler-evidence writer.
7. Any emergency administrative bypass must be attributable to a human repository administrator and must be documented in durable repository evidence.
8. Prefer signed/verified merge commits when supported by the repository/account configuration.
9. Do not allow runtime execution receipts, scheduler mutation claims, scheduler mutation events, heartbeats, or other runtime evidence to be committed directly to `main` after the evidence-branch cutover.

## Separate target: `scheduler-evidence`

The `scheduler-evidence` branch is a runtime evidence surface, not a code/policy authority surface. It requires a separate restrictive control model:

1. Block force pushes.
2. Block branch deletion.
3. Permit only append/create-new-file runtime evidence at the declared evidence paths:
   - `governance/scheduler-mutation-journal-v3/claims/`;
   - `governance/scheduler-mutation-journal-v3/events/`;
   - `agentbus-backup/coordination-messages/` for scheduler execution receipts and permitted degraded coordination evidence.
4. Treat overwrites, deletes, history rewrites, policy/code edits, or writes outside authorized evidence paths as invalid even if GitHub branch controls cannot express path-level restrictions directly.
5. Evidence-branch write permission never conveys authority to merge, update, or bypass `main`.
6. The independent scheduler must fetch and validate this branch read-only before trusting its journal or receipts.
7. A missing/unavailable, forked, force-rewritten, or invalid evidence branch must fail closed for automatic scheduler mutation and must not be interpreted as healthy execution evidence.

If GitHub cannot express the desired append-only/path-restricted policy natively, preserve these restrictions in runtime credentials, application logic, immutable create-new-file semantics, CI validation, and audit. Do not weaken `main` merely to make runtime evidence persistence convenient.

## Safety rationale

Repository policy and CI cannot protect themselves against a direct unguarded write to `main` if the hosting repository permits such writes. GitHub-native branch/ruleset enforcement must therefore be treated as an external control-plane boundary. CODEOWNERS alone is not equivalent to branch protection or required status checks.

Separating runtime evidence from canonical code/policy removes the need to grant scheduler automation a broad `main` bypass. The evidence branch is not a second source of scheduler policy; canonical code, policy, mappings, grants, and protocol remain on `main`.

## Verification

After the rulesets are installed, verification must read the live GitHub ruleset/branch-protection state for both `main` and `scheduler-evidence` and confirm each applicable required control. The repository must not mark this item complete based only on this document, CODEOWNERS presence, or successful runtime evidence commits.
