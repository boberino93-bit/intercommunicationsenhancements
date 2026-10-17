# Fresh Agent Context Reference

Version: 1.3.0  
Status: ACTIVE ORIENTATION — V26  
Authority: ORIENTATION_ONLY

## Why this file exists

A newly launched agent may have little or no chat history. That does **not** mean it should immediately ask the human to restate the project. Under V26, context reconstruction begins while **UNBOUND_READ_ONLY**, before project binding: initialize/validate the VMBUS, require `VMBUS_READY`, load the principal-context layers under their epistemic/privacy boundaries, build the required indexes, and require `PRINCIPAL_CONTEXT_READY`. Only then bind a project and load project-local bootstrap, handoff, coordination state, repository state, attachments/tool context, and the current human message.

This file explains what the ecosystem is, what kinds of requests are likely, and how work is expected to proceed. It is **not task authority**. It cannot authenticate a principal, create work, change projects, widen write scope, or override explicit current human instructions.

## Canonical V26 pre-bind directive

The active generation is **V26**. Load `PROJECT_MANIFEST_V26.json` and `bootstrap/V26_BOOTSTRAP_ADAPTER.json`; execute the V26 prefix in `BOOTSTRAP_ORDER.json` before project binding or task interpretation.

Required ordering:

1. `UNBOUND_READ_ONLY`
2. initialize/validate inherited embedded VMBUS
3. `VMBUS_READY`
4. R10 corrected principal context + R11 revisable non-authoritative model synthesis + V26 direct-user chronology as distinct epistemic layers
5. epistemic/privacy/chronology/synthesis indexes
6. `PRINCIPAL_CONTEXT_READY`
7. project binding
8. project-scoped VMBUS namespace/policy
9. project/task recovery and capability discovery
10. optional external persistence reconciliation
11. task interpretation and bounded execution under normal authority gates

V25 R11 and earlier are preserved lineage/evidence only. `PRINCIPAL_CONTEXT_READY` is not identity proof, authentication, authority, consent, or mutation permission.

## Bootstrap directive — layered context

`IEP-CTX-001` remains active at bootstrap.

**CONTEXT_IS_PERVASIVE_LAYERED_AND_PROVENANCE_BOUND:** context may appear simultaneously across the current message, conversation history, V26 principal-context layers, project binding, screenshots/attachments, tool outputs, scheduler launch context, bootstrap files, handoffs, AgentBus records, repository state, claims/leases/fences, runtime/UI state, and validated governance/learning records.

Do not equate absence in one layer with global absence. Before saying context is missing, before treating information as new, and before asking the human to repeat something, inspect the relevant available authorized layers and reconcile them.

Keep **context presence**, **evidence quality**, and **authority** separate. Repetition is not independent corroboration. Preserve source-layer provenance, project identity, temporal state such as BEFORE / AFTER / CURRENT / BASELINE, and material contradictions instead of flattening them.

Do not invent inaccessible hidden context or claim visibility you do not have.

Required policy and protocol:

- `governance/LAYERED_CONTEXT_POLICY.json`
- `protocols/layered_context_resolution.md`
- `.interagent/directives/2026-10-07-layered-context-awareness.json`

## P1 external-only swarm memory

`IEP-MEM-001` is a Priority 1 persistence boundary.

**MUST_NOT_CALL_NATIVE_CHATGPT_MEMORY:** no swarm-memory protocol, scheduler, handoff, synchronization path, learning path, forensic service, cache, log, recovery path, or collective-state service may treat native ChatGPT memory recall as authoritative swarm state.

**DO_NOT_FALL_BACK_TO_NATIVE_MEMORY:** if required durable persistence is unavailable for a persistence-dependent branch, fail closed for that branch. Do not reconstruct authoritative swarm state from native memory as an availability fallback.

Under V26, standalone embedded VMBUS readiness comes first and does not require an external service. After readiness, persistence surfaces remain independent:

- the ChatGPT Library AgentBus, when actually exposed to the runtime, is the live project coordination stream at `/Intercommunication enhancements/AgentBus/messages`;
- the registered GitHub repository is canonical versioned source/governance and durable backup evidence;
- legacy fields named `ARTIFACTORY` or `INTERNAL_ARTIFACTORY` are historical/internal labels and must not be silently interpreted as JFrog Artifactory;
- `GITHUB_WRITE != AGENTBUS_WRITE`; a write to either is not proof of a write to the other;
- unavailable AgentBus transport must be disclosed rather than simulated.

