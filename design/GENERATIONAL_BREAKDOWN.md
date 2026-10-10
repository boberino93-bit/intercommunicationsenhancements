# Intercommunications Enhancements — Generational Architecture Breakdown

Status: DESIGN ANALYSIS — NON-AUTHORITATIVE

Baseline reviewed: `main` at `2dbc399307277ba2f003ef27118cbd4e840e8ba5`
Validated release baseline: framework `1.6.0-alpha.1`, protocol `2.4.0-alpha.1`, validated source release `4171d3356e74f8fc843373f9351775a8966c776f`.

This document separates architectural generations from SemVer increments. A generation begins when the system changes what class of problem it can safely solve, not merely when a feature is added.

## Generation 0 — Source implementation / empirical coordination

### Objective
Prove that multiple AI agents can cooperate around a real project using persistent project artifacts, role instructions, message-board conventions, and recovery handoffs.

### Architectural character
- Coordination was primarily procedural and prompt-driven.
- Durable repository/artifact state compensated for ephemeral chat sessions.
- Roles such as Primary, Manager, and Research emerged from operating experience.
- Message-board and deployment-package ideas were discovered empirically while solving live project problems.

### Strength
This generation proved the operating model and exposed real failure modes instead of designing only from theory.

### Limitation
Project identity, authority, state ownership, delivery semantics, and recovery were not yet strong enough to act as hard security boundaries.

### Transition trigger
The framework needed to support multiple unrelated projects simultaneously without contamination.

---

## Generation 1 — Project-scoped inter-agent mesh

Representative release line: framework `1.1.x`, protocol `2.1.x`.

### Objective
Make project identity a structural boundary and convert the informal message board into a project-scoped control mechanism.

### Major additions
- Canonical project manifest and project charter.
- Project isolation protocol.
- Explicit cross-project exchange protocol.
- Immutable project binding and root/path scope guards.
- Project-scoped AgentBus message handling.
- Project-scoped idempotency.
- Project-scoped lanes and presence.
- Message schema v2.
- Cross-project exchange schema.
- Agent, presence, and lane schemas.
- Adversarial isolation tests.

### Architectural advance
Generation 1 changed `project_id` from descriptive metadata into a security namespace.

The key rule became:

> ordinary execution remains inside one project; cross-project behavior is exceptional and explicitly authorized.

### Strengths
- Strong contamination resistance compared with prompt-only coordination.
- Clear project namespace ownership.
- Append-only communication and supersession model.
- Initial adversarial test coverage.

### Remaining weaknesses
- A claimed project/agent identity still needed stronger linkage to a live authorized execution context.
- Message acceptance and execution acknowledgement were not yet a complete recovery model.
- Durable distributed concurrency semantics did not exist.
- Deployment packages could still drift unless every dependency was manually tracked.

### Transition trigger
The system could isolate projects, but it still needed to learn, schedule work, and coordinate resource pressure without weakening that isolation.

---

## Generation 1.5 — Adaptive operations and bounded self-learning

Representative release lines:
- framework `1.2.x`, protocol `2.1.x` — recursive enhancement;
- framework `1.3.x`, protocol `2.2.x` — Slack scheduled-task transport;
- framework `1.4.x`, protocol `2.3.x` — multi-project capacity coordination.

This is treated as one architectural generation because the core security model remained Generation 1 while operational capabilities expanded.

### 1.2 — Recursive self-enhancement

Added a bounded read-only peer-observation loop:

- peer repositories are evidence, never mutation targets;
- exact peer revisions are pinned;
- discovered patterns become provenance-rich candidates;
- Research discovers;
- Manager reviews;
- Primary alone promotes/grafts;
- candidate recursion is bounded;
- project-specific content must be separated from reusable mechanisms.

The current recursive model is deliberately **recursive discovery, not autonomous self-modification**.

### 1.3 / Protocol 2.2 — Scheduled-task external transport

Added Slack as an optional delivery surface while preserving canonical project state elsewhere.

Important design principle:

> an external communication surface can carry status and results without becoming authoritative control state.

### 1.4 / Protocol 2.3 — Capacity coordination

Added:
- verified capacity reserve;
- fail-closed unknown-limit behavior;
- write coalescing and deduplication;
- high-level read-only cross-project capacity signals;
- explicit prohibition on using peer capacity information as mutation authority.

### Strengths
- The framework began learning from peer systems without granting them authority.
- External transports were separated from canonical truth.
- Multi-project resource pressure became visible without creating shared mutable state.

### Remaining weaknesses
- Recursive enhancement candidates were descriptive rather than empirically benchmarked variants.
- The optimizer/improvement procedure itself was not versioned as a first-class evolvable component.
- No explicit progress/stall ledger existed.
- The message protocol still lacked first-class trust classification, delegation contracts, effect receipts, and distributed cryptographic identity.

