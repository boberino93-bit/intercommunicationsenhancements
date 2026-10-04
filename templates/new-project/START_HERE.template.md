# {{PROJECT_NAME}} — Start Here

Project ID: `{{PROJECT_ID}}`

Repository binding: `UNBOUND`

## Agent startup

1. Read `PROJECT_IDENTITY_LOCK.json` first.
2. Read `AGENT_BOOTSTRAP.json` and follow `BOOTSTRAP_ORDER.json`.
3. Read the authoritative internal forum at `{{PROJECT_ID}}::messages` before mutation.
4. Read `PROJECT_MANIFEST.json`, `PROJECT_CHARTER.md`, `HARDENING_STATUS.md`, and the latest state/handoff.
5. State communication visibility accurately; a repository mirror is never the authoritative forum unless the local contract explicitly says otherwise.
6. Work only inside this project's scope and authorized role.

## Repository state

This project is intentionally valid before GitHub exists. Do not guess, invent, or inherit a repository identity. Until a repository is explicitly connected:

- repository full name: `null`
- repository ID: `null`
- repository mirror: `NONE`
- GitHub mutation: denied

When a repository is later connected, follow the binding lifecycle in `NEW_PROJECT_BOOTSTRAP.json` and update the local identity files before registering the project globally.

## Creating another project

This project carries the portable project-factory contract in `NEW_PROJECT_BOOTSTRAP.json`. An explicit human request to start another project may use that contract, but this project's identity values must not be copied into the new project.
