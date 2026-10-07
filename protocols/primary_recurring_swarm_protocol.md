# PRIMARY RECURRING SWARM PROTOCOL

Status: **CANONICAL ACTIVE DEFAULT AFTER NORMALIZATION CERTIFICATION**

Activation authority: the latest valid normalization retirement/handoff records on `/Intercommunication enhancements/AgentBus/messages`. The normalized runtime source remains frozen at `fb592418f700fc5e540e76bfa42b043e03fe6ed9`; later governance-only bootstrap or status corrections do not silently redefine that runtime revision.

This is the normal-operation protocol that receives control after the one-time normalization protocol succeeds. It does not rerun full normalization during ordinary work.

## 1. Startup gate

Every session MUST:
1. bind exact project, repository, role, execution instance, and authority;
2. read the current project state/capsule, health/quarantine state, protocol/package versions, active objective, claims/leases, dependencies, handoffs, and relevant routed context;
3. establish a cross-session context watermark and replay all material durable context deltas newer than that watermark before making continuity-dependent claims;
4. reconcile stale revisions before mutation;
5. fail closed only for the affected mutation or branch when safe unrelated work can continue;
6. ask the user only when a true non-delegable ambiguity remains after authoritative state has been exhausted.

A fresh chat or resumed session is not evidence that project state is fresh. Current conversational context is one input to synchronization, not the canonical persistence layer.

## 2. Normal task lifecycle

`RESOLVE -> SYNC DURABLE CONTEXT -> DECLARE INTENT -> CLAIM -> EXECUTE BOUNDED WORK -> PERSIST MATERIAL DELTA -> CHECKPOINT -> VALIDATE -> PUBLISH -> HANDOFF -> RELEASE -> CLOSE`

A status question or other inline control message is not cancellation unless it explicitly says stop, cancel, pause, or redirect.

## 3. Dependency and suspension lifecycle

When a dependency blocks work:
1. record the dependency;
2. persist an operational checkpoint containing objective, current base revision, assumptions, dependencies, next action, and unexecuted plan steps;
3. enter `SUSPENDED` rather than overwriting upstream work;
4. accept a durable handback carrying evidence and the resulting canonical revision;
5. reconcile against current canonical state;
6. invalidate stale unexecuted plan steps when the base changed;
7. resume only after required dependencies are validated.

## 4. Ownership and concurrency

Claims and leases are project-scoped, execution-instance-fenced, and temporary. Stale writes fail CAS. Dead/expired owners do not retain permanent authority. Recent changes MUST be checked against active ownership, claims, dependencies, and migration state before repair.

## 5. Project isolation and cross-project flow

Project isolation governs unauthorized mutation, not information. Cross-project mutation is deny-by-default. Sanitized, provenance-bearing summaries may be copied into a local ecosystem registry through approved exchange paths; doing so never grants mutation authority over the peer project.

## 6. Containment and recovery

Health states are `HEALTHY`, `DEGRADED`, `QUARANTINED`, and `RECOVERING`.
- Hard-stop conditions quarantine the affected project/branch before promotion.
- Quarantined or recovering state cannot be promoted as trusted ecosystem truth.
- Recovery requires explicit probes, hysteresis thresholds, and cooldown before rejoin.
- A local fault does not become a global shutdown when smaller containment is sufficient.

## 7. Recursive generations

Generation-scoped work rejects stale-generation mutation. Recursive descendants remain subordinate to the current objective, inherit project identity and no greater capabilities than their parent, and converge through bounded depth/width rather than spawning indefinitely.

## 8. Universal improvements

Project agents may propose evidence-backed universal improvements but may not silently rewrite universal architecture. Universal changes route through Intercommunications governance, review, versioning, isolated validation, canary, monitored promotion, and rollback semantics.

## 9. Evaluation and anti-Goodhart rules

Passive evaluation measures mission completion, user intervention, useful coordination effects, avoided duplicate work, recovery, and correctness. Message volume, agent count, token count, recursion depth, and raw activity are never authoritative success metrics. Evaluation remains observational and cannot become a competing control plane.

## 10. Scheduled and cold-start agents

Scheduled/cold-start agents must receive explicit project-bound launch context, validate it against the local contract before mutation, preserve occurrence identity across retry, and must not advance task state before bootstrap is ready.

### 10A. Post-normalization successor overlay

Normal-operation agents MUST also load `protocols/post_normalization_successor.md` and its machine-readable registry at `reliability/SUCCESSOR_CONTROL_REGISTRIES.json` before creating new research claims or performing a protected universal-governance consequence.

For research/cold-start work, the overlay requires a freshness-checked `PriorityFrontierSnapshot`, deterministic `get started` semantics, capability/data-boundary discovery, semantic launch identity before sharding, and `READ -> RECONCILE -> CLAIM -> EXECUTE` preflight ordering.

The overlay is additive and does not replace the existing control plane, ownership/lease/fencing model, v1.8 Reliability Kernel, v1.8.1 consequence gateway, or communication-awareness protocol. If overlay metadata conflicts with a stronger current canonical control, the stronger canonical control wins and the conflict must be surfaced rather than guessed away.

The historical normalization-retirement evidence remains contradictory in the repository. The current successor integration records that state as `HUMAN_ROOT_OVERRIDE_UNPROVEN`; it must not be presented as a recovered or newly verified retirement packet solely because the overlay is on `main`.

### 10B. Supervisory governance overlay

Every normal, scheduled, and cold-start swarm agent MUST also load `protocols/supervisory_governance.md` and `governance/SWARM_SUPERVISION_POLICY.json`.

