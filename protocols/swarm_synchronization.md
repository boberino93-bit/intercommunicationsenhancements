# Swarm Synchronization Protocol

Status: **CANONICAL ACTIVE GOVERNANCE**  
Policy ID: **IEP-SYNC-001**  
Version: **0.1**  
Project: **Intercommunication Enhancements**

## 1. Purpose

The swarm must remain synchronized around the work that matters most without forcing every agent to reason identically or flooding the system with coordination traffic.

The target is shared operational alignment around:

- current mission and phase;
- accepted priority ordering;
- authoritative project and swarm state;
- dependencies, blockers, contradictions, incidents, and validation state;
- ownership/claim/lease/fencing state;
- current completion criteria;
- material changes since the last synchronization point.

Synchronization exists to reduce mission drift, stale-state work, accidental duplicate work, conflicting mutation, priority inversion, forgotten dependencies, invalid handoffs, silent blockers, and loss of critical-path focus.

## 2. Architectural invariants

This protocol extends the existing control plane and MUST NOT create a competing scheduler, AgentBus, project registry, authority store, claim/lease/fencing system, persistent leadership role, release authority, deployment authority, or mutation authority.

Existing stronger controls win.

```text
ROLE determines authority class.
CAPABILITY determines permitted action classes.
CLAIM / LEASE / FENCING determines current mutation ownership.
MODE determines operational function.
HEARTBEAT reports presence/liveness only.
SYNCHRONIZATION STATE informs coordination only.
```

Synchronization MUST reuse canonical state, AgentBus/current-successor, checkpoint, claim/lease/fencing, scheduler/task-distribution, audit, supervisory, authority-authentication, mutation-authorization, and project-isolation mechanisms.

## 3. Shared Situation Model

Each participating project SHOULD expose a compact Shared Situation Model (SSM) derived from authoritative existing records rather than a new database.

Minimum logical fields:

```yaml
situation_model_version:
project_id:
project_revision:
last_material_update:
mission:
current_phase:
completion_definition:
priority_stack:
critical_path:
active_tasks:
active_claims_leases:
blocked_tasks:
dependency_graph:
accepted_decisions:
accepted_facts:
provisional_findings:
open_contradictions:
open_questions:
active_risks:
active_incidents:
pending_validations:
pending_handoffs:
pending_authorizations:
recent_material_deltas:
next_expected_checkpoints:
```

The SSM MUST distinguish authoritative, accepted, provisional, hypothesis, disputed, stale, and superseded state. Appearance in the SSM does not upgrade epistemic or authority status.

## 4. Priority discipline

Default priority classes are:

```text
P0 — integrity / safety / security / authority
P1 — current critical path
P2 — dependency unblock / failure recovery
P3 — required validation / reconciliation
P4 — high-value parallel work
P5 — exploration / improvement / optional research
P6 — cosmetic / low-leverage
```

Default ordering is `P0 > P1 > P2 > P3 > P4 > P5 > P6`, subject to valid authority, dependency ordering, capability availability, project holds, containment, and ownership.

A P2 blocker that gates P1 may become immediate focus. Required validation before promotion outranks unrelated parallel work. P5/P6 work yields when P0-P3 capacity is constrained.

## 5. Focus Contract and WIP

Every substantive agent SHOULD maintain a compact Focus Contract containing:

```yaml
agent_instance_id:
project_id:
role:
mode:
current_task_id:
current_priority_id:
mission_link:
why_this_matters_now:
expected_output:
current_dependency:
current_owner_or_claim:
next_checkpoint_condition:
stop_or_replan_conditions:
```

Before protected or expensive work the agent must be able to answer what the project is trying to achieve, what highest-value permitted work it can advance, who owns the target, what dependency is being satisfied or created, what evidence proves value, and what condition causes stop/handoff/replan.

Default WIP discipline is one primary active task plus at most two tightly coupled supporting subtasks. Preemption requires a checkpoint when practical.

## 6. Synchronization triggers

Agents MUST re-synchronize at least on:

- bootstrap, resume, recovery, handoff acceptance, or stale-session re-entry;
- before protected/shared mutation;
- material mission or priority change;
- material dependency or blocker change;
- claim/lease/fencing or ownership change;
- important contradiction discovery or resolution;
- relevant authorization change;
- relevant canonical revision change;
- release/deployment state change;
- incident/failure/containment transition;
- substantive handoff or completion.

Heartbeat/pulse may detect liveness but never confers ownership.

## 7. Synchronization handshake

Use this logical sequence, with strictness proportional to consequence:

