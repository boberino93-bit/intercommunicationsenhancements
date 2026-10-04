# IPG3 New Project Initializer

Status: **DESIGN DRAFT — NON-AUTHORITATIVE — NOT PACKAGED**

This integration defines the default bootstrap path for a completely new Organization Agent Mesh project.

Its purpose is to let a fresh Primary agent start from an idea/problem statement without manually constructing the internal coordination structure.

## Core rule

> The internal Artifactory/message-board project namespace is created first. GitHub is an external code-repository binding and MUST NOT be used as a substitute for the internal coordination plane.

If the executing environment cannot access the internal message-board backend, initialization fails closed.

A GitHub binding alone does **not** mean the project is initialized. The Primary must also persist its initial source-of-truth map, workstream decomposition and research/swarm assessment before initialization reaches `COMPLETE`.

---

## Default invocation

A fresh agent should be able to receive an instruction equivalent to:

```text
Initialize a new Organization Agent Mesh project.
Project name: <name>
Project idea/problem: <problem statement>
```

The machine-readable entrypoint is:

```text
design/NEW_PROJECT_ENTRYPOINT.json
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
- a stable audit record for namespace initialization;
- a stable Primary-forum bootstrap record.

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
- a stable binding audit record;
- a `PRIMARY_BOOTSTRAP_READY` Primary-forum record.

The initialization state becomes:

```text
BOUND
```

`BOUND` means:

- the isolated internal project namespace exists;
- the external GitHub repository has been verified;
- the Primary has a durable handoff describing what remains;
- normal project work MUST NOT yet be treated as fully initialized.

The external repository binding records canonical repository identity, URL and default branch where available.

A bound or completed project cannot be silently rebound to another repository. Rebinding requires a separately governed migration/change process.

---

## Phase 6 — mandatory Primary initialization

The Primary must now perform the initial project assessment and persist a structured `PrimaryBootstrapResult`.

Required outputs:

- source-of-truth references/hierarchy;
- initial workstream decomposition;
- whether additional research assistance is required;
- initial Research-agent count;
- initial Manager-agent count;
- rationale for the assistance/topology decision.

The Primary should use `design/ADAPTIVE_SWARM_REGULATION.md` when deciding whether additional intelligence capacity is warranted.

If assistance is not required, both Research and Manager counts must be zero.

If assistance is required, at least one Research agent must be allocated. Manager capacity is only justified where integration/coordination burden requires it.

The initializer persists at minimum:

- `bootstrap/primary-initialization.json`;
- `swarm/initial-assessment.json`;
- a stable initialization-complete audit record;
- a stable Primary-forum initialization-complete record.

Only then does initialization become:

```text
COMPLETE
```

The next action becomes:

```text
EXECUTE_PROJECT_WORK
```

---

## Interruption and recovery

The initializer is explicitly designed for interruptible agents and Primary succession.

Expected recovery behavior:

- `WAITING_FOR_GITHUB` -> prompt for the repository;
- `BOUND` / `PRIMARY_INITIALIZING` -> complete the structured Primary bootstrap assessment;
- `COMPLETE` -> begin/continue normal project work;
- conflicting or malformed state -> fail closed and require investigation.

A resume MUST NOT recreate forums, duplicate bootstrap records or mint a second project identity.

Stable initialization artifacts use **create-or-match** semantics: if a replacement agent sees a record that already exists, it must match the expected deterministic content or initialization fails closed.

This also supports recovery from an interruption after Primary bootstrap records were persisted but before the final state revision reached `COMPLETE`.

---

## Authority boundary

The integration automates project scaffolding and initialization, not arbitrary project authority.

Creating an internal namespace does not authorize arbitrary mutation of external repositories.

GitHub repository verification does not grant project capabilities.

Completing the Primary bootstrap does not bypass normal project/session/capability rules.

The Primary must still satisfy the framework's project/session/capability rules before protected effects.

---

## Runtime adapters

The reference implementation is:

```text
design/ipg3_project_initializer.py
```

It requires two injected adapters.

### `InternalBoardBackend`

Provides internal Artifactory/message-board directory and JSON-object operations.

The ChatGPT/product runtime or future connector supplies this adapter. The reference implementation MUST NOT redirect these writes to GitHub when the backend is unavailable.

### `GitHubRepositoryVerifier`

Uses the ChatGPT GitHub integration to verify repository existence, public visibility and connector accessibility.

Verification is an external fact-check. It does not make GitHub the inter-agent message store.

---

## End-user flow

The intended experience is:

```text
User: Start a new project to investigate <problem>.

Agent: <creates isolated internal project/message-board namespace and bootstrap state>
Agent: Please provide a public GitHub repository accessible through your connected GitHub integration.
User: <repository>
Agent: <verifies and binds repository; state becomes BOUND>
Agent: <performs source-of-truth discovery, decomposition and initial swarm assessment>
Agent: <persists Primary bootstrap result; state becomes COMPLETE>
Agent: <begins project execution and creates approved Research/Manager delegation if warranted>
```

The user should not need to know the internal directory layout, forum names, schema names or role-package structure.

---

## Promotion requirement

This integration remains under `design/` until:

1. initializer unit/adversarial tests pass;
2. the full end-to-end initialization field campaign passes;
3. interruption/recovery tests pass;
4. private and connector-inaccessible GitHub repositories fail closed;
5. G2 package/reproducibility gates remain green;
6. a real internal Artifactory/message-board adapter is available to the runtime;
7. a production GitHub verifier uses the connected ChatGPT GitHub integration rather than trusting user-provided metadata;
8. an independent review confirms there is no cross-project namespace or repository-binding bypass.
