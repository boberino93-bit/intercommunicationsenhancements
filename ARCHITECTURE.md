# Intercommunications Architecture

## Purpose

Intercommunications Enhancements is the reference hardening project for the Organization Agent Mesh. It makes simultaneous unrelated AI project teams safer by construction: project identity is an authorization boundary, ordinary execution state is isolated by default, and deployment packages are traceable to one exact source revision.

Current target: **framework 1.6.0-alpha.1 / protocol 2.4.0-alpha.1**.

## Identity-first bootstrap

Execution begins with `BOOTSTRAP_ORDER.json`. Launch origin is resolved first. Interactive runs validate current human project intent; scheduled project-bound runs validate the captured launch context against the target local contract; generic unbound runs remain read-only until universal routing resolves exactly one project. `PROJECT_IDENTITY_LOCK.json` and the ordinary local authorization gates still follow. Handoffs, queues, forums, accepted state, recent context, working-directory state, and semantic similarity are not mutation authorization inputs.

Canonical operations resolve `project_id -> repository/workspace -> agent_id -> agent_instance_id -> task/resource -> capability`.

`ProjectBinding` is immutable. Lifecycle is `UNBOUND -> BOUND -> INITIALIZED -> ACTIVE -> DRAINING -> TERMINATED`. Only an `ACTIVE` bound `AgentSession` may authorize mutation. Mutation APIs do not accept a caller-supplied project string as proof of identity; destination-side code revalidates the bound session.

## Scheduled agent launch, project context and provider admission

Dynamic scheduled work is project-bound at configuration time rather than rediscovered from topic at execution time. `ScheduledTaskRoute.from_project_contract(...)` captures the exact project ID, role, routing-contract version, authoritative forum/artifact namespaces, repository identity/ID when bound, and bootstrap paths from `AGENT_BOOTSTRAP.json`. `render_scheduler_prompt(...)` serializes that state into a machine-readable `ORG_AGENT_MESH_PROJECT_LAUNCH_CONTEXT` block for the future run.

The launch block is **routing evidence, not mutation authority**. The future run must compare it with the target local contract before mutation, then continue through the identity lock, role/capability checks, master handoff, communication-awareness and active-session gates. Missing, malformed or conflicting scheduled context is fail-closed and may not fall back to topic similarity or silently switch projects. The global entrypoint recognizes a verified scheduled launch as exact routing evidence and skips fuzzy project discovery only after local-contract agreement.

Scheduled execution has a separate pre-provider lifecycle because provider throttling can occur before any agent code executes. The reference state machine is `PENDING -> ADMITTED -> PROVIDER_ACCEPTED -> BOOTSTRAP_READY -> COMPLETED`, with `RETRY_WAIT` and `TERMINAL_FAILURE` branches. `TOO_MANY_REQUESTS`, rate limiting, temporary provider unavailability and timeout before bootstrap are retryable **launch** failures, not project task failures. The logical task may not advance merely because a scheduler fired; project task execution may advance only after `BOOTSTRAP_READY`.

`org_agent_mesh.launch_admission` is the reference scheduler/dispatcher admission implementation. It provides bounded concurrent starts, minimum start spacing, deterministic launch staggering, bounded exponential backoff with deterministic jitter, retry-attempt caps and occurrence identity preservation. `deterministic_launch_offset_seconds(project_id, task_id, window_seconds)` spreads recurring jobs across an admission window to reduce synchronized wake-ups.

The architecture is explicit about the host boundary: provider admission must execute **before** model invocation to prevent a thundering herd. When the actual hosting scheduler exposes such a hook, the admission controller belongs there. When it does not, project configuration must use deterministic staggering plus retry/reconciliation; an agent cannot retrospectively prevent or self-retry a request that was rejected before the agent started. The project therefore does not claim control over provider infrastructure it cannot execute ahead of model invocation.

Retries preserve the same task/occurrence/idempotency identity. Duplicate or late starts are reconciled rather than opening a second independent mutation stream. Provider-throttle and launch-context incidents are recorded as observable evidence and may enter the normal swarm-learning pipeline, but do not bypass validation or doctrine-promotion rules.

Normative behavior is defined in `protocols/scheduled_agent_launch.md`; the route and context schemas are `schemas/scheduled_task_route.schema.json` and `schemas/scheduled_launch_context.schema.json`.

## Canonical identifiers

Project and resource IDs are validated canonical identifiers. The runtime does not lossily sanitize IDs into keys; invalid inputs are rejected instead of rewritten into potentially colliding aliases. Qualified keys are injective within the accepted identifier language: `project_id::resource_id`.

