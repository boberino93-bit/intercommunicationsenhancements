# IPG3 New Project Initializer

Status: **DESIGN DRAFT — NON-AUTHORITATIVE — NOT PACKAGED**

This integration defines the default bootstrap path for a completely new Organization Agent Mesh project.

Its purpose is to let a fresh Primary agent start from an idea/problem statement without manually constructing the internal coordination structure.

## Core rule

> The internal Artifactory/message-board project namespace is created first. GitHub is an external code-repository binding and MUST NOT be used as a substitute for the internal coordination plane.

If the executing environment cannot access the internal message-board backend, initialization fails closed.

---

## Default invocation

A fresh agent should be able to receive an instruction equivalent to:

```text
Initialize a new Organization Agent Mesh project.
Project name: <name>
Project idea/problem: <problem statement>
```

The initializer then performs the following sequence without requiring the user to manually specify internal directories.

---

## Phase 1 — internal project reservation

The initializer derives a canonical new-project ID and creates a dedicated internal namespace under:

```text
projects/<project_id>/
```

Default project-scoped structure:

```text
projects/<project_id>/
  bootstrap/
  identity/
  forums/
    primary/
    managers/
    research/
  queues/
  handoffs/
  evidence/
  audit/
  swarm/
  artifacts/
```

The namespace is exclusive to that project.

A pre-existing namespace with no valid initialization record is considered ambiguous and MUST NOT be taken over automatically.

A repeated initialization request with the same project identity and same intent fingerprint resumes the existing initialization instead of creating duplicate state.

A conflicting intent using the same namespace fails closed.

---

## Phase 2 — bootstrap records

Before asking for GitHub, the initializer creates at minimum:

- `bootstrap/initialization.json`;
- `identity/project.json`;
- `forums/index.json`;
- `swarm/state.json`;
- an audit event recording namespace initialization;
- a Primary-forum bootstrap event.

The initialization state moves to:

```text
WAITING_FOR_GITHUB
```

At this point the internal message board is the durable source for resuming the bootstrap process.

---

## Phase 3 — user GitHub prompt

Only after the internal namespace is durable does the agent prompt the end user:

> Please provide the GitHub repository for this project. It must be publicly shared and accessible through the GitHub integration connected to ChatGPT.

The initializer does not create or infer a repository automatically.

The user may provide either an owner/repository identifier or a supported GitHub repository URL, depending on the connector implementation.

---

## Phase 4 — GitHub verification

The executing agent MUST verify through the ChatGPT GitHub integration that:

1. the repository resolves;
2. the repository is public;
3. the connected GitHub integration can access it.

A URL supplied by the user is not sufficient proof by itself.

If any condition fails, initialization remains `WAITING_FOR_GITHUB` and the internal project namespace remains intact for retry.

Private repositories are rejected by this initializer policy even if the connector can access them.

Repositories that are public but cannot be resolved through the connected GitHub integration are also rejected.

---

## Phase 5 — external repository binding

After successful verification the initializer writes:

- `identity/github-binding.json`;
- `handoffs/primary-bootstrap.json`;
- a binding audit event;
- a `PRIMARY_BOOTSTRAP_READY` forum event.

The initialization state becomes:

```text
COMPLETE
```

The external repository binding records canonical repository identity, URL and default branch where available.

A completed project cannot be silently rebound to another repository. Rebinding requires a separately governed migration/change process.

---

## Phase 6 — Primary execution

After binding, the Primary resumes normal Organization Agent Mesh bootstrap and authority validation.

Its first project work should include:

1. validate internal project identity and external repository binding;
2. establish source-of-truth hierarchy;
3. decompose the problem;
4. perform an initial local assessment;
5. evaluate whether research assistance is required;
6. use IPG3 Adaptive Research & Swarm Regulation when additional intelligence capacity is justified;
7. create explicit delegation contracts for any approved Research/Manager agents;
8. persist all coordination state under the internal project namespace.

The internal board remains canonical for inter-agent coordination; GitHub remains the bound code/document repository unless the project explicitly defines additional stores.

---

## Interruption and recovery

The initializer is designed for interruptible agents.

If execution stops after Phase 1 or 2, a replacement/fresh agent calls the resume operation against the existing `project_id`.

Expected behavior:

- `WAITING_FOR_GITHUB` -> prompt for the repository;
- `COMPLETE` -> continue Primary execution;
- conflicting or malformed state -> fail closed and require investigation.

A resume MUST NOT recreate forums, append duplicate bootstrap events or mint a second project identity.

---

## Authority boundary

The integration automates project scaffolding, not project authority.

Creating an internal namespace does not authorize arbitrary mutation of external repositories.

GitHub repository verification does not grant project capabilities.

The Primary must still satisfy the framework's project/session/capability rules before protected effects.

---

## Runtime adapters

The reference implementation is `design/ipg3_project_initializer.py`.

It requires two injected adapters:

### `InternalBoardBackend`

Provides internal Artifactory/message-board directory/object/event operations.

The ChatGPT/product runtime or future connector supplies this adapter. The reference implementation MUST NOT redirect these writes to GitHub when the backend is unavailable.

### `GitHubRepositoryVerifier`

Uses the ChatGPT GitHub integration to verify repository existence, public visibility and connector accessibility.

Verification is an external fact-check. It does not make GitHub the inter-agent message store.

---

## Future production integration

For production promotion, the ChatGPT/internal runtime should expose the `InternalBoardBackend` operations directly to the initializer so the entire flow can be triggered from a fresh conversation with one project idea.

The desired end-user experience is:

```text
User: Start a new project to investigate <problem>.

Agent: <creates isolated internal project/message-board namespace and bootstrap state>
Agent: Please provide a public GitHub repository accessible through your connected GitHub integration.
User: <repository>
Agent: <verifies/binds it, completes Primary bootstrap, decomposes problem and sizes initial research swarm if warranted>
```

The user should not need to know the internal directory layout, forum names, schema names or role-package structure.
