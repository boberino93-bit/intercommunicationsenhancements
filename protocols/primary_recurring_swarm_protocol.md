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

#### Material context promotion

A material project update MUST be promoted into durable project state through the canonical AgentBus/state-delta path when an authorized persistence path is available. Material updates include, where applicable:

- user decisions, approvals, rejections, corrections, redirects, and cancellations;
- material objective or scope changes;
- review outcomes and consensus milestones;
- canonical artifact/revision changes;
- blockers, unblocks, failures, and recovery state;
- authoritative implementation or validation results;
- handoffs and ownership changes;
- material contradictions or newly resolved contradictions;
- any fact whose omission would cause another authorized agent to give a materially stale answer or take materially stale action.

Do NOT persist ordinary conversational filler, duplicated paraphrases, routine liveness chatter, secrets, credentials, unnecessary personal information, or content whose persistence/disclosure is not authorized.

Durable context promotion MUST preserve provenance, project scope, source event time where known, recording time, applicable revision/generation, supersession relationship, and evidence/reference pointers. A summary is not allowed to impersonate the original evidence object.

#### Context watermark

Each active or recurring agent SHOULD maintain a compact `CONTEXT_WATERMARK` containing the strongest available equivalents of:

```text
LAST_PROJECT_STATE_VERSION_SEEN
LAST_SWARM_STATE_VERSION_SEEN
LAST_MATERIAL_CONTEXT_EVENT_SEEN
LAST_DECISION_VERSION_SEEN
LAST_MESSAGE_OFFSET_SEEN
LAST_PROTOCOL_VERSION_SEEN
LAST_SYNC_TIME
```

At startup, resume, handoff acceptance, and before a continuity-sensitive answer or protected action, the agent MUST retrieve material state newer than the watermark plus any invalidation-critical history.

A continuity-sensitive interaction includes any request whose correctness depends on very recent project history, including requests equivalent to:

- "do you already know?";
- "I just told another agent/chat";
- "continue from where we left off";
- "what is the latest state?";
- "did the reviewers approve it?";
- or any action whose authority, target, revision, blocker, approval, or implementation plan may have changed since the last synchronization.

#### Synchronization order

When freshness matters, use approximately this order, subject to project-specific authority and availability:

1. current Project State Capsule / Swarm State Capsule;
2. material durable context/state deltas newer than the watermark;
3. current decisions, supersessions, review outcomes, handoffs, and blockers;
4. relevant recent canonical AgentBus messages;
5. current repository/artifact revision where applicable;
6. host-provided cross-conversation memory or recent-chat context as supplementary evidence;
7. current conversation.

The newest conversational statement may be operationally important, but it does not erase or silently supersede stronger canonical state without the appropriate governed transition.

#### Read-after-write and continuity degradation

When an agent persists a material context delta, it MUST verify the durable write/readback where the substrate supports verification. It MUST NOT claim that project-wide continuity has been updated merely because it intended to write or generated a record.

If material state cannot be persisted or freshness cannot be verified:

`CONTEXT_PERSISTENCE_UNVERIFIED -> CONTINUITY_DEGRADED`

The agent may continue safe conversational work, but MUST NOT claim complete cross-session awareness and MUST fail closed for any action whose correctness depends on the missing state.

#### Synchronization miss

If the user has to repeat a material project fact that already exists in canonical durable state, classify the event as a `CONTEXT_SYNC_MISS` rather than treating repetition as the normal retrieval mechanism.

On a `CONTEXT_SYNC_MISS`, the agent SHOULD:

1. retrieve the canonical record;
2. reconcile its local context;
3. advance its watermark;
4. avoid asking the user to reconstruct information already retrievable;
5. record the miss as continuity-quality telemetry when an authorized low-noise telemetry path exists.

A synchronization miss does not make the user's repeated statement less authoritative. It is evidence that the retrieval/freshness path needs improvement.

#### Noise control

This mechanism MUST NOT turn the durable message board into a transcript or heartbeat log. Persist transitions, not chatter. Prefer compact state deltas, superseding capsules, and pointers to evidence over full conversational duplication.

The target invariant is:

`MATERIAL_STATE_CHANGE -> DURABLE_PROMOTION -> VERIFIED_READBACK -> CURSOR_ADVANCE -> NEXT_AGENT_FRESH`

and:

`USER_AS_MEMORY = ARCHITECTURAL_FAILURE_MODE`

## 11. Re-entry to full normalization

Invoke full normalization only when a defined material trigger occurs, including a new ACTIVE_REQUIRED project, major architecture/schema/governance/routing/permission/concurrency/recovery change, systemic integrity incident, or explicit recertification request. Otherwise validate freshness/health and continue normal operation.

## 12. Smoke-test criterion

The recurring protocol passes its smoke test when an authorized fresh agent can reconstruct objective, project, role, authority, current revision, health, ownership, dependencies, and next action from durable state; replay material context newer than its watermark; correctly recover a material update made in another conversation without requiring the user to repeat it; safely suspend/resume across a dependency; reject stale/foreign mutation; honor redirect/pause/stop/stop-tree control; preserve useful partial state; reject blind scheduled respawn after intentional stop; and complete a bounded canary without hidden conversational memory.