## Capabilities and child agents

Authority tier and capability set are separate. `PROJECT_IDENTITY_LOCK.json` is authoritative role-capability policy packaged with every role. Children inherit parent project/repository/root/protocol identity and receive a fresh execution-instance ID. A child may inherit the same capability set or a strict subset; escalation is rejected.

## Messaging and delivery

Protocol 2.4 requires explicit source/destination project identity, sender agent/execution-instance identity, correlation/causation, idempotency and expiry. The internal bus has no cross-project override. Publication requires an `ACTIVE` session with `PUBLISH_MESSAGE`, and claimed sender identity must match it.

Message persistence uses atomic exclusive creation keyed by SHA-256 of `(project_id, idempotency_key-or-message_id)`. Concurrent retries therefore cannot both become effective accepted messages. Delivery distinguishes `RECEIVED`, `ACCEPTED`, `STARTED`, `COMPLETED`, `FAILED`, and `REJECTED`; retries are bounded and unsafe/expired input is quarantined as non-executable evidence.

## Tasks, artifacts, leases and state

`TaskRegistry` provides project-scoped task identity, execution-instance ownership and expected-version transitions. `ArtifactRegistry` records ownership/provenance/content hashes and expected-version replacement. `AuditLedger` records project, logical agent, execution instance, task/message/resource context, operation, result and before/after versions.

Collision-sensitive work uses project-qualified expiring leases owned by a specific execution instance. Claim/renew/release authority comes from the bound session; restarted instances cannot inherit stale locks. Stale-sensitive mutable state uses compare-and-set.

Projects have independent `ACTIVE`, `DRAINING`, and `PAUSED` lifecycle state. Pausing one project does not stop unrelated projects.

`DurableRecordBackend` defines the durable create/read/CAS/versioned-delete/list contract. `SQLiteRecordBackend` is the first crash-durable reference implementation: it uses transactional project-qualified records, WAL, FULL synchronous persistence, deterministic JSON checksums and schema-version fencing. `DurableVersionedStateStore` and `DurableLeaseRegistry` preserve the existing bound-session authorization, execution-instance ownership, expiry/recovery and CAS semantics across process restarts. Their tests exercise reopen recovery, concurrent writers, competing lease claimants, stale execution instances, cross-project key collisions, tamper detection and concurrent expired-lease reclamation.

The remaining task, artifact, audit, project-registry and delivery registries are thread-safe in-process references. A distributed or multi-node adapter is conformant only if it preserves equivalent atomicity, ownership, expiry/recovery, isolation and CAS semantics; otherwise it must fail closed. The SQLite backend is a single-node durability reference and is not presented as a distributed-consensus service.

## Swarm learning and organizational memory

The architecture treats each completed agent run as a potential source of **cumulative operational intelligence**, not as model-weight training. The swarm improves by persisting evidence, validating reusable conclusions, and selectively promoting high-confidence lessons into bootstrap-loadable operating doctrine. The normative rules are defined in `protocols/swarm_learning.md`.

Learning has three authority layers:

1. **Raw experience** — append-only run evidence, failures, measurements, experiments, diagnostics and candidate lessons. It is non-authoritative.
2. **Validated knowledge** — reusable conclusions that survived an explicit validation method appropriate to their risk and scope.
3. **Operating doctrine** — concise, versioned, reversible instructions and heuristics approved for routine inheritance by later agents.

Candidate lessons move through `OBSERVED -> CANDIDATE -> VALIDATED -> DOCTRINE`, with `REJECTED`, `SUPERSEDED`, and `EXPIRED` as non-promoted terminal or replacement states. Repetition alone never promotes a lesson. Higher-risk lessons affecting identity, authorization, project boundaries, destructive mutation, security, cross-project exchange, or release gates require reviewer validation and cannot auto-promote. Doctrine integration remains an ORCHESTRATOR/PRIMARY responsibility unless a narrower project policy explicitly delegates a low-risk class.

Every promoted lesson retains project/run/agent/task provenance, evidence references, scope, confidence semantics, validation method, reviewer/promoter identity and supersession/expiry metadata. Confidence never substitutes for evidence or promotion state. Contradictory validated lessons require reconciliation rather than last-writer-wins replacement.

Runtime learning state is project-local and may be sharded under `.swarm/learning/<global_run_id>/{experience,candidates,validation}/...`. Cross-project learning remains observation-only unless the ordinary explicit exchange path is approved; a project may not write learning state or doctrine into a peer repository. Slack may carry notifications or pointers but is never canonical learning state.

