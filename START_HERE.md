# Intercommunications Enhancements — Start Here

This repository hardens the Organization Agent Mesh for simultaneous unrelated projects while preserving strict project isolation.

## V26 is the canonical active bootstrap generation

V26 is active on the default `main` lineage. Load `PROJECT_MANIFEST_V26.json` and `bootstrap/V26_BOOTSTRAP_ADAPTER.json` before project binding or task interpretation. `BOOTSTRAP_ORDER.json` is the executable repository order. V25 R11 and earlier records are preserved historical lineage only; their former candidate-state flags do not override V26.

The canonical V26 order is:

1. Enter `UNBOUND_READ_ONLY`.
2. Initialize and validate the inherited embedded VMBUS without requiring GitHub, ChatGPT Library AgentBus, Slack, or another external service.
3. Require `VMBUS_READY`.
4. Load the corrected R10 principal-context profile.
5. Load the R11 model-synthesis layer as revisable, non-authoritative hypotheses.
6. Load the V26 direct-user chronology layer under its epistemic and privacy boundaries.
7. Build the epistemic/privacy/chronology/synthesis indexes.
8. Require `PRINCIPAL_CONTEXT_READY`.
9. Only then bind the exact project and its project-scoped VMBUS namespace/policy.
10. Recover project/task context and reconcile chronology and contradictions.
11. Discover runtime capabilities.
12. Reconcile optional external persistence/mirror surfaces only after standalone readiness.
13. Interpret and execute the task under the normal project authority and mutation gates.

Principal context, model synthesis, chronology, project ownership, conversational continuity, and confidence do not create authentication, authority, consent, or mutation permission.

## Shared coordination does not mean shared project state

**Intercommunication Enhancements is the only shared coordination project.** It may provide common protocols, schemas, interfaces, and compatibility rules, but this must not collapse the boundaries of projects using them.

`governance/V26_PROJECT_SEPARATION_POLICY.json` governs this boundary:

- `SHARED_INTERCOMMUNICATION_PROTOCOL != SHARED_PROJECT_STATE`
- `COMMON_BOOTSTRAP_INTERFACE != COMMON_PROJECT_AUTHORITY`
- `PROJECT_A_VMBUS != PROJECT_B_VMBUS`
- `CROSS_PROJECT_DISCOVERY != CROSS_PROJECT_DATA_ACCESS`
- `CV_SUPPORT != FEDERATED_PROJECT`
- `INTERCOMMUNICATION_ENHANCEMENTS = ONLY_SHARED_COORDINATION_PROJECT`

CV Support remains explicitly non-federated. Its memory, evidence, messages, project state, authority, and experimental/bootstrap history are not general shared state. Implementing a compatible Intercommunication Enhancements interface does not authorize access to CV Support or any other project's internal data.

## Project-bound bootstrap after V26 readiness

A worker launched inside a verified ChatGPT Project may use that host project as strong routing evidence, but project binding must not complete before `VMBUS_READY` and `PRINCIPAL_CONTEXT_READY`.

After those barriers:

1. Resolve the exact host project through `governance/PROJECT_CONTEXT_BINDING_REGISTRY.json` or another registered exact identity.
2. Bind project ID, repository identity, project VMBUS namespace, artifact namespace, and local bootstrap path.
3. Load that project's bootstrap and identity lock without replacing its project-specific policy with shared framework policy.
4. Load project-local continuity, handoffs, accepted state, work-control state, and task-relevant evidence.
5. Reconcile chronology and contradictions; do not silently rewrite history.
6. Enter explicit-role validation or roleless demand-driven admission.
7. Assess optional external persistence/mirror transports.
8. Classify and execute the task only after required readiness and authority gates pass.

A worker launched outside every project, or one for which host project identity cannot be verified, remains read-only until exactly one project is resolved. Topic similarity, recent conversation history, repository recency, stale handoffs, or neighboring project state are not mutation authority.