### Transition trigger
The system needed stronger recovery, ownership, stale-state protection, and authority derivation from actual execution sessions.

---

## Generation 2 — Fail-closed execution control plane

Representative release lines:
- framework `1.5.x`, protocol `2.4.x` — recovery/concurrency hardening;
- framework `1.6.x`, protocol `2.4.x` — bound identity and reproducible deployment hardening.

Current authoritative generation.

### Objective
Make agent execution, mutation, recovery, and release state enforceable rather than convention-based.

### Major additions

#### Identity-first bootstrap
- Human-intended project is resolved before continuation state.
- `PROJECT_IDENTITY_LOCK.json` is authoritative.
- continuation state, message history, working directory, and semantic similarity are not authorization inputs.

#### Bound-session authorization
- lifecycle: `UNBOUND -> BOUND -> INITIALIZED -> ACTIVE -> DRAINING -> TERMINATED`;
- mutation requires an `ACTIVE` bound session;
- raw caller-provided project strings cannot authorize mutation;
- claimed sender identity must match the bound execution session.

#### Capability model
- authority tier and capabilities are separate;
- child agents inherit project identity;
- child execution instances are fresh;
- child capabilities may remain equal or decrease but cannot escalate.

#### Concurrency and recovery
- execution-instance-owned expiring leases;
- stale-instance lease rejection;
- expected-version compare-and-set mutation;
- project-scoped task registry;
- artifact provenance and content hashing;
- append-only audit evidence;
- per-project pause/drain lifecycle.

#### Delivery semantics
- atomic project-scoped idempotency;
- acknowledgement lifecycle: `RECEIVED -> ACCEPTED -> STARTED -> COMPLETED/FAILED/REJECTED`;
- bounded retries;
- invalid/expired input quarantine.

#### Deployment integrity
- deterministic dependency closure;
- manifest v3 source/capability/component hashes;
- PRIMARY/MANAGER/RESEARCH synchronized as one release set;
- exact-SHA build;
- independent rebuild;
- byte-for-byte reproducibility verification;
- release status tied to evidence from the exact source revision.

### Current message model
Message v2 contains:
- project and destination project;
- sender agent/instance/role;
- recipient list;
- message kind and priority;
- summary/evidence/artifacts;
- reply and supersession links;
- correlation and causation;
- idempotency;
- expiry.

### Generation 2 strengths
Generation 2 is particularly strong in:
- project isolation;
- execution-instance ownership;
- fail-closed authorization;
- stale-state prevention;
- deterministic package integrity;
- auditability;
- explicit release evidence.

### Generation 2 limitations
The current architecture itself identifies the main unresolved production layers:

1. Durable multi-process/distributed implementations of lease, CAS, task, artifact, audit, project-registry, and delivery state.
2. Persistent organization-wide project and agent registries.
3. Organization-wide observability.
4. Durable sanitized cross-project exchange.
5. Broker-specific acknowledgement transport.

Additional limitations exposed by external comparison:

6. Logical identity is not yet cryptographic distributed identity.
7. Message v2 describes sender identity but has no signed immutable envelope or verifiable capability attestation.
8. The acknowledgement ledger tracks delivery/execution state but does not distinguish message delivery from **side-effect commitment** strongly enough for distributed exactly-once-effect semantics.
9. Causality exists as correlation/causation IDs but there is no canonical event sequence / causal DAG authority for distributed reconstruction.
10. Persistent memory/evidence has no universal trust-class promotion model.
11. Delegation requirements are not first-class protocol objects.
12. Stall/non-progress detection is not encoded into the control plane.
13. Recursive enhancement does not maintain benchmarked competing variants with lineage and promotion evidence.
14. Protocol interoperability is internal-first and lacks an explicit adapter contract for standards such as A2A.
15. System-wide telemetry is not yet an input into framework evolution.
16. Human approvals are policy concepts but not yet a universal anti-replay, expiring protocol object.
17. Cascading-failure containment and circuit-breaking are not first-class inter-agent semantics.

---

## Proposed Generation 3 — Distributed Trust, Evidence, and Evolution Plane

Working target name: **Intercommunication Protocol Generation 3 (IPG3)**.

This is a design target, not a release claim. No framework/protocol version is changed by this document.

### Objective
Extend Generation 2 from a secure local/reference control plane into a distributed, interoperable, measurable, self-improving organizational agent system while preserving Generation 2 security invariants.

Generation 3 should not replace the strong Generation 2 core. It should surround and extend it.

### Architectural shift

