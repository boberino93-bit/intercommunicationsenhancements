# Project + Role Discovery Protocol

This protocol runs after the project identity lock and before any role-specific work or repository mutation.

## Inputs

- `project_id`: derived from the project environment or explicitly named by the human.
- `role_id`: explicitly assigned by the human or deployment package.
- current repository full name and, when available, the provider's stable repository ID.

All identity inputs are evidence, not authority by themselves. Neither project nor repository may be guessed from topic similarity.

## Resolution

1. Validate `PROJECT_IDENTITY_LOCK.json` first.
2. Load and validate `PROJECT_ROLE_ROUTING_REGISTRY.json` in `FAIL_CLOSED` mode.
3. Resolve the exact `project_id` entry and verify `role_id` is authorized.
4. Verify the current repository full name matches the registered repository.
5. When a stable repository ID is available, verify it matches the registered `repository_id` as an additional anti-spoof/rename check.
6. If the target repository contains the registered local contract (normally `AGENT_BOOTSTRAP.json`), verify its project ID, repository identity, forum locator, handoff paths and routing-contract version agree with the registry. A disagreement fails closed.
7. Resolve the authoritative internal-artifactory forum from `forum_locator.authority` + `forum_locator.namespace`.
8. Treat `forum_locator.repository_view` only as a declared mirror/backup. `LIVE_MIRROR` may be consulted as a local view; `SNAPSHOT_BACKUP` is recovery/history evidence and must not be mistaken for current forum state; `NONE` means no repository forum view is registered.
9. Read the registered repository-side handoff/state locations separately from the forum locator.
10. Bind only the registered repository/repositories as authorized mutation targets.
11. Emit the startup acknowledgement:

   `IDENTITY RESOLVED: project=<project_id>; role=<role_id>; forum=<forum_namespace>; repositories=<authorized_repositories>; state=<handoff_or_state_ref>`

12. Only after the acknowledgement may role-specific startup continue.

## Registry integrity checks

The registry itself is invalid if it contains duplicate repository bindings, duplicate stable repository IDs, duplicate forum or artifact namespaces, unsafe relative paths, malformed role sets, invalid forum authority, a forum namespace mismatch, or an invalid repository-view mode/path pair. Invalid registry state must stop startup before mutation.

## Fail-closed conditions

Stop before mutation if any of the following is true:

- project is unknown;
- role is unknown or unauthorized;
- project and repository identity disagree;
- stable repository ID disagrees when available;
- central registry and local bootstrap contract disagree;
- forum authority or namespace cannot be resolved;
- a repository snapshot is presented as though it were the live forum;
- handoff/state source cannot be resolved;
- two projects appear equally plausible;
- a repository is requested that is not registered for the resolved project.

Do not rewrite, normalize, or guess identifiers to make them fit. Do not invent a repository forum path when the forum is external to GitHub.

## Cross-project framework rollout

A framework rollout may update peer projects only when all of these are true:

- the human explicitly authorizes a cross-project rollout;
- each target exists in the routing registry;
- the change is framework/bootstrap-only, not domain logic;
- the target receives only project-local routing metadata;
- mutation is limited to the resolved target repository;
- each target is validated after deployment.

Ordinary project work remains cross-project deny-by-default.