Bootstrap intentionally loads **doctrine first, scoped validated knowledge second, and raw history only on demand**. This prevents unvalidated history from becoming accidental policy and limits context growth as the swarm ages. Current human intent, identity/capability controls and newer authoritative protocols always outrank inherited doctrine.

Before normal handoff or termination, agents should persist an idempotent learning checkpoint containing material outcomes, failures/retries, evidence-backed lesson candidates, doctrine confirmations or contradictions, efficiency observations where measurable, and unresolved validation needs. `NO_MATERIAL_LEARNING` is a valid checkpoint; agents must not invent lessons merely to satisfy the protocol.

The system may measure success rate, first-pass completion, repeated-failure recurrence, rework, handoff defects, lease conflicts, candidate-validation yield, doctrine rollback/supersession and task latency where reliably observable. These metrics are diagnostic evidence only and never bypass review or authorization gates.

The intended system property is that later agents begin with better validated procedures and fewer repeated mistakes than earlier agents while retaining auditability, reversibility, bounded context, project isolation, and explicit human/project authority.

## Cross-project operational intelligence and exchange

Ordinary internal channels never cross projects. Base exchange requires an `ACTIVE` source-project session, `CROSS_PROJECT_EXCHANGE`, exact requesting-agent/session agreement, distinct projects, explicit approval, bounded artifact scope/purpose, and valid creation/expiry.

Above that transport gate, `protocols/cross_project_operational_intelligence.md` provides the semantic federation layer. It separates passive knowledge, discovery, expertise/capability/managerial awareness, routing requests and active execution. Cross-project intelligence metadata always carries `authority_conveyed=false` and can never grant peer mutation or local capability inheritance.

`OperationalIntelligenceRegistry` maintains a consumer-project-owned copy-by-value discovery index of sanitized peer themes, expertise, capability references, availability and provenance. Expired entries are not discoverable and unknown fields fail closed. The registry is advisory/read-only for discovery and does not assign work.

Cross-project routing uses explicit correlation and lineage. `validate_routing_lineage()` rejects cycles and repeated project visits. A target project must independently accept or decline the request. Acceptance and later redirect/supersession state are represented by explicit non-authoritative receipts; `ACCEPTED` creates no active-participation claim by itself.

`SanitizedSnapshotBridge` is the durable reference bridge. Source export validates the approved exchange and stores an immutable, digest-bound sanitized snapshot under the source project. Destination import revalidates destination identity/capabilities, expiry and classification, then writes a copy-by-value evidence record only under the destination project. Imported records are explicitly `accepted_state=false` and `authority_conveyed=false`; there is no automatic knowledge/doctrine/assignment promotion path.

This design intentionally avoids a global mutable Project Intelligence Bus. Federation is achieved by bounded, explicit, copy-by-value exchange plus project-local acceptance.

## Packaging and dependency closure

`packaging/agent_package_dependencies.json` is authoritative package dependency closure. Shared inputs include all `org_agent_mesh/*.py`, `schemas/*.json`, and `protocols/*.md`, preventing new runtime components from silently escaping deployment ZIPs.

Each role ZIP contains manifest v3 with project/repository identity, role/tier, capabilities, framework/protocol/package versions, exact source commit, commit-derived deterministic build time, dependency-map hash, exact component inventory and SHA-256 hashes. Build emits PRIMARY, MANAGER and RESEARCH as one release set plus `release-set.json` archive hashes.

Verification recomputes dependency closure from repository source, compares every packaged component to source, checks role isolation and one coordinated revision. ZIP metadata is deterministic; CI builds twice and rejects non-reproducible archives.

## Release gate

A revision is release-complete only after `tests -> exact-SHA build -> package verification -> independent rebuild -> reproducibility comparison -> coordinated artifact publication`.

Doctrine changes that alter packaged agent behavior are subject to this same release gate before they are deployment-complete.

## Remaining production layers

The alpha still needs distributed/multi-node durable adapters for the complete registry set, persistent organization-wide lifecycle/global observability, broker-specific durable acknowledgement transport, cryptographic cross-host attestation for sanitized snapshot packages when crossing separate trust domains, a concrete durable learning-registry implementation that enforces the promotion lifecycle described above, and host/scheduler integration that can enforce provider admission before model invocation. Those are production/distribution layers, not missing semantics in the completed reference cross-project intelligence federation.