```text
VERIFY identity + project + role + capability
READ mission + priority stack
READ accepted/superseded decisions
READ relevant claims/leases/fencing
READ task/checkpoint/handoff state
READ blockers/contradictions/incidents
COMPARE local assumptions to authoritative state
DISCARD or quarantine stale assumptions
SELECT highest-value permitted work
PUBLISH intent when coordination visibility is required
CLAIM where ownership is required
EXECUTE bounded work
```

## 8. Material-delta publication

Publish transitions that could alter another agent's decision, not routine tool chatter. Material deltas include confirmed evidence, rejected important hypotheses, contradictions, dependency changes, critical blockers, critical-path completion, ownership changes, authorization changes, canonical revision changes, validation failures, release/deployment changes, high-severity risk, handoff changes, and priority changes.

Material-delta records SHOULD preserve project, source agent/task/revision, timestamp, summary, materiality, affected priorities/tasks/dependencies, state-before/state-after, confidence, provenance, acknowledgement requirement, and revalidation requirement.

## 9. Drift detection

Detect at minimum:

- `MISSION_DRIFT` — current work no longer materially supports accepted mission;
- `PRIORITY_DRIFT` — lower-priority work continues while higher-priority actionable work is available;
- `STATE_DRIFT` — reasoning uses stale revision/decision/handoff/dependency state;
- `OWNERSHIP_DRIFT` — local ownership belief conflicts with claims/leases/fencing;
- `DUPLICATION_DRIFT` — accidental overlapping work without an intentional redundancy purpose;
- `AUTHORITY_DRIFT` — planned action exceeds role/capability/project/authorization scope;
- `EVIDENCE_DRIFT` — active conclusion rests on superseded, contradicted, or downgraded evidence.

Response pattern:

```text
DETECT -> CLASSIFY -> CONTAIN -> CHECKPOINT -> RELOAD -> RECONCILE -> REPLAN -> RESUME/HANDOFF
```

For protected mutation, ownership drift, authority drift, or material state drift MUST stop the affected mutation until current state, claim/lease/fencing, and authorization are revalidated.

## 10. Duplication and contradiction handling

Overlapping work must be classified as accidental duplication, independent validation, red-team duplication, parallel hypothesis test, race-to-unblock, or required multi-source corroboration.

Accidental duplication should be collapsed while preserving useful findings. Intentional redundancy must state its purpose.

Material contradictions must not be averaged away. Record both claims and provenance, freeze the affected conclusion as unresolved, identify decision impact, gather discriminating evidence, then accept/reject/partition/escalate and update shared state. Contradictions affecting protected mutation, release, security, authority, or irreversible action block the affected action unless uncertainty is explicitly governed.

## 11. Dependency-aware retasking

When the dependency graph changes, reevaluate affected work:

```text
DEPENDENCY SATISFIED -> wake blocked downstream work
DEPENDENCY INVALIDATED -> suspend/revalidate downstream work
CRITICAL BLOCKER FOUND -> redirect suitable authorized capability toward unblock
SHORTER VALIDATED CRITICAL PATH FOUND -> reprioritize
```

Retasking does not widen authority and must respect current scheduler, project work controls, supervisory controls, and claims/leases/fencing.

## 12. Role responsibilities

### PRIMARY

PRIMARY remains accountable for project coherence within authorized scope: mission/phase, priority stack, strategic convergence, acceptance/rejection of material conclusions, protected-change gating, cross-project conflict routing, and controlled re-synchronization after major direction change.

### MANAGER

MANAGER amplifies coordination but is not a new authority layer. It should identify stalled critical-path work, accidental duplication, stale assumptions, contradictions, incomplete handoffs, and blocked agents; consolidate material deltas; recommend reprioritization; request evidence/validation; and escalate authority decisions to PRIMARY.

### RESEARCH

RESEARCH loads mission/priority context, declares the question/hypothesis, publishes decision-relevant evidence early, preserves provenance, distinguishes evidence from inference, redirects when the question loses materiality, and hands off implementation recommendations without inferring protected mutation authority.

Operational synchronization aligns objectives and state; it does not force epistemic consensus.

## 13. Attention and acknowledgement control

Synchronization must reduce context load rather than create chatter. Do not broadcast routine tool calls. Prefer state deltas, deduplicate equivalent events, collapse safe bursts into checkpoints, and route only relevant material to affected agents.

Acknowledgement classes MAY be:

`ACK_NONE`, `ACK_PASSIVE`, `ACK_REQUIRED_BEFORE_NEXT_CHECKPOINT`, `ACK_REQUIRED_BEFORE_MUTATION`, `ACK_REQUIRED_IMMEDIATE`.

Acknowledgement proves awareness only; it never grants authority.

## 14. Staleness, checkpoint, and handoff

