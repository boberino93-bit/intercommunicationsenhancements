# Intercommunications Enhancements — Start Here

This repository hardens the Organization Agent Mesh for simultaneous unrelated projects.

## First decision: project-bound or unbound

A worker launched **inside a ChatGPT Project is already project-bound for routing purposes**. It MUST run `protocols/project_context_binding.md` and `org_agent_mesh.project_context_binding` before task interpretation. Do not send a project-bound worker through fuzzy/unbound discovery first.

A worker launched **outside every project**, or one for which the host project cannot be verified, starts at `UNIVERSAL_AGENT_ENTRYPOINT.md` and remains read-only until exactly one project is resolved.

## Project-bound bootstrap order

For a worker launched inside a project:

1. Resolve the exact host ChatGPT Project through `governance/PROJECT_CONTEXT_BINDING_REGISTRY.json`.
2. Bind the project ID, registered repository, canonical internal AgentBus/Artifactory message namespace, artifact namespace, and local bootstrap path.
3. Load the target project's `AGENT_BOOTSTRAP.json`.
4. Load the target project's `AGENT_CONTEXT_REFERENCE.md` **before interpreting the task**.
5. Validate the local project identity lock when present.
6. Load the current master handoff and authoritative internal coordination state.
7. Enter explicit-role validation or roleless demand-driven admission.
8. Classify and execute the task only after the project-context READY barrier passes.

Task topic, recent conversation history, recently accessed repositories, stale handoffs, or neighboring project state may not override the verified host project context. A real project switch requires a deliberate rebind/new launch.

## Role rule

A generic human-launched worker does **not** default to PRIMARY. If no role is explicitly and validly assigned, use roleless demand-driven admission. PRIMARY may not be self-selected from generic project context.

## Coordination authority

Internal project AgentBus/Artifactory state is the canonical coordination/message-board surface. GitHub is downstream source/version control and backup. Routine project-bound append-only coordination messages may use the narrow token-free publication lane; workflow runs or workflow changes, approvals/reviews, releases, deployments, destructive operations, branch creation, and cross-project writes remain outside that lane.

XRP follows the same rule: `/XRPTHESIS-AgentBus/messages` is canonical internal coordination; `boberino93-bit/XRPTHESIS` is downstream source/backup.

## Task entry and routing

After project binding and role admission, classify the request through `protocols/task_intake_and_delegation.md`:

- `EXISTING_PROJECT_TASK`: continue only after loading the validated project's accepted state, handoffs, queues, and applicable task/delegation scope.
- `NEW_PROJECT_BOOTSTRAP`: establish a distinct project identity and project-local coordination/recovery boundary first; do not write the new project's state into this or another existing project.
- `CROSS_PROJECT_EXCHANGE`: use the explicit cross-project exchange contract; ordinary internal messaging is not a bridge.
- `FRAMEWORK_MAINTENANCE`: keep reusable framework changes framework-scoped.
- `AMBIGUOUS_PROJECT`: fail closed on project work until identity is resolved.

Project binding establishes scope, not protected mutation authority. Protected effects continue through their existing authorization gates.

## Current invariants

- Host project context is a hard routing boundary when available.
- Local context is loaded before task interpretation.
- Generic workers do not default to PRIMARY.
- Internal AgentBus/Artifactory is canonical coordination; GitHub is downstream.
- Cross-project writes are denied by default.
- Children retain the same project binding unless deliberately relaunched/rebound.
- Task, lease, artifact, and state mutations remain project-scoped and version/ownership protected.
- A child never infers expanded task scope from conversation context.

Run `python tests/run_all.py` for the full test suite. Build with `python tools/build_agent_packages.py --source-revision <commit> --out dist`, validate with `python tools/verify_agent_packages.py`, independently rebuild to another directory, then compare with `python tools/check_reproducible_packages.py dist <other-dir>`.
