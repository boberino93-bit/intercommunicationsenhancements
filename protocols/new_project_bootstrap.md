# New Project Bootstrap Protocol

## Purpose

This protocol lets an agent launched from any participating project create a new project that uses the same inter-agent communication, identity, handoff, scheduler, operational-glance, and repository-routing architecture without requiring a GitHub repository at project inception.

The source project is a reference only. Its project ID, forum namespace, artifact namespace, repository identity, handoff state, operational status, and project-specific content must never be copied into the new project.

## Entry condition

Enter this protocol only after an explicit human request to create, start, seed, or bootstrap a new project. Topic similarity, a guessed repository, or an unrecognized task is not enough.

A new-project request is not an unknown-project routing failure. It enters `UNBOUND_PROJECT` seed mode instead of selecting an existing registered project.

## Phase 1 — Seed identity before repository binding

1. Choose the new `project_id` from an explicit human-provided project name or identifier. If the request clearly creates a new project but gives no final name, create a provisional slug and mark it pending rather than binding it to an existing project.
2. Create `PROJECT_IDENTITY_LOCK.json` with repository binding state `UNBOUND` and repository `full_name`/`id` set to `null`.
3. Establish authoritative internal namespaces:
   - forum: `<project_id>::messages`
   - artifacts: `<project_id>::artifacts`
4. Create the required `.interagent` and `.swarm` directory skeleton.

## Phase 2 — Materialize the portable bootstrap documents

Read `NEW_PROJECT_BOOTSTRAP.json` and materialize every required document from `templates/new-project/`, replacing template tokens with the new project's own values.

Required documents include:

- `AGENT_BOOTSTRAP.json`
- `AGENT_CONTEXT_REFERENCE.md`
- `PROJECT_IDENTITY_LOCK.json`
- `PROJECT_MANIFEST.json`
- `BOOTSTRAP_ORDER.json`
- `MASTER_HANDOFF.json`
- `START_HERE.md`
- `PROJECT_CHARTER.md`
- `HARDENING_STATUS.md`
- `NEW_PROJECT_BOOTSTRAP.json`
- `INTERNAL_SCHEDULER_SERVICE_BINDING.json`
- `bootstrap/INTERNAL_SCHEDULER_SERVICE.json`
- `PROJECT_GLANCE.json`

`NEW_PROJECT_BOOTSTRAP.json` is a local factory pointer for the newly seeded project itself. This makes bootstrap capability recursive: every project created by this architecture can later seed another isolated project without inheriting the parent project's identity.

`PROJECT_GLANCE.json` is the project's local stale-aware operational summary. It begins `UNKNOWN` and repository `UNBOUND`; it is observability only, not authority. Update it on material transitions, not heartbeat noise. Unknown must never be treated as idle, and repository activity alone must never be treated as proof of live agent execution.

Treat these as the minimum portable architecture. Project-specific files may be added after identity is locked.

## Phase 3 — Operate while GitHub is absent

A seeded project may proceed with chartering, research, planning, internal forum messages, artifacts, handoffs, scheduler metadata, and role assignment before a repository exists.

While repository binding is `UNBOUND`:

- do not invent a GitHub repository;
- do not copy the source project's repository ID;
- do not mutate an unrelated existing repository on behalf of the new project;
- keep repository mirror paths disabled (`NONE`);
- keep the authoritative forum and artifact namespaces independent of GitHub;
- keep the local `NEW_PROJECT_BOOTSTRAP.json` source-project repository field unbound;
- keep `PROJECT_GLANCE.json` repository identity `UNBOUND` until verified binding;
- use the local glance only as derived status, never as mutation or scheduling authority.

## Phase 4 — Bind GitHub later

When the user explicitly creates, supplies, or connects a repository:

1. Verify the repository full name and, when available, stable repository ID.
2. Change repository binding from `UNBOUND` to `BOUND_VERIFIED` in `PROJECT_IDENTITY_LOCK.json`.
3. Update repository blocks in `PROJECT_MANIFEST.json` and `AGENT_BOOTSTRAP.json`.
4. Update the local `NEW_PROJECT_BOOTSTRAP.json` pointer so its `source_project.repository` identifies the now-verified repository.
5. Update `INTERNAL_SCHEDULER_SERVICE_BINDING.json` and `bootstrap/INTERNAL_SCHEDULER_SERVICE.json` with the verified repository identity and appropriate scheduler activation state.
6. Update `PROJECT_GLANCE.json` with the verified repository identity and a fresh conservative status derived from current project-local state.
7. Establish repository mirror/backup paths appropriate to the project.
8. Add the project to `PROJECT_ROLE_ROUTING_REGISTRY.json` only after the repository identity is verified.
9. Register it with scheduler/operations registries only after exact identity verification.
10. Record the binding event in the new project's authoritative forum.

## Discovery from any participating project

Every participating project must expose `NEW_PROJECT_BOOTSTRAP.json` or a local pointer with the same filename. Its local `AGENT_BOOTSTRAP.json` should reference that file through `project_factory.pointer` and include it in handoff/discovery paths.

A newly launched agent that receives an explicit new-project request should therefore:

1. resolve the current project normally;
2. read its `NEW_PROJECT_BOOTSTRAP.json` pointer;
3. load this canonical protocol and template set;
4. enter new-project seed mode without changing the current project's identity;
5. create the new project's isolated namespaces and bootstrap documents, including its own local project-factory pointer, scheduler binding, and project glance.

## Safety invariants

- Existing-project routing remains fail-closed.
- Cross-project writes remain denied by default.
- New-project seed mode is human-triggered, not inferred.
- Repository identity is nullable until binding and must never be guessed.
- Internal forum identity exists before repository identity.
- A source project can provide architecture, never identity or operational status.
- Every newly seeded project carries forward bootstrap discovery without copying its parent project's identity.
- Project-glance state is derived observability only; it never grants role, scheduling, claim, lease, fencing, or mutation authority.
- Unknown is not idle; stale is not current.
