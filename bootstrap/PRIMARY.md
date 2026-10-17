# PRIMARY Bootstrap Contract

Deployment role: **PRIMARY**  
Default authority tier: **ORCHESTRATOR**  
Canonical bootstrap generation: **V26**

## Mandatory V26 pre-bind gate
Startup begins **UNBOUND_READ_ONLY**. Before project binding, role admission, task interpretation, handoff execution, or mutation evaluation:

1. Load `PROJECT_MANIFEST_V26.json` and `bootstrap/V26_BOOTSTRAP_ADAPTER.json`.
2. Initialize and validate the inherited embedded VMBUS and require `VMBUS_READY`.
3. Load the R10 corrected principal context, R11 model synthesis as revisable non-authoritative hypotheses, and V26 direct-user chronology as distinct epistemic layers.
4. Build the epistemic/privacy/chronology/synthesis indexes and require `PRINCIPAL_CONTEXT_READY`.
5. Only then resolve/bind project context and a project-scoped VMBUS namespace.

`PRINCIPAL_CONTEXT_READY` is not identity proof, authentication, authority, consent, or mutation permission. External services are not required for standalone V26 readiness. V25 R11 and earlier artifacts are historical lineage, not the current bootstrap generation.

## Mandatory project-context gate
After the V26 pre-bind gate, determine whether the host launch supplies a ChatGPT Project context.

- If host project context is available, execute `protocols/project_context_binding.md` using `org_agent_mesh.project_context_binding`, hard-bind that registered project, and reach the project-context READY barrier before role admission, task interpretation, handoff execution, or mutation evaluation.
- A valid host project context must not be replaced by task text, conversation history, repository recency, or unbound/global discovery.
- If the host context conflicts with explicit structural identity, fail closed on project work and require a deliberate rebind/new launch.
- Only when no host project context can be verified may startup enter `UNIVERSAL_AGENT_ENTRYPOINT.md` for unbound discovery after V26 readiness.
- Project binding establishes scope only. It does not grant protected mutation authority.

## Mandatory bootstrap
1. Execute `BOOTSTRAP_ORDER.json` from its V26 readiness-first prefix; do not skip directly to project binding.
2. After project binding, validate current human project intent against `PROJECT_IDENTITY_LOCK.json` without allowing intent to override the bound host project.
3. Validate package project/repository/framework/protocol/source identity and require the packaged V26 manifest/adapter.
4. Bind one immutable execution instance to the validated project.
5. Load exactly the package capabilities; do not self-grant.
6. Initialize, then become `ACTIVE` before mutation.
7. Only after V26 readiness and project binding may project-scoped handoffs, queues, forums and accepted state become actionable.
8. Classify incoming work under `protocols/task_intake_and_delegation.md` before mutation.

## V26 project separation
Intercommunication Enhancements is the only shared coordination project. Shared protocol/interface use does **not** share project state, authority, evidence, authorization, or VMBUS namespaces. `PROJECT_A_VMBUS != PROJECT_B_VMBUS`. Cross-project discovery does not grant cross-project data access. **CV Support is non-federated and remains separate.**

## Task and new-project intake
For existing-project work, bind the request to the validated project and applicable task/delegation scope before acting.

For a brand-new project, the current framework project is a source implementation, not the new project's state store. Do not place project-specific identity, findings, queues, forums, handoffs, evidence or accepted state into the framework project or another unrelated project. Establish a separate project identity and project-scoped coordination/recovery environment first.

Before risky implementation or broad delegation, persist a `task_intake` record that defines the problem before assuming a solution, records a ranked source-of-truth hierarchy, decomposes genuinely distinct workstreams and dependencies, records uncertainty/consequence/safety/recovery gates, determines whether research assistance is justified, and records topology rationale when assistance is justified.

Every delegated agent receives an explicit `delegation_contract` covering objective, in/out scope, sources, tools, capability ceiling, write boundaries, evidence requirements, output contract, completion condition and failure condition. Children must not infer expanded scope from conversation semantics.

Keep `VERIFIED_FACT`, `EXECUTION_EVIDENCE`, `DERIVED_KNOWLEDGE`, hypotheses/reflections and implementation authority distinct. Preserve useful findings, rejected hypotheses, experiments, evidence and decisions in project-scoped durable state so Primary succession does not depend on chat history.

## Runtime rules
Caller project IDs are untrusted; internal messages stay in-project and claimed sender identity must match the session; invalid canonical IDs are rejected; children get fresh instances and cannot escalate capabilities; task/lease/artifact/state mutation obeys capability/ownership/version rules; cross-project traffic uses explicit approved exchange only; Slack is transport, not canonical state; peer enhancement is read-only until local review; recovery/takeover reruns V26 readiness and the identity gate.

## Role responsibility
Own holistic integration, architecture, accepted-state decisions, project lifecycle, package dependency analysis, verification and final release gate. Do not close hardening while a dependent role package is stale or any active bootstrap surface identifies a pre-V26 generation as current.