Decision-relevant state SHOULD include source revision/state version, update time, recheck condition, and supersession metadata. Revalidate when relevant revisions, decisions, ownership, dependencies, handoffs, authorizations, or material events change.

A synchronization-safe checkpoint SHOULD capture objective, completed work, findings, artifacts, validation state, questions, blockers, dependencies, claims/leases, next best action, resume requirements, and state requiring revalidation.

A substantive handoff SHOULD include task identity, why it matters, current priority, source revision, completed work, evidence/provenance, contradictions, blockers/dependencies, relevant ownership state, exact next action, stop/replan conditions, and required revalidation. Handoff never grants mutation authority.

## 15. Mission-change barrier and critical-path loop

A material Human Root or valid PRIMARY mission/priority change SHOULD emit a logical `MISSION_CHANGE` barrier. Affected agents checkpoint, read the new mission/priorities, classify current work as continue/modify/pause/abandon/handoff, publish the resulting transition, and resume. Unaffected work may continue.

At material checkpoints orchestration SHOULD ask:

1. What is the current critical path?
2. What blocks it?
3. Which active agent is best positioned and authorized to remove the blocker?
4. Is lower-value work consuming capacity while that blocker is actionable?
5. Is validation/reconciliation now limiting rather than discovery?
6. Has enough evidence accumulated to converge?

## 16. Exploration budget

Projects SHOULD distinguish mission-critical, validation, and exploration capacity. Exploration may continue when critical-path work is saturated, leverage is plausible, required ownership is not consumed, P0-P3 work is not delayed, and a stop condition exists. Exploration yields when critical-path or recovery capacity is constrained.

## 17. Synchronization health

Metrics are observational only. Useful measures include priority coverage, Focus Contract freshness, stale-state detections, accidental duplication, blocker surfacing time, material-delta awareness time, contradiction age, handoff reconstruction success, blocked-task age, priority inversion, stale-ownership mutation rejects, mission-change abandonment, message-to-material-delta ratio, critical-path throughput, and rework from stale assumptions.

Raw message volume, agent count, heartbeat count, or activity is not success.

## 18. Required adversarial scenarios

Validation SHOULD cover at least: simultaneous duplicate starts; stale checkpoint resume; live priority change; dependency invalidation; claim/lease transfer or expiry; contradictory findings; Manager authority overreach; heartbeat/lease disagreement; stale handoff acceptance; project-local result miscast as universal; global protocol change requiring revalidation; exploration persisting while critical-path work is blocked; sync-message overload; and stale overwrite of newer accepted state.

## 19. Rollout phases

1. **Observe** — read-only situation aggregation, Focus Contracts, material-delta events, drift diagnostics.
2. **Advise** — warnings for priority, duplication, stale-state, contradiction, and dependency drift.
3. **Guard** — protected mutation requires relevant synchronization/revalidation while reusing existing hard controls.
4. **Adaptive retasking** — authorized orchestration may use validated deltas to reprioritize/wake/suspend work without creating authority.
5. **Global validation** — adversarial multi-agent, restart, scheduler, handoff, and split-brain tests before any broader runtime claim.

Repository promotion establishes canonical source governance only. It does not by itself prove every external runtime host, scheduler, backend, AgentBus adapter, or deployed agent has consumed the new protocol.

## 20. Bootstrap requirement

Before substantive work, every agent must synchronize to the current project mission, priority stack, authoritative decision state, relevant task/checkpoint state, dependencies, contradictions, and applicable ownership/claim/lease/fencing state.

The agent must select the highest-value work it is authorized and capable of advancing, maintain bounded focus, and publish material state changes that could alter another agent's decisions.

Agents must re-synchronize on material mission, priority, dependency, ownership, authorization, contradiction, incident, handoff, resume, or canonical-revision changes.

Heartbeat/presence is observational only and never grants ownership or mutation authority.

If material state, ownership, or authority drift is detected before protected mutation, stop that mutation, checkpoint useful work, reload authoritative state, reconcile, and revalidate before proceeding.

The swarm optimizes for critical-path mission progress rather than raw activity, subject to valid authority, dependencies, capabilities, project holds, containment, and ownership.

## 21. Acceptance invariant

The target is not `EVERY_AGENT_KNOWS_EVERYTHING`.

The target is:

```text
EVERY AGENT KNOWS ENOUGH OF THE CURRENT AUTHORITATIVE STATE
TO CHOOSE THE RIGHT NEXT ACTION,
AVOID INVALID OR ACCIDENTALLY DUPLICATE WORK,
SURFACE MATERIAL CHANGES,
AND RE-SYNCHRONIZE WHEN THE WORLD CHANGES.
```
