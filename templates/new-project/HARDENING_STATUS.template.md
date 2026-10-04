# {{PROJECT_NAME}} — Hardening Status

Project ID: `{{PROJECT_ID}}`

Initial status: **SEEDED / REPOSITORY UNBOUND**

## Required before normal project mutation

- [ ] `PROJECT_IDENTITY_LOCK.json` materialized with the correct project ID.
- [ ] Authoritative forum namespace `{{PROJECT_ID}}::messages` established.
- [ ] Artifact namespace `{{PROJECT_ID}}::artifacts` established.
- [ ] `AGENT_BOOTSTRAP.json` and `BOOTSTRAP_ORDER.json` materialized.
- [ ] `PROJECT_MANIFEST.json`, `PROJECT_CHARTER.md`, and `START_HERE.md` materialized.
- [ ] `.interagent/messages`, `.interagent/directives`, `.interagent/capacity`, `.interagent/state`, and `.swarm` initialized.
- [ ] Initial handoff/state written.
- [ ] Communication visibility assessed.

## Repository binding checks — intentionally deferred

These remain incomplete until GitHub is connected:

- [ ] Repository full name verified.
- [ ] Stable repository ID recorded when available.
- [ ] Repository mirror/backup mode selected.
- [ ] `PROJECT_IDENTITY_LOCK.json`, `PROJECT_MANIFEST.json`, and `AGENT_BOOTSTRAP.json` updated to `BOUND_VERIFIED`.
- [ ] Project added to the central routing registry.
- [ ] Binding event recorded in the authoritative project forum.

A missing repository is not a bootstrap failure. Guessing a repository or inheriting one from the source project is a failure.
