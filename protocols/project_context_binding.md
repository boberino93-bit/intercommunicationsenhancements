# Project Context Binding Protocol

Status: **ACTIVE HARD GATE**  
Version: **1.1.0**

## Purpose

A worker launched inside a ChatGPT Project must inherit that project as a hard launch boundary before it interprets the task. Project placement is not a hint and must not be reconstructed from recent chats, task topic, repository recency, or another project's handoff.

Canonical machine policy: `governance/PROJECT_CONTEXT_BINDING_POLICY.json`  
Canonical binding registry: `governance/PROJECT_CONTEXT_BINDING_REGISTRY.json`  
Reference runtime: `org_agent_mesh.project_context_binding`

## Project-bound startup order

When host project context is available, execute this order before task interpretation:

1. resolve the exact host ChatGPT Project to one registered `project_id`;
2. bind repository, internal message-board namespace, artifact namespace, and local contract from the binding registry;
3. load the project's local `AGENT_BOOTSTRAP.json`;
4. load the project's local `AGENT_CONTEXT_REFERENCE.md`;
5. validate the project identity lock when present;
6. load the current master handoff and authoritative internal coordination route;
7. only after those checks pass, interpret the task and enter role admission.

The required acknowledgement is:

`PROJECT CONTEXT BOUND: project=<project_id>; chat_project=<host project>; repository=<repository>; forum=<internal namespace>; task_interpretation_allowed=true; mutation_authority=false`

## Child/worker launch envelope

Parents, dispatchers, and scalers that create project-bound workers SHOULD render the canonical machine block with `render_project_launch_context(...)` and include it in the worker instruction:

`ORG_AGENT_MESH_PROJECT_CONTEXT_BINDING`

`<canonical JSON + context_fingerprint>`

`END_ORG_AGENT_MESH_PROJECT_CONTEXT_BINDING`

The child parses that block with `parse_project_launch_context(...)` before task interpretation and revalidates it against the binding registry. A changed repository, forum, project, artifact namespace, or context path invalidates the fingerprint or registry comparison and fails closed. The fingerprint is an integrity checksum, not mutation authorization.

## Precedence

For a project-bound worker, the verified host project context or verified launch envelope wins over task-topic similarity, conversation history, recently accessed repositories, stale handoffs, and neighboring project state. Those sources may provide read-only evidence after binding but may not silently rebind the worker.

An explicit structured project switch that conflicts with the host project is not executed in place. Fail closed on project-specific work and perform a deliberate rebind/new launch.

## Role admission

Project binding does not imply PRIMARY. A generic human-launched worker with no explicit authorized role enters roleless demand-driven admission. PRIMARY is never the default merely because the worker is project-bound.

## Coordination and GitHub

Internal project AgentBus/Artifactory messaging is the canonical coordination surface. Routine project-bound append-only agent messages do not require a separate security token when they satisfy the coordination publication contract.

GitHub is downstream source/version control and backup. The token-free coordination backup lane is limited to append/create-new backup message files in the allowlisted project path. It never includes workflow execution or modification, approvals/reviews, releases, deployments, branch creation, destructive operations, or cross-project writes.

XRP uses `/XRPTHESIS-AgentBus/messages` as the canonical internal message namespace. `boberino93-bit/XRPTHESIS` is downstream source/backup, not the live coordination authority.

## Failure behavior

If host project resolution, repository identity, launch-envelope integrity, local bootstrap, context reference, identity lock, handoff, or coordination route is missing or conflicting, do not interpret the project task as executable work and do not mutate. Preserve the blocker and continue only safe diagnostic work.