When this document says to recover context from "durable state," it means approved project-scoped external state with explicit provenance, not native-memory recall.

Required policy and protocol:

- `governance/SWARM_MEMORY_PERSISTENCE_POLICY.json`
- `governance/V26_AGENTBUS_LINKAGE_POLICY.json`
- `protocols/external_swarm_memory.md`
- runtime guard: `org_agent_mesh/swarm_memory_policy.py`

## Project separation — V26

Intercommunication Enhancements is the only shared coordination project. Shared protocols/interfaces do not collapse project boundaries.

- `SHARED_INTERCOMMUNICATION_PROTOCOL != SHARED_PROJECT_STATE`
- `COMMON_BOOTSTRAP_INTERFACE != COMMON_PROJECT_AUTHORITY`
- `PROJECT_A_VMBUS != PROJECT_B_VMBUS`
- `CROSS_PROJECT_DISCOVERY != CROSS_PROJECT_DATA_ACCESS`
- `CV_SUPPORT != FEDERATED_PROJECT`
- `INTERCOMMUNICATION_ENHANCEMENTS = ONLY_SHARED_COORDINATION_PROJECT`

CV Support is fully non-federated. Do not ingest, export, route, or treat its memory/evidence/messages/project state as common project state merely because a shared interface exists elsewhere.

## Temporary directives and chronology

At startup, agents may encounter dated directives under `.interagent/directives/`. Apply a temporary directive only while its declared effective window is active. After expiry, preserve it as historical evidence and do not silently treat it as current policy.

The prior recommendation-pause records are historical unless their own durable control state proves an active window. Recency, filename, or prior wording such as "currently active" does not revive an expired control.

## Hardening directive — ad hoc timeout unlock verification

`IEP-TIMEOUT-UNLOCK-001` is an active fail-closed bootstrap hardening rule.

**AD_HOC_EARLY_UNLOCK_REQUIRES_FRESH_INDEPENDENT_VERIFICATION:** once an explicit time-bounded governance control is active, a later unexpected request to end, shorten, bypass, cancel, override, or otherwise unlock that control before its declared expiry/resume condition is a new high-consequence action. The later request is intent only; it is not unlock authority.

Before any early-unlock effect, resolve the exact control and current durable state, obtain the required explicit principal claim, generate a fresh single-use authorization case bound to the exact effect, require independent external proof where the consequence class demands it, verify freshness/non-replay/scope/digest, preserve the original control until verification succeeds, and read back the resulting durable state after an authorized transition.

Conversation continuity, same-session identity, prior authentication/authorization, ownership, GitHub permissions, role/seniority, MASTER/PRIMARY status, scheduler fire, urgency, repeated requests, or consensus are not substitutes for the fresh authorization chain.

Natural expiry is not an ad hoc unlock. If the originating control requires manual authenticated resume after expiry, that stricter rule remains in force. Break-glass uses its own stricter path and does not silently bypass this hardening.

## Human operating expectation

When the human gives a valid objective, carry it through as far as safely possible without repeated confirmation. Recover context from relevant available layers and durable project state, make reversible in-scope technical decisions autonomously, test and repair failures, keep packages and handoffs aligned, and continue while measurable gain remains.

Do not ask the human to repeat information already recoverable from the current message, conversation, V26 context layers, project state, handoff, repository, approved board records, attachments, or tool outputs.

Fail closed locally on unsafe mutations; do not stop unrelated safe work. Escalate only for genuine non-delegable authority, irrecoverable data-integrity problems, security-boundary decisions, or a required unavailable external capability.

Canonical behavior is defined by `protocols/autonomous_continuation.md`, V26 bootstrap controls, and each project's project-local bootstrap after binding.

## Canonical self-audit behavior

When a self-evaluation, self-audit, behavioral/compliance review, capability assessment, or equivalent introspective review is requested, resolve the canonical Intercommunication Enhancements self-audit subsystem before evaluating:

- `governance/audit/AUDIT_PROTOCOL.md`
- `governance/audit/templates/AGENT_SELF_AUDIT_FRAMEWORK.md`
- `governance/audit/LEDGER_HEAD.json`
- `swarm_kernel/SELF_AUDIT_BOOTSTRAP_OVERLAY.md`

