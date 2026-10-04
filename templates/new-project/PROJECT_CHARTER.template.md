# {{PROJECT_NAME}} — Project Charter

## Identity

- Project ID: `{{PROJECT_ID}}`
- Initial lifecycle state: `BOOTSTRAPPED_UNBOUND`
- Authoritative forum: `{{PROJECT_ID}}::messages`
- Artifact namespace: `{{PROJECT_ID}}::artifacts`
- Repository: not yet bound

## Purpose

{{PROJECT_PURPOSE}}

## Operating model

The project uses the organization agent-mesh architecture for identity resolution, role routing, handoffs, communication awareness, project isolation, and future repository binding.

The internal forum is authoritative from project inception. GitHub is a later storage/execution binding and is not required to define project identity.

## Roles

Core roles are `primary`, `manager`, `research`, `recovery`, `qa`, and `build`. A role may act only after the local bootstrap contract authorizes it.

## Boundaries

- Do not infer or borrow another project's repository identity.
- Do not write into another project's forum, artifacts, or repository unless an explicit cross-project contract allows it.
- Keep source-project examples separate from this project's facts and state.
- Persist meaningful decisions and handoffs to this project's own authoritative forum/state.

## Repository binding milestone

When a GitHub repository is explicitly connected, verify it, update all local identity contracts, establish mirror/backup paths, then register the project in the central routing registry.
