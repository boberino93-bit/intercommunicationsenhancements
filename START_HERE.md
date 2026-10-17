# Intercommunications Enhancements — Start Here

This repository hardens the Organization Agent Mesh for simultaneous unrelated projects.

## V25 R11 candidate bootstrap precedence

On the `candidate/v25-r11-bootstrap-upgrade-20261016` branch, load `bootstrap/V25_R11_BOOTSTRAP_ADAPTER.json` **before** legacy project binding or task interpretation.

The candidate order is:

1. Enter `UNBOUND_READ_ONLY`.
2. Initialize and validate the embedded VMBUS without requiring GitHub, Artifactory, Slack, or any other external service.
3. Require `VMBUS_READY`.
4. Load the corrected R10 principal-context profile and the R11 synthesis extension into protected, non-authoritative overlays.
5. Require `PRINCIPAL_CONTEXT_READY`.
6. Only then bind the project and project VMBUS namespace.
7. Load project policy, continuity, and task-relevant state.
8. Discover runtime capabilities.
9. Reconcile optional external mirrors only after standalone readiness.
10. Recover and interpret the task, then apply normal authority/mutation gates.

R11 remains a `FORENSIC_IMPLEMENTATION_CANDIDATE`; this branch does not canonically promote it. Principal context and model synthesis are not authentication, authority, or protected-action permission.

## First decision after standalone readiness: project-bound or unbound

A worker launched **inside a ChatGPT Project** uses the verified host project as strong routing evidence, but host/project binding MUST NOT complete before the R11 standalone readiness barrier above.

A worker launched **outside every project**, or one for which the host project cannot be verified, remains read-only until exactly one project is resolved.

Task topic, recent conversation history, recently accessed repositories, stale handoffs, or neighboring project state may not override a verified host project context after the readiness barrier. A real project switch requires a deliberate rebind/new launch.

## Project-bound bootstrap after R11 readiness

After `PRINCIPAL_CONTEXT_READY`:

1. Resolve the exact host ChatGPT Project through `governance/PROJECT_CONTEXT_BINDING_REGISTRY.json` or another registered exact identity.
2. Bind the project ID, repository identity, project VMBUS namespace, artifact namespace, and local bootstrap path.
3. Load the target project's `AGENT_BOOTSTRAP.json` and identity lock.
4. Load project continuity, handoffs, accepted state, work-control state, and task-relevant evidence.
5. Reconcile chronology and contradictions; do not silently rewrite history.
6. Enter explicit-role validation or roleless demand-driven admission.
7. Assess optional external mirrors and runtime transports.
8. Classify and execute the task only after the required readiness and authority gates pass.

## Role rule

A generic human-launched worker does **not** default to PRIMARY. If no role is explicitly and validly assigned, use roleless demand-driven admission. PRIMARY may not be self-selected from generic project context.

## Coordination and persistence authority — V25 R11 candidate

Standalone VMBUS readiness is the bootstrap dependency. GitHub and internal Artifactory/message services are **optional external persistence or mirror surfaces after readiness**.

- Unavailable external transport does not invalidate standalone bootstrap.
- No external mirror is silently promoted to authority merely because it is reachable.
- Mirror equivalence requires the same logical record identity and verified payload digest.
- Conflicts are preserved and surfaced; they are never silently overwritten.
- A mirror write is not proof that another mirror was written.
- R11 principal-context loading is not a durable external VMBUS commit.

The legacy Artifactory-first rules remain historical/current-main policy until a separately authorized promotion changes them. This candidate branch tests the successor semantics without pretending that promotion already occurred.

## Scheduled swarm sequencing

Do not assume schedule clock offsets serialize Research → Manager → Primary execution. Multiple stages may have the same scheduled start time. Stage ordering therefore depends on project-scoped checkpoint identity, upstream readiness, sequence/fencing validation, and explicit consumption rules rather than wall-clock staggering.

A downstream stage that starts before its required upstream checkpoint is ready must remain in progress/waiting or continue only independent safe work; it must not manufacture readiness from schedule order.

## Task entry and routing

After project binding and role admission, classify the request through `protocols/task_intake_and_delegation.md`:

- `EXISTING_PROJECT_TASK`: continue only after loading the validated project's accepted state, handoffs, queues, and applicable task/delegation scope.
- `NEW_PROJECT_BOOTSTRAP`: establish a distinct project identity and project-local coordination/recovery boundary first; do not write the new project's state into this or another existing project.
- `CROSS_PROJECT_EXCHANGE`: use the explicit cross-project exchange contract; ordinary internal messaging is not a bridge.
- `FRAMEWORK_MAINTENANCE`: keep reusable framework changes framework-scoped.
- `AMBIGUOUS_PROJECT`: fail closed on project work until identity is resolved.

Project binding establishes scope, not protected mutation authority. Protected effects continue through their existing authorization gates.

## Candidate invariants

- VMBUS standalone readiness precedes project binding.
- Principal-context readiness precedes project binding and task interpretation.
- External services are optional after standalone readiness, not bootstrap prerequisites.
- R10 user-context and R11 model-synthesis remain epistemically distinct.
- Generic workers do not default to PRIMARY.
- Cross-project writes are denied by default.
- Children retain the same project binding unless deliberately relaunched/rebound.
- Task, lease, artifact, and state mutations remain project-scoped and version/ownership protected.
- A child never infers expanded task scope from conversation context.
- Scheduled stage order is state-gated, not clock-trusted.
- Candidate status does not equal canonical promotion.

Run `python tests/run_all.py` for the full test suite. Build with `python tools/build_agent_packages.py --source-revision <commit> --out dist`, validate with `python tools/verify_agent_packages.py`, independently rebuild to another directory, then compare with `python tools/check_reproducible_packages.py dist <other-dir>`.