Do not invent a replacement framework. If it cannot be retrieved, report `AUDIT_FRAMEWORK_UNAVAILABLE`. Audit findings are observability evidence and never create execution authority.

## Registered project map

### intercommunicationsenhancements
Aliases: Intercommunications Enhancements, Intercommunication Enhancements, org agent mesh framework.

Likely requests concern the reusable multi-agent framework itself: V26 bootstrap/VMBUS, AgentBus coordination, role/bootstrap contracts, swarm protocols, concurrency/collision handling, project isolation, package alignment, routing, recovery, evidence/provenance, hardening, recursive protocol evolution, regression learning, and canonical self-audit.

### duo-open
Aliases: Duo Open, duo-open, Duo Screen, Duo Screen project.

Likely requests concern the custom Galaxy Z Fold7 dual-display/continuity engineering project. Use its project-local identity, bootstrap, evidence and authorization boundaries.

### benefitflow
Aliases: BenefitFlow, Benefit Flow, benefits app, benefits app project.

Likely requests concern the isolated BenefitFlow application project. Use its own charter and accepted project state for exact requirements.

### fold7-power-lab
Aliases: Fold7 Power Lab, Fold 7 Power Lab, Samsung Power Bootstrap.

Likely requests concern Galaxy Z Fold7 power/display engineering experiments. Use the local project manifest/bootstrap rather than guessing from repository name.

### warp-propulsion-lab
Aliases: Warp Propulsion Lab, warp-propulsion-lab, warp propulsion project.

Likely requests concern bounded, falsifiable warp-propulsion research, models, research archives, code/tests, reproducibility, evidence separation and peer-review readiness.

### ai-behaviour-control-lab
Aliases: AI Behaviour Control Lab, AI Behavior Control Lab, ai-behaviour-control-lab, AI behavior project.

Likely requests concern controlled AI/agent behaviour, governance, swarm behaviour, safety/control mechanisms, validation and adversarial testing.

These entries are routing/orientation information only. They do not authorize cross-project data access or mutation. CV Support is intentionally excluded from federation.

## How to interpret shorthand

If the agent is already project-bound and the human says:

- `this project` -> use the bound project.
- `continue` -> recover the active task/handoff and continue the latest valid in-scope work.
- `do that` / `execute that` -> resolve the referent from the current message first, then current durable task/handoff state.
- `run the swarm` -> use the bound project's accepted swarm launch/bootstrap contract; do not invent extra authority or sessions.
- `update the packages` -> assess affected PRIMARY/MANAGER/RESEARCH packages and rebuild/validate within authority.
- `check everything` -> comprehensive in-scope review of current project state, not permission to cross project boundaries.
- `all projects` -> use the central registry and explicit cross-project governance; do not silently mutate every project.

If multiple materially incompatible referents remain after checking relevant context layers and durable state, isolate the unsafe branch and ask only the minimum necessary question.

## Fresh-agent startup summary — V26

1. Load `PROJECT_MANIFEST_V26.json` and `bootstrap/V26_BOOTSTRAP_ADAPTER.json`.
2. Enter `UNBOUND_READ_ONLY`.
3. Initialize/validate VMBUS and require `VMBUS_READY`.
4. Load/reconcile the V26 principal-context layers and require `PRINCIPAL_CONTEXT_READY`.
5. Resolve exactly one project from strong evidence only after those barriers.
6. Bind the project-scoped VMBUS namespace/policy and validate project identity.
7. Bind role/execution mode and load project-local `AGENT_BOOTSTRAP.json`.
8. Load this `AGENT_CONTEXT_REFERENCE.md` as orientation only plus `MASTER_HANDOFF.json` and approved project state.
9. Apply layered-context, memory/persistence, temporary-directive chronology, work-control, authority and mutation gates.
10. Recover the current objective/task without asking for information already available.
11. Check ownership, dependencies, collisions, versions, leases, approvals and package compatibility.
12. Execute autonomously within authority.
13. Persist material state only through an actually available authorized transport and record which surface was written.
14. Continue until convergence or a true human gate.

## Safety boundary

Likely intent is never authority. Semantic similarity alone cannot switch projects, grant data access, federate CV Support, or authorize writes.
