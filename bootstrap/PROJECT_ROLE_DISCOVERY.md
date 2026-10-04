# Project + Role Discovery Protocol

This protocol runs before any role-specific work or repository mutation.

## Inputs

- `project_id`: derived from the project environment or explicitly named by the human.
- `role_id`: explicitly assigned by the human or deployment package.

Both are required. Neither may be guessed from topic similarity.

## Resolution

1. Load `PROJECT_ROLE_ROUTING_REGISTRY.json`.
2. Resolve the exact `project_id` entry.
3. Verify `role_id` is authorized for that project.
4. Verify the current repository/project identity lock matches the resolved project.
5. Read the registered internal forum/message namespace before repository mutation.
6. Read the registered handoff/state locations before repository mutation.
7. Bind only the registered repository/repositories as authorized mutation targets.
8. Emit the startup acknowledgement:

   `IDENTITY RESOLVED: project=<project_id>; role=<role_id>; forum=<forum_namespace>; repositories=<authorized_repositories>; state=<handoff_or_state_ref>`

9. Only after the acknowledgement may role-specific startup continue.

## Fail-closed conditions

Stop before mutation if any of the following is true:

- project is unknown;
- role is unknown or unauthorized;
- project and repository identity disagree;
- forum namespace cannot be resolved;
- handoff/state source cannot be resolved;
- two projects appear equally plausible;
- a repository is requested that is not registered for the resolved project.

Do not rewrite, normalize, or guess identifiers to make them fit.

## Cross-project framework rollout

A framework rollout may update peer projects only when all of these are true:

- the human explicitly authorizes a cross-project rollout;
- each target exists in the routing registry;
- the change is framework/bootstrap-only, not domain logic;
- the target receives only project-local routing metadata;
- mutation is limited to the resolved target repository;
- each target is validated after deployment.

Ordinary project work remains cross-project deny-by-default.
