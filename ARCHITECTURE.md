# Intercommunications Architecture

## Purpose

Intercommunications Enhancements is the reference hardening project for the Organization Agent Mesh. It makes simultaneous unrelated AI project teams safer by construction: project identity is an authorization boundary, ordinary execution state is isolated by default, and deployment packages are traceable to one exact source revision.

Current target: **framework 1.6.0-alpha.1 / protocol 2.4.0-alpha.1**.

## Identity-first bootstrap

Execution begins with `BOOTSTRAP_ORDER.json`. Current human project intent is validated first, then `PROJECT_IDENTITY_LOCK.json`. Handoffs, queues, forums, accepted state, recent context, working-directory state, and semantic similarity are not authorization inputs.

Canonical operations resolve `project_id -> repository/workspace -> agent_id -> agent_instance_id -> task/resource -> capability`.

`ProjectBinding` is immutable. Lifecycle is `UNBOUND -> BOUND -> INITIALIZED -> ACTIVE -> DRAINING -> TERMINATED`. Only an `ACTIVE` bound `AgentSession` may authorize mutation. Mutation APIs do not accept a caller-supplied project string as proof of identity; destination-side code revalidates the bound session.

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

## Cross-project exchange

Ordinary internal channels never cross projects. Exchange requires an `ACTIVE` source-project session, `CROSS_PROJECT_EXCHANGE`, exact requesting-agent/session agreement, distinct projects, explicit approval, bounded artifact scope/purpose, and valid creation/expiry. The validator is implemented; a durable sanitized export/import bridge remains future production work.

## Packaging and dependency closure

`packaging/agent_package_dependencies.json` is authoritative package dependency closure. Shared inputs include all `org_agent_mesh/*.py`, `schemas/*.json`, and `protocols/*.md`, preventing new runtime components from silently escaping deployment ZIPs.

Each role ZIP contains manifest v3 with project/repository identity, role/tier, capabilities, framework/protocol/package versions, exact source commit, commit-derived deterministic build time, dependency-map hash, exact component inventory and SHA-256 hashes. Build emits PRIMARY, MANAGER and RESEARCH as one release set plus `release-set.json` archive hashes.

Verification recomputes dependency closure from repository source, compares every packaged component to source, checks role isolation and one coordinated revision. ZIP metadata is deterministic; CI builds twice and rejects non-reproducible archives.

## Release gate

A revision is release-complete only after `tests -> exact-SHA build -> package verification -> independent rebuild -> reproducibility comparison -> coordinated artifact publication`.

Doctrine changes that alter packaged agent behavior are subject to this same release gate before they are deployment-complete.

## Remaining production layers

The alpha still needs distributed/multi-node durable adapters for the complete registry set, persistent organizational registry/global observability, a full sanitized cross-project bridge, broker-specific durable acknowledgement transport, and a concrete durable learning-registry implementation that enforces the promotion lifecycle described above. Those are future layers, not current enforcement claims.
