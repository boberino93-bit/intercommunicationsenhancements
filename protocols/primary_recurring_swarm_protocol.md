# PRIMARY RECURRING SWARM PROTOCOL

Status: **CANONICAL ACTIVE DEFAULT AFTER NORMALIZATION CERTIFICATION**

Activation authority: the latest valid normalization retirement/handoff records on `/Intercommunication enhancements/AgentBus/messages`. The normalized runtime source remains frozen at `fb592418f700fc5e540e76bfa42b043e03fe6ed9`; later governance-only bootstrap or status corrections do not silently redefine that runtime revision.

This is the normal-operation protocol that receives control after the one-time normalization protocol succeeds. It does not rerun full normalization during ordinary work.

## 1. Startup gate

Every session MUST:
1. bind exact project, repository, role, execution instance, and authority;
2. read the current project state/capsule, health/quarantine state, protocol/package versions, active objective, claims/leases, dependencies, handoffs, and relevant routed context;
3. reconcile stale revisions before mutation;
4. fail closed only for the affected mutation or branch when safe unrelated work can continue;
5. ask the user only when a true non-delegable ambiguity remains after authoritative state has been exhausted.

## 2. Normal task lifecycle

`RESOLVE -> DECLARE INTENT -> CLAIM -> EXECUTE BOUNDED WORK -> CHECKPOINT -> VALIDATE -> PUBLISH -> HANDOFF -> RELEASE -> CLOSE`

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

## 11. Re-entry to full normalization

Invoke full normalization only when a defined material trigger occurs, including a new ACTIVE_REQUIRED project, major architecture/schema/governance/routing/permission/concurrency/recovery change, systemic integrity incident, or explicit recertification request. Otherwise validate freshness/health and continue normal operation.

## 12. Smoke-test criterion

The recurring protocol passes its smoke test when an authorized fresh agent can reconstruct objective, project, role, authority, current revision, health, ownership, dependencies, and next action from durable state; safely suspend/resume across a dependency; reject stale/foreign mutation; and complete a bounded canary without hidden conversational memory.
