# Project Context Binding Protocol

Status: **ACTIVE HARD GATE**  
Version: **1.2.0**  
Canonical bootstrap generation: **V26**

## Purpose

A worker launched inside a ChatGPT Project must inherit that project as a hard launch boundary **after V26 standalone readiness and before task interpretation**. Project placement is not a hint and must not be reconstructed from recent chats, task topic, repository recency, or another project's handoff.

Canonical machine policy: `governance/PROJECT_CONTEXT_BINDING_POLICY.json`  
Canonical binding registry: `governance/PROJECT_CONTEXT_BINDING_REGISTRY.json`  
Reference runtime: `org_agent_mesh.project_context_binding`

## Mandatory V26 pre-bind boundary

Before project binding:

1. load `PROJECT_MANIFEST_V26.json` and `bootstrap/V26_BOOTSTRAP_ADAPTER.json`;
2. enter `UNBOUND_READ_ONLY`;
3. initialize/validate the inherited embedded VMBUS and require `VMBUS_READY`;
4. load R10 corrected principal context, R11 model synthesis as revisable non-authoritative hypotheses, and V26 direct chronology as distinct epistemic layers;
5. build the epistemic/privacy/chronology/synthesis indexes and require `PRINCIPAL_CONTEXT_READY`.

Only after both readiness barriers may a project be bound. Principal context does not authenticate a person and does not grant authority, consent, or mutation permission.

## Project-bound startup order

When host project context is available after the V26 readiness barrier:

1. resolve the exact host ChatGPT Project to one registered `project_id`;
2. bind repository, internal AgentBus namespace, artifact namespace, and a distinct project-scoped VMBUS namespace from the binding registry/local contract;
3. load the project's local `AGENT_BOOTSTRAP.json`;
4. load the project's local `AGENT_CONTEXT_REFERENCE.md`;
5. validate the project identity lock when present;
6. load the current master handoff, work-control state, and authoritative internal coordination route;
7. only after those checks pass, interpret the task and enter role admission.

The required acknowledgement is:

`PROJECT CONTEXT BOUND: generation=V26; vmbus_ready=true; principal_context_ready=true; project=<project_id>; chat_project=<host project>; repository=<repository>; forum=<internal namespace>; task_interpretation_allowed=true; mutation_authority=false`

## Child/worker launch envelope

Parents, dispatchers, and scalers that create project-bound workers SHOULD render the canonical machine block with `render_project_launch_context(...)` and include it in the worker instruction. A child revalidates the project binding after V26 readiness. A changed repository, forum, project, artifact namespace, or context path invalidates the registry comparison and fails closed. The fingerprint is an integrity checksum, not mutation authorization.

## Precedence

For a project-bound worker, the verified host project context or verified launch envelope wins over task-topic similarity, conversation history, recently accessed repositories, stale handoffs, and neighboring project state **after V26 standalone readiness**. Those sources may provide read-only evidence but may not silently rebind the worker.

An explicit structured project switch that conflicts with the host project is not executed in place. Fail closed on project-specific work and perform a deliberate rebind/new launch.

`RETRIEVAL_RANK != CANONICAL_PRECEDENCE`. V25 R11 or earlier lineage must not become current merely because it was retrieved first. For Intercommunication Enhancements, V26 is the active canonical bootstrap generation.

## Role admission

Project binding does not imply PRIMARY. A generic human-launched worker with no explicit authorized role enters roleless demand-driven admission. PRIMARY is never the default merely because the worker is project-bound.

## Coordination and GitHub

For Intercommunication Enhancements the live coordination surface is the internal ChatGPT Library AgentBus at `/Intercommunication enhancements/AgentBus/messages` when available. GitHub is canonical versioned source/governance plus durable backup/corroboration. Historical machine labels `INTERNAL_ARTIFACTORY` and `ARTIFACTORY` are compatibility aliases for AgentBus and do not mean JFrog.

A GitHub write does not prove an AgentBus write. A difference between whole stores is not itself a record conflict. Corresponding records reconcile by logical record ID plus payload SHA-256.

## Project separation

The common Intercommunication Enhancements interface must not collapse project boundaries. Shared protocol does not imply shared state or authority; each project retains its own identity, policy, evidence, authorization and VMBUS namespace. **CV Support is explicitly non-federated.**

## Failure behavior

If V26 readiness, host project resolution, repository identity, launch-envelope integrity, local bootstrap, context reference, identity lock, handoff, or coordination route is missing or conflicting, do not interpret the affected project task as executable work and do not mutate. Preserve the blocker and continue only safe diagnostic or unrelated read-only work.