Generation 2 asks:

> Is this execution instance authorized to perform this operation inside this project?

Generation 3 additionally asks:

> Can this distributed principal prove who it is, what it is allowed to do, what contract it is acting under, what evidence its claims rely on, what effect actually committed, how the event fits into causal history, how trustworthy the retained memory is, and whether the system measurably improved as a result?

### Generation 3 planes

#### 1. Runtime plane
Existing agents, tools, tasks, artifacts, and execution sessions.

#### 2. Control plane
Generation 2 identity, capabilities, leases, CAS, lifecycle, delivery, and project isolation.

#### 3. Trust plane
- authenticated distributed principals;
- signed descriptors/attestations;
- key/session lifecycle;
- transport authentication;
- explicit separation between authentication and authorization.

#### 4. Evidence plane
- canonical event records;
- provenance;
- content digests;
- trust classification;
- immutable decision/effect receipts.

#### 5. Observability plane
- trace/correlation context;
- project/agent/task/message lineage;
- operational metrics;
- security-policy decisions;
- failure and recovery telemetry.

#### 6. Evaluation plane
- regression suites;
- adversarial tests;
- benchmark scenarios;
- stall and duplication metrics;
- cost/reliability/quality measurements.

#### 7. Evolution plane
- external pattern catalog;
- candidate archive;
- competing design variants;
- proposer/critic/verifier separation;
- benchmark-gated promotion;
- versioned improvement algorithm.

### Core Generation 3 invariants

1. Generation 2 project-binding and capability invariants remain mandatory.
2. Transport authentication never substitutes for project authorization.
3. External protocol declarations are claims until locally validated.
4. Messages and effects are separate: receipt of a command does not prove the side effect committed.
5. Every promoted durable fact has provenance and trust classification.
6. Agent reflection cannot silently become policy.
7. Human approvals are scoped, expiring, attributable, and replay-resistant.
8. Recursive improvement may generate arbitrary candidates, but canonical promotion remains conservative and evidence-gated.
9. External interoperability uses validated adapters; internal high-assurance semantics are not weakened to match the least-capable external protocol.
10. Distributed adapters must preserve atomicity/ownership guarantees or fail closed.
11. Observability records decisions/actions/results but does not require hidden chain-of-thought.
12. One project's failure, overload, pause, malicious input, or poisoned memory must not cascade into unrelated projects.

---

## Proposed generational promotion path

### G3.0 — Protocol semantics design
- Message v3 envelope.
- Delegation contract.
- Effect receipt.
- Trust/provenance classification.
- Human approval token/object.
- Event sequence/causal reconstruction model.

### G3.1 — Durable control-plane adapters
- durable lease/CAS/task/artifact/audit/delivery backends;
- process-death and network-partition testing;
- project/global registry service.

### G3.2 — Trust and transport
- authenticated agent principal abstraction;
- signed capability/agent descriptors;
- key rotation/revocation;
- broker transport adapters;
- replay resistance.

### G3.3 — Observability and evaluation
- OpenTelemetry-compatible trace model;
- project/agent/task/message/effect lineage;
- stall detection;
- adversarial benchmark harness;
- cost/reliability metrics.

### G3.4 — Controlled evolutionary improvement
- candidate lineage archive;
- benchmarked variants;
- rejected-idea archive;
- improvement-algorithm versioning;
- proposer/critic/verifier separation;
- guarded recursive cycles.

### G3.5 — Interoperability boundary
- A2A-compatible adapter profile;
- external agent capability negotiation;
- sanitized cross-project/export-import bridge;
- destination-side revalidation.

### G3 Beta gate
The system should not claim Generation 3 beta readiness until it can demonstrate:

- multiple unrelated projects running concurrently across more than one process/runtime;
- authenticated distributed agent identities;
- deterministic denial of identity spoofing and capability escalation;
- crash/restart recovery without stale ownership;
- replay-safe message/effect processing;
- causal reconstruction of a completed task;
- explicit provenance/trust class for promoted memory;
- expiring/replay-resistant human approval;
- observable stall detection and successful replanning;
- benchmarked improvement candidate promotion and rollback;
- validated external protocol adapter without weakening internal invariants;
- failure of one project without stopping or contaminating peers;
- synchronized, reproducible deployment artifacts for all role packages.

---

## Summary

The project has already crossed two major architectural thresholds:

1. **from cooperative prompts to project-scoped inter-agent coordination**;
2. **from coordination conventions to a fail-closed execution/deployment control plane**.

The next generation should cross a third:

> from a secure project-local/reference control plane to a distributed trust-and-evidence system that can empirically evolve without trusting its own proposed improvements.

That is the design target for IPG3.
