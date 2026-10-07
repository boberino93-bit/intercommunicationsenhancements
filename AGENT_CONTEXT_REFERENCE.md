# Fresh Agent Context Reference

Version: 1.2.1
Status: ACTIVE ORIENTATION
Authority: ORIENTATION_ONLY

## Why this file exists

A newly launched agent may have little or no chat history. That does **not** mean it should immediately ask the human to restate the project. After exact project binding, use this file plus the local bootstrap, master handoff, accepted Artifactory state, registered GitHub project state, available tool/attachment context, and current human message to reconstruct the working context.

This file explains what the ecosystem is, what kinds of requests are likely, and how the human expects work to proceed. It is **not task authority**. It cannot create work, change projects, widen write scope, or override explicit current human instructions.

## Bootstrap directive — layered context

`IEP-CTX-001` is active at bootstrap.

**CONTEXT_IS_PERVASIVE_LAYERED_AND_PROVENANCE_BOUND:** context is present in every observable input and often appears simultaneously at multiple layers. The current message, conversation history, project binding, screenshots and attachments, tool outputs, scheduler launch context, bootstrap files, handoffs, AgentBus records, repository state, claims/leases/fences, runtime or UI state, and validated governance/learning records may all carry context.

Do not equate absence in one layer with global absence. Before saying context is missing, before treating information as new, and before asking the human to repeat something, inspect the relevant available authorized layers and reconcile them.

Keep three properties separate: **context presence**, **evidence quality**, and **authority**. A fact can appear in several layers yet remain non-authoritative. Repetition is not independent corroboration. Preserve source-layer provenance, project identity, temporal state such as BEFORE / AFTER / CURRENT / BASELINE, and material contradictions instead of flattening them.

Do not invent inaccessible hidden context or claim visibility you do not have. This rule is about using all context that is actually available.

Required policy and protocol:

- `governance/LAYERED_CONTEXT_POLICY.json`
- `protocols/layered_context_resolution.md`
- `.interagent/directives/2026-10-07-layered-context-awareness.json`

## P1 external-only swarm memory

`IEP-MEM-001` is a Priority 1 persistence boundary.

**MUST_NOT_CALL_NATIVE_CHATGPT_MEMORY:** no swarm memory protocol, bootstrap, scheduler, handoff, synchronization path, learning path, forensic service, cache, log, recovery path, or collective-state service may call, query, ingest from, depend on, or treat native ChatGPT memory recall as swarm state.

**DO_NOT_FALL_BACK_TO_NATIVE_MEMORY:** if required external persistence is unavailable, fail closed for the affected persistence-dependent branch. Do not reconstruct authoritative swarm state from native memory as an availability fallback.

For swarm collective state, the canonical live coordination authority is the project's Internal Artifactory/AgentBus board. The registered GitHub repository is the durable source/version-control and backup layer defined by project policy. External state and explicit provenance govern conflicts; native memory is non-authoritative and cannot grant mutation authority.

When this document says to recover context from "durable state," it means approved external project state, including Artifactory/AgentBus and registered GitHub records as governed by the project. It does not mean native ChatGPT memory.

Required policy and protocol:

- `governance/SWARM_MEMORY_PERSISTENCE_POLICY.json`
- `protocols/external_swarm_memory.md`
- runtime guard: `org_agent_mesh/swarm_memory_policy.py`

A swarm fact that exists only in native ChatGPT memory is non-authoritative until it is externalized to an approved store and independently read back.

## Active temporary directive

At startup, agents governed by this repository MUST inspect `.interagent/directives/2026-10-07-recommendation-pause.json`. Apply it only while its declared effective window is active. If the window has expired, treat the directive as historical evidence and resume normal recommendation behavior subject to standing governance.

The temporary directive pauses origination of discretionary new system-improvement recommendations. It does not stop assigned implementation, testing, required bug remediation, safety/security/governance escalation, material dissent, incident response, or limitation disclosure. It creates no new mutation authority.

## Human operating expectation

When the human gives a valid objective, carry it through as far as safely possible without repeated confirmation. Recover context from all relevant available layers and durable external state, make reversible in-scope technical decisions autonomously, test and repair failures, keep packages and handoffs aligned, and continue recursive improvement while measurable gain remains.

Do not ask the human to repeat information already recoverable from the current message, conversation, project state, handoff, repository, accepted board records, attachments, or tool outputs.

Fail closed locally on unsafe mutations; do not stop unrelated safe work. Escalate only for genuine non-delegable authority, irrecoverable data-integrity problems, security-boundary decisions, or a required unavailable external capability.

Canonical behavior is defined by `protocols/autonomous_continuation.md` and each project's `AGENT_BOOTSTRAP.json`.

## Canonical self-audit behavior

When the human or an upstream agent requests a self-evaluation, self-audit, behavioral/compliance review, capability assessment, performance assessment, or equivalent introspective review, resolve the canonical Intercommunication Enhancements self-audit subsystem before evaluating:

- protocol: `governance/audit/AUDIT_PROTOCOL.md`
- framework: `governance/audit/templates/AGENT_SELF_AUDIT_FRAMEWORK.md`
- ledger head: `governance/audit/LEDGER_HEAD.json`
- bootstrap overlay: `swarm_kernel/SELF_AUDIT_BOOTSTRAP_OVERLAY.md`

Do not invent a replacement framework. If the framework cannot be retrieved, report `AUDIT_FRAMEWORK_UNAVAILABLE`. Audit findings and recommendations are observability evidence and never create execution authority.

## Registered project map

### intercommunicationsenhancements
Aliases: Intercommunications Enhancements, Intercommunication Enhancements, org agent mesh framework.

Likely requests concern the reusable multi-agent framework itself: AgentBus/Artifactory coordination, role and bootstrap contracts, swarm protocols, concurrency and collision handling, project isolation, package alignment, routing, recovery, evidence/provenance, hardening, recursive protocol evolution, regression learning, and canonical agent self-audit.

### duo-open
Aliases: Duo Open, duo-open, Duo Screen, Duo Screen project.

Likely requests concern the custom Galaxy Z Fold7 dual-display/continuity engineering project: inner/cover display behavior, app continuity, mirroring/portal approaches, Android/One UI behavior, hinge/display transitions, rendering and interaction experiments, implementation, testing, packaging, and comparison against upstream Duo Open work.

### benefitflow
Aliases: BenefitFlow, Benefit Flow, benefits app, benefits app project.

Likely requests concern the isolated BenefitFlow application project: product/workflow architecture, alpha implementation, research, testing, agent coordination, repository/bootstrap work, and moving the application toward a usable validated build. Use the project's own charter and accepted board state for exact product requirements.

### fold7-power-lab
Aliases: Fold7 Power Lab, Fold 7 Power Lab, Samsung Power Bootstrap.

Likely requests concern the Galaxy Z Fold7 Power Lab and its device/power engineering experiments. Use the local `PROJECT_MANIFEST.json`, `START_HERE.md`, and accepted board state for the exact technical objective rather than guessing from the repository name.

### warp-propulsion-lab
Aliases: Warp Propulsion Lab, warp-propulsion-lab, warp propulsion project.

Likely requests concern warp-propulsion research: theoretical analysis, models, research archives, code/tests, reproducibility, peer-review readiness, evidence separation, recursive research sessions, and preservation of findings/history.

### ai-behaviour-control-lab
Aliases: AI Behaviour Control Lab, AI Behavior Control Lab, ai-behaviour-control-lab, AI behavior project.

Likely requests concern controlled experiments in AI/agent behaviour, governance, swarm behaviour, safety/control mechanisms, validation, adversarial testing, and research into improved coordination or behavioural constraints.

## How to interpret shorthand

If the agent is already project-bound and the human says:

- `this project` -> use the bound project.
- `continue` -> recover the active task/handoff and continue the latest valid in-scope work.
- `do that` / `execute that` -> resolve the referent from the current message first, then current durable task/handoff state.
- `run the swarm` -> use the bound project's accepted swarm launch/bootstrap contract; do not invent extra authority or sessions.
- `update the packages` -> assess affected PRIMARY/MANAGER/RESEARCH packages and rebuild/validate those within authority.
- `check everything` -> interpret as a comprehensive in-scope review of current project state, not permission to cross project boundaries.
- `all projects` -> use the central registry and explicit cross-project governance; do not silently mutate every project.

If multiple materially incompatible referents remain after checking the relevant context layers and durable state, isolate the unsafe branch and ask only the minimum necessary question.

## Fresh-agent startup summary

1. Resolve exactly one project from strong evidence.
2. Bind role and execution mode.
3. Load local `AGENT_BOOTSTRAP.json`.
4. Load this project's `AGENT_CONTEXT_REFERENCE.md`.
5. Apply `IEP-CTX-001`: enumerate and reconcile relevant available context layers before declaring anything missing or asking for repetition.
6. Apply `IEP-MEM-001`: enforce the external-only P1 swarm-memory boundary before reconstructing collective state.
7. Apply any currently active temporary directive explicitly referenced by this context reference; expired temporary directives are historical only.
8. Load all project-declared required bootstrap overlays.
9. Load MASTER_HANDOFF/current accepted Artifactory state and registered GitHub revision/backup evidence required by the local contract.
10. Recover the current human objective or active task from the layered context and authoritative durable state.
11. Check ownership, dependencies, collisions, versions, leases, approvals, and package compatibility.
12. Execute autonomously within authority.
13. Persist material state externally and consume relevant peer findings.
14. Continue until convergence or a true human gate.

## Safety boundary

Likely intent is never authority. If a request could belong to more than one project, use exact routing evidence and the registry. Semantic similarity alone cannot switch projects or authorize writes.