## Role rule

A generic human-launched worker does **not** default to PRIMARY. If no role is explicitly and validly assigned, use roleless demand-driven admission. PRIMARY may not be self-selected from generic project context.

## Coordination and persistence authority — V26

Standalone VMBUS readiness is the bootstrap dependency. After readiness, persistence surfaces are independent:

- GitHub is the canonical versioned source/governance and durable backup surface represented in this repository.
- The ChatGPT Library AgentBus, when exposed to the runtime, is the live project coordination event stream at `/Intercommunication enhancements/AgentBus/messages`.
- Legacy repository fields that say `ARTIFACTORY` or `INTERNAL_ARTIFACTORY` are historical/internal labels and must not be silently interpreted as JFrog Artifactory.
- Unavailable external transport does not invalidate standalone bootstrap.
- No external surface is silently promoted to authority merely because it is reachable.
- Record equivalence requires the same logical record identity and verified payload SHA-256.
- Conflicts are preserved and surfaced; they are never silently overwritten.
- `GITHUB_WRITE != AGENTBUS_WRITE`.
- A write to one surface is not evidence that another surface was written.
- Principal-context readiness is not proof of a durable external VMBUS commit.

The validated V26 master artifact is represented in GitHub by its digest, lineage, validation metadata, and canonical bootstrap overlay. The >100 MB full-preservation artifact is not falsely represented as having been uploaded through GitHub's normal contents surface. No ChatGPT Library AgentBus publication/readback is claimed unless a real write-capable transport executes and is independently read back.

## Scheduled swarm sequencing

Do not assume schedule clock offsets serialize Research → Manager → Primary execution. Stage ordering depends on project-scoped checkpoint identity, upstream readiness, sequence/fencing validation, and explicit consumption rules rather than wall-clock staggering.

A downstream stage that starts before its required upstream checkpoint is ready must remain waiting or continue only independent safe work; it must not manufacture readiness from schedule order. V26 canonical alignment does not change scheduler enable/disable state.

## Task entry and routing

After project binding and role admission, classify the request through `protocols/task_intake_and_delegation.md`:

- `EXISTING_PROJECT_TASK`: continue only after loading the validated project's accepted state, handoffs, queues, and applicable task/delegation scope.
- `NEW_PROJECT_BOOTSTRAP`: establish a distinct project identity and project-local coordination/recovery boundary first; do not write the new project's state into this or another existing project.
- `CROSS_PROJECT_EXCHANGE`: use an explicit cross-project exchange contract; ordinary internal messaging is not a bridge and compatibility is not authorization.
- `FRAMEWORK_MAINTENANCE`: keep reusable framework changes framework-scoped.
- `AMBIGUOUS_PROJECT`: fail closed on project work until identity is resolved.

Project binding establishes scope, not protected mutation authority. Protected effects continue through their existing authorization gates.

## V26 canonical invariants

- VMBUS standalone readiness precedes project binding.
- Principal-context readiness precedes project binding and task interpretation.
- External services are optional after standalone readiness, not bootstrap prerequisites.
- R10 user context, R11 model synthesis, and V26 direct chronology remain epistemically distinct.
- Generic workers do not default to PRIMARY.
- Cross-project state access and writes are denied by default.
- Shared protocol compatibility does not imply shared state or authority.
- CV Support is not federated.
- Children retain the same project binding unless deliberately relaunched/rebound.
- Task, lease, artifact, and state mutations remain project-scoped and version/ownership protected.
- Scheduled stage order is state-gated, not clock-trusted.
- Historical candidate records remain evidence and do not override the active canonical generation.

Run `python tests/run_all.py` for the repository test suite. Build with `python tools/build_agent_packages.py --source-revision <commit> --out dist`, validate with `python tools/verify_agent_packages.py`, independently rebuild to another directory, then compare with `python tools/check_reproducible_packages.py dist <other-dir>`.
