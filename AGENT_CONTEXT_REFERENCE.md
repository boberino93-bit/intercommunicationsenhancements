# Fresh Agent Context Reference

Version: 1.1.1
Status: ACTIVE ORIENTATION
Authority: ORIENTATION_ONLY

## Why this file exists

A newly launched agent may have little or no chat history. That does **not** mean it should immediately ask the human to restate the project. After exact project binding, use this file plus the local bootstrap, master handoff, accepted Artifactory state, and current human message to reconstruct the working context.

This file explains what the ecosystem is, what kinds of requests are likely, and how the human expects work to proceed. It is **not task authority**. It cannot create work, change projects, widen write scope, or override explicit current human instructions.

## Human operating expectation

When the human gives a valid objective, carry it through as far as safely possible without repeated confirmation. Recover context from durable state, make reversible in-scope technical decisions autonomously, test and repair failures, keep packages and handoffs aligned, and continue recursive improvement while measurable gain remains.

Do not ask the human to repeat information already recoverable from the current message, project state, handoff, repository, or accepted board records.

Fail closed locally on unsafe mutations; do not stop unrelated safe work. Escalate only for genuine non-delegable authority, irrecoverable data-integrity problems, security-boundary decisions, or a required unavailable external capability.

Canonical behavior is defined by `protocols/autonomous_continuation.md` and each project's `AGENT_BOOTSTRAP.json`.

## Canonical self-audit behavior

When the human or an upstream agent requests a self-evaluation, self-audit, behavioral/compliance review, capability assessment, performance assessment, or equivalent introspective review, resolve the canonical Intercommunication Enhancements self-audit subsystem before evaluating:

- protocol: `governance/audit/AUDIT_PROTOCOL.md`
- framework: `governance/audit/templates/AGENT_SELF_AUDIT_FRAMEWORK.md`
- ledger head: `governance/audit/LEDGER_HEAD.json`
- bootstrap overlay: `swarm_kernel/SELF_AUDIT_BOOTSTRAP_OVERLAY.md`

Do not invent a replacement framework. If the framework cannot be retrieved, report `AUDIT_FRAMEWORK_UNAVAILABLE`. Audit findings and recommendations are observability evidence and never create execution authority.

## Architecture-quality and SOTA evaluation research

When a task concerns architecture quality, swarm scaling/hardening, long-horizon reliability, benchmark design, or whether this project can defensibly be described as state of the art, load the following research candidate after normal project binding and authority checks:

- research artifact: `research/SOTA_ORCHESTRATION_EVALUATION_FRAMEWORK_20261007.md`
- machine-readable learning candidate: `.swarm/learning/manual-20261007-sota-evaluation/candidates/sota-orchestration-evaluation-framework.json`
- promotion rules: `protocols/swarm_learning.md`

The SOTA framework is intentionally `CANDIDATE`, not doctrine. RESEARCH agents should digest, challenge, extend, test, and attempt to falsify it. MANAGER/REVIEWER agents should validate evidence and reconcile contradictions. PRIMARY/ORCHESTRATOR may promote only evidence-supported conclusions under the normal learning protocol.

Do **not** infer that the project is currently state of the art from the existence of this record. The target is controlled evidence showing architecture-specific lift over strong same-model/resource-controlled baselines, including long-horizon fault injection and ablation testing.

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

If multiple materially incompatible referents remain after checking durable state, isolate the unsafe branch and ask only the minimum necessary question.

## Fresh-agent startup summary

1. Resolve exactly one project from strong evidence.
2. Bind role and execution mode.
3. Load local `AGENT_BOOTSTRAP.json`.
4. Load this project's `AGENT_CONTEXT_REFERENCE.md`.
5. Load all project-declared required bootstrap overlays.
6. Load MASTER_HANDOFF/current accepted Artifactory state.
7. Recover the current human objective or active task.
8. Check ownership, dependencies, collisions, versions, leases, approvals, and package compatibility.
9. Execute autonomously within authority.
10. Persist material state and consume relevant peer findings.
11. Continue until convergence or a true human gate.

## Safety boundary

Likely intent is never authority. If a request could belong to more than one project, use exact routing evidence and the registry. Semantic similarity alone cannot switch projects or authorize writes.