The overlay adds machine-readable `REDIRECT`, `PAUSE`, `STOP`, and `STOP_TREE` lifecycle control, bounded control-state checks, useful-state preservation, and intentional-stop respawn suppression. The User remains highest authority; the MASTER is global/roaming for lifecycle supervision; PRIMARY agents govern only their own project trees. Global lifecycle supervision does not bypass existing project/capability/consequence gates for source or production mutation.

Before scheduled launch or replacement, reconcile intentional-stop state. A timer firing, stale liveness observation, or unfinished task is not authority to revive work whose `allow_respawn` state is false. A materially revised task may restart under User, MASTER, or authorized PRIMARY rules defined by the overlay.

Scheduled MASTER invocations remain global/Recents and must not inherit the project that caused a wake-up. Project-bound agents use the canonical ChatGPT Project mapping through the host adapter and must verify actual placement; absence of a host adapter is an external-effect limitation, not permission to claim assignment success.

### 10C. Cross-session durable freshness synchronization

The swarm MUST treat conversation context, host memory, recent-chat summaries, and model recollection as convenience caches rather than the authoritative project database.

Therefore:

`CURRENT_CHAT != CURRENT_PROJECT_STATE`

`MODEL_MEMORY != CANONICAL_PROJECT_STATE`

`RECENT_CHAT_VISIBILITY != DURABLE_CONTINUITY`

`MATERIAL_USER_UPDATE -> DURABLE_CONTEXT_DELTA`

The purpose of this rule is to prevent a newly opened or concurrently active conversation from being seconds or minutes behind a material fact that another conversation already learned.

A material project update MUST be promoted into durable project state through the canonical AgentBus/state-delta path when an authorized persistence path is available. Material updates include user decisions, material objective or scope changes, review outcomes, canonical artifact/revision changes, blockers, failures/recovery state, authoritative implementation or validation results, handoffs/ownership changes, contradictions, and any fact whose omission would cause materially stale action.

Do NOT persist conversational filler, duplicated paraphrases, liveness chatter, secrets, credentials, unnecessary personal information, or unauthorized content. Durable promotion MUST preserve provenance, project scope, source event time where known, recording time, revision/generation, supersession, and evidence pointers.

Each active or recurring agent SHOULD maintain a compact `CONTEXT_WATERMARK` including strongest available project/swarm state version, last material event, decision version, message offset, protocol version, and last sync time.

At startup, resume, handoff acceptance, and before a continuity-sensitive answer or protected action, retrieve material state newer than the watermark plus invalidation-critical history.

When freshness matters, prefer current state capsules, material durable deltas, decisions/supersessions/handoffs/blockers, canonical AgentBus messages, current repository/artifact revision, then host cross-conversation memory and current conversation as supplementary evidence.

When an agent persists a material context delta, verify durable write/readback where supported. If persistence/freshness cannot be verified, mark `CONTINUITY_DEGRADED`; safe conversational work may continue but actions depending on missing state fail closed.

If the user must repeat a material fact already in canonical durable state, classify `CONTEXT_SYNC_MISS`, retrieve/reconcile the canonical record, advance the watermark, avoid making the user reconstruct retrievable state, and record low-noise telemetry where authorized.

Persist transitions, not chatter. Target invariant:

`MATERIAL_STATE_CHANGE -> DURABLE_PROMOTION -> VERIFIED_READBACK -> CURSOR_ADVANCE -> NEXT_AGENT_FRESH`

### 10D. Mission and priority synchronization overlay

Every normal, scheduled, resumed, recovered, and cold-start swarm agent MUST also load `protocols/swarm_synchronization.md`.

Before substantive work, the agent MUST synchronize to the current project mission, priority stack, authoritative decision state, relevant task/checkpoint state, dependencies, contradictions, and applicable ownership/claim/lease/fencing state. It must select the highest-value work it is authorized and capable of advancing, maintain bounded focus, and publish material deltas that could change another agent's decisions.

Agents MUST re-synchronize on material mission, priority, dependency, ownership, authorization, contradiction, incident, handoff, resume, or canonical-revision changes. A stale checkpoint or fresh chat is not sufficient state.

The synchronization overlay is coordination only. It cannot create authority, ownership, scheduler authority, release authority, or deployment authority. Heartbeat remains observational. Claims/leases/fencing remain ownership authority. Existing authority-authentication, single-use mutation authorization, project work control, supervisory control, containment, and project isolation remain stronger gates.

When material state drift, ownership drift, or authority drift is detected before protected mutation, the affected mutation MUST stop, useful work must be checkpointed, authoritative state must be reloaded and reconciled, and all applicable claim/lease/fencing/authorization state must be revalidated before proceeding.

The swarm SHOULD optimize for critical-path mission progress rather than raw activity. P0 integrity/safety/security/authority and P1 critical-path work take precedence over lower-value work subject to valid authority, dependencies, capabilities, holds, containment, and ownership. Accidental duplicate work should be collapsed; intentional independent validation/red-team work must state its purpose.

## 11. Re-entry to full normalization

Invoke full normalization only when a defined material trigger occurs, including a new ACTIVE_REQUIRED project, major architecture/schema/governance/routing/permission/concurrency/recovery change, systemic integrity incident, or explicit recertification request. Otherwise validate freshness/health and continue normal operation.

## 12. Smoke-test criterion

The recurring protocol passes its smoke test when an authorized fresh agent can reconstruct objective, project, role, authority, current revision, health, ownership, dependencies, priorities, contradictions, and next action from durable state; replay material context newer than its watermark; recover a material update made in another conversation without requiring repetition; detect stale/duplicate/priority-drift work; safely suspend/resume across a dependency; reject stale/foreign mutation; honor redirect/pause/stop/stop-tree control; preserve useful partial state; reject blind scheduled respawn after intentional stop; and complete a bounded canary without hidden conversational memory.
