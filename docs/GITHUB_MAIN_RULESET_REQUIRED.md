# Required GitHub `main` ruleset

## Status

`REQUIRED_EXTERNAL_REPOSITORY_CONFIGURATION`

The repository currently has no GitHub ruleset protecting `main`. The connected GitHub automation interface available to the swarm can read rulesets but cannot create or modify repository rulesets. This document is therefore an enforceable target specification, not a claim that the GitHub-side control has already been installed.

## Target

Apply to branch `main`.

## Required controls

1. Require changes to reach `main` through a pull request.
2. Require the following successful status checks before merge:
   - `Scheduler dispatch regression`;
   - `Root change authority guard`;
   - `Build and validate agent deployment packages`.
3. Require the branch to be up to date with `main` before merge when GitHub supports this without deadlocking repository workflows.
4. Block force pushes to `main`.
5. Block deletion of `main`.
6. Do not permit status-check bypass by scheduler workers, researchers, managers, recovery actors, or ordinary automation identities.
7. Any emergency administrative bypass must be attributable to a human repository administrator and must be documented in durable repository evidence.
8. Prefer signed/verified merge commits when supported by the repository/account configuration.

## Safety rationale

Repository policy and CI cannot protect themselves against a direct unguarded write to `main` if the hosting repository permits such writes. GitHub-native branch/ruleset enforcement must therefore be treated as an external control-plane boundary. CODEOWNERS alone is not equivalent to branch protection or required status checks.

## Verification

After the ruleset is installed, verification must read the live GitHub ruleset/branch-protection state and confirm each required control. The repository must not mark this item complete based only on this document or on CODEOWNERS presence.
