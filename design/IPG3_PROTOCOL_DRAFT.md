# IPG3 — Next-Generation Intercommunication Protocol Draft

Status: DESIGN DRAFT — NON-AUTHORITATIVE — NOT PACKAGED

Baseline: framework `1.6.0-alpha.1`, protocol `2.4.0-alpha.1`.

This document proposes the next major intercommunication generation while preserving the validated Generation 2 security model. It does not change `PROTOCOL_VERSION`, package manifests, runtime code, schemas, or release status.

Normative words `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, and `MAY` describe intended Generation 3 requirements only.

---

# 1. Design goal

IPG3 turns AgentBus from a secure project-scoped message mechanism into a distributed inter-agent protocol with explicit:

- authenticated principal identity;
- local authorization;
- task/delegation contracts;
- immutable message envelopes;
- provenance and trust classification;
- causal event history;
- effect commitment receipts;
- replay resistance;
- human approval objects;
- failure containment;
- observability;
- interoperability adapters;
- evidence-driven recursive improvement.

IPG3 MUST preserve the central Generation 2 rule:

> identity claims inside a message never authorize mutation by themselves.

Authorization remains derived from a validated local execution/session context and local policy.

---

# 2. Layer model

IPG3 separates concerns that Message v2 partially combines.

## 2.1 Authentication layer
Answers: **Who or what produced this envelope?**

Potential implementations MAY use signed local credentials, workload identity, mTLS, verifiable credentials, or other deployment-specific mechanisms.

Authentication MUST NOT directly imply project authority.

## 2.2 Authorization layer
Answers: **May this authenticated principal perform this operation in this project, under this task/contract, at this time?**

Existing bound-session/capability checks remain authoritative for local runtime operations.

## 2.3 Messaging layer
Answers: **What immutable claim/event/request was communicated, to whom, with what causal and delivery requirements?**

## 2.4 Effect layer
Answers: **What side effect actually committed?**

A message being delivered, accepted, or started MUST NOT be interpreted as proof that a requested mutation or external side effect occurred.

## 2.5 Evidence layer
Answers: **What evidence supports the claim, what is its provenance, and how much trust may be assigned to it?**

## 2.6 Evolution layer
Answers: **Did a proposed protocol/framework change measurably improve the system without weakening invariants?**

---

# 3. Identity model

IPG3 introduces four distinct identities.

## 3.1 Project identity
Stable authorization namespace, already present in Generation 2.

## 3.2 Logical agent identity
Example: `primary`, `manager`, `research-03`.

Represents organizational role continuity across executions.

## 3.3 Execution instance identity
Fresh identity for one actual agent execution/session.

It MUST NOT be reused after termination or restart.

Lease ownership, execution ownership, and mutation attribution remain tied to execution instance.

## 3.4 Authenticated principal identity
Identity proven by the runtime/transport authentication mechanism.

This may identify a workload, process, service account, tool host, human, or agent runtime.

The authenticated principal and claimed logical/execution identities MUST be reconciled by local policy before privileged work.

A mismatch MUST fail closed.

---

# 4. Capability and authority model

Message-carried capability claims are advisory evidence, never authority.

For every protected effect:

1. authenticate principal where applicable;
2. resolve local bound session;
3. validate project binding;
4. validate execution instance;
5. validate required capability;
6. validate task/delegation scope when required;
7. validate project lifecycle;
8. validate approval object when required;
9. validate freshness/expiry;
10. only then execute the effect.

IPG3 SHOULD support capability attenuation when delegating work.

Delegation MUST NOT increase capability beyond the parent/local policy ceiling.

---

# 5. Message v3 envelope

Message v3 is conceptually divided into an immutable **envelope** and a typed **payload**.

The envelope is intended to be canonically serialized and hashable.

## 5.1 Required envelope fields

### Protocol identity
- `schema`
- `protocol_version`
- `protocol_features`

### Message identity
- `message_id`
- `project_id`
- `channel_id`
- `created_at_utc`
- `expires_at_utc`

### Sender identity
- `sender.agent_id`
- `sender.agent_instance_id`
- `sender.role`
- `sender.principal_id` when authenticated principal identity exists

### Recipient identity
- explicit recipient agents/roles/services or validated selector object

### Semantic classification
- `class`
- `kind`
- `priority`

### Task and contract linkage
- `task_id`
- `delegation_contract_id`
- `approval_id` when applicable

### Causality
- `trace_id`
- `correlation_id`
- `causation_id`
- `parent_message_id`
- project event sequence or equivalent durable ordering reference when assigned

### Delivery
- `idempotency_key`
- `ack_policy`
- `max_attempts`

### Evidence/integrity
- `payload_sha256`
- `provenance_refs`
- `trust_class`
- signature/attestation metadata when supported

### Policy metadata
- `sensitivity`
- `retention_class`

The exact schema will be validated separately before promotion.

---

# 6. Message classes

IPG3 SHOULD separate broad semantic classes from specific kinds.

Suggested classes:

## CONTROL
Changes or requests lifecycle/control state.

Examples:
- project pause/drain request;
- release gate request;
- delegation creation;
- cancellation.

## WORK
Task assignment and execution coordination.

Examples:
- task offer;
- task claim;
- task progress;
- blocker;
- handoff.

## EVIDENCE
Communicates findings or references to immutable evidence.

Examples:
- research finding;
- test result;
- benchmark result;
- contradiction.

## REVIEW
Requests or records evaluation.

Examples:
- review request;
- disposition;
- adversarial critique;
- verifier result.

## DECISION
Records accepted/superseded organizational decisions.

## EFFECT
Records side-effect commitment or failure.

## SECURITY
Records policy denial, quarantine, suspected poisoning, credential/replay issue, or containment action.

## OBSERVABILITY
Carries bounded operational checkpoints when a transport needs them; high-volume telemetry SHOULD normally use the observability plane rather than AgentBus messages.

## EVOLUTION
Carries improvement candidate lifecycle events, benchmark comparisons, promotion/rejection, and rollback.

---

# 7. Delegation contract protocol

Generation 2 delegates primarily through role instructions and tasks. IPG3 makes delegation scope explicit and durable.

A delegation contract SHOULD contain:

- `contract_id`;
- project identity;
- parent agent and execution instance;
- child/logical assignee identity or selector;
- objective;
- in-scope resources;
- explicit out-of-scope boundaries;
- allowed tools;
- capability ceiling;
- write boundaries;
- source-of-truth references;
- evidence requirements;
- output schema/contract;
- completion criteria;
- failure criteria;
- expiry;
- cancellation policy;
- parent task/trace linkage.

A child agent MUST NOT infer expanded scope from conversation semantics.

If the assignment is inconsistent with local project identity/capabilities, the child MUST reject or escalate it.

Delegation contracts are especially important for parallel Research agents to reduce duplicate work and uncontrolled write overlap.

---

# 8. Trust and provenance protocol

Every durable item that may influence future action SHOULD have a trust classification.

Minimum classes:

## AUTHORITATIVE_CONFIG
Locally approved project/security configuration.

## VERIFIED_FACT
Evidence validated under an explicit verification process.

## EXECUTION_EVIDENCE
Observed logs, test results, receipts, hashes, tool outputs, or state transitions.

## DERIVED_KNOWLEDGE
Analysis based on known evidence but not itself primary evidence.

## AGENT_REFLECTION
Agent-generated lessons/hypotheses.

## EXTERNAL_UNTRUSTED
External web/repository/message content not yet validated.

## QUARANTINED
Content explicitly prevented from influencing execution.

Promotion from a lower-trust class to a higher-trust class MUST require a defined validator and attributable event.

Agent reflection MUST NOT silently become `AUTHORITATIVE_CONFIG` or security policy.

---

# 9. Causal event model

Generation 2 provides `correlation_id` and `causation_id`. IPG3 extends this into reconstructable event history.

The durable control plane SHOULD assign a project-scoped monotonically ordered event reference or another ordering mechanism with equivalent reconstruction semantics.

Each durable event SHOULD preserve:

- project ID;
- event ID;
- event type;
- logical agent;
- execution instance;
- authenticated principal where applicable;
- task ID;
- message ID;
- causal parent(s);
- previous resource version when relevant;
- resulting resource version when relevant;
- timestamp;
- result;
- evidence refs.

The goal is not global total ordering across every project.

The goal is deterministic reconstruction of security-relevant and task-relevant state transitions within a project/failure domain.

---

# 10. Delivery versus effect commitment

IPG3 introduces a strict distinction:

1. **message persisted**;
2. **message received**;
3. **message accepted**;
4. **execution started**;
5. **effect prepared** where applicable;
6. **effect committed**;
7. **effect receipt persisted**;
8. **task completed**.

Transport retries MAY cause duplicate delivery attempts.

They MUST NOT cause duplicate protected effects.

Protected side effects SHOULD use a stable `effect_id`/idempotency identity and destination-side effect ledger.

The effect ledger SHOULD record:

- `effect_id`;
- project/task/message linkage;
- operation type;
- target resource/system;
- request digest;
- commit result;
- resulting version/external receipt where available;
- committing execution instance;
- timestamp;
- retry/replay disposition.

This gives IPG3 **exactly-once effect intent** even when underlying delivery is at-least-once.

---

# 11. Human approval object

Where human authorization is required, IPG3 SHOULD use a first-class approval record rather than relying on prose history.

An approval record SHOULD contain:

- approval ID;
- project ID;
- approving human/principal identity;
- exact operation class;
- bounded resource/target;
- task/effect linkage;
- issued time;
- expiry;
- maximum uses, normally one for high-impact actions;
- status: `ISSUED`, `CONSUMED`, `REVOKED`, `EXPIRED`;
- evidence/reference to the human decision.

Consumption MUST be atomic for one-shot approvals.

Replays MUST fail closed.

Approvals MUST NOT grant capabilities beyond the local policy ceiling unless the governance model explicitly defines that authority.

---

# 12. Cross-project exchange v2

Ordinary AgentBus traffic remains intra-project.

IPG3 cross-project exchange SHOULD be a distinct export/import transaction.

## Export side
- validate source project/session/capability;
- select bounded artifacts/evidence;
- sanitize/redact according to policy;
- classify sensitivity;
- construct immutable export package;
- hash/sign when supported;
- record approval, purpose, destination, expiry.

## Import side
- authenticate/identify source transport principal where applicable;
- verify package integrity;
- verify destination project and purpose;
- treat imported material as `EXTERNAL_UNTRUSTED` by default;
- scan/validate schema and policy;
- import into quarantine/staging;
- promote only through local validation.

Source approval MUST NOT force destination acceptance.

Destination policy remains sovereign.

---

# 13. External interoperability adapter contract

IPG3 SHOULD support standards such as A2A through adapters instead of weakening internal semantics.

Adapter responsibilities:

- protocol/version negotiation;
- external agent descriptor mapping;
- identity claim mapping;
- task mapping;
- message mapping;
- artifact mapping;
- lifecycle mapping;
- error mapping;
- capability claim mapping;
- trust downgrade for unverifiable fields;
- local reauthorization;
- observability correlation.

No external field may bypass local authorization because it is named `role`, `capability`, `approved`, or equivalent.

If the external protocol cannot represent an IPG3 invariant, the adapter MUST either preserve the invariant out-of-band or reject the operation.

---

# 14. Protocol feature negotiation

A major distributed risk is version skew.

IPG3 SHOULD advertise a bounded feature set separately from the numeric protocol version.

Example features:

- `SIGNED_ENVELOPE`;
- `EFFECT_RECEIPT`;
- `DELEGATION_CONTRACT`;
- `TRUST_CLASSIFICATION`;
- `HUMAN_APPROVAL_V1`;
- `DURABLE_ACK`;
- `CAUSAL_EVENT_SEQUENCE`;
- `A2A_ADAPTER_V1`.

Peers MUST NOT assume a feature merely because a version string appears recent enough.

Required feature negotiation MUST fail closed when the peer lacks a safety-critical feature.

---

# 15. Observability protocol

IPG3 SHOULD emit structured traces spanning:

project
→ agent
→ execution instance
→ delegation contract
→ task
→ message
→ tool/action
→ effect
→ artifact
→ review
→ decision.

Recommended trace attributes include:

- project ID;
- agent ID;
- execution instance ID;
- task ID;
- message/effect IDs;
- capability exercised;
- policy decision;
- retry count;
- failure/rejection reason;
- latency;
- state version;
- lease ownership event;
- human approval reference;
- external adapter/protocol;
- cost/token metrics where available and appropriate.

Observability MUST NOT require hidden chain-of-thought.

It should capture attributable actions, structured decisions, evidence, and outcomes.

---

# 16. Stall and convergence protocol

Borrowing the useful ledger concept from orchestrator systems, IPG3 SHOULD maintain two separate structures.

## Evolution/Task Strategy Ledger
Contains:
- objective;
- current plan;
- confirmed facts;
- unresolved assumptions;
- accepted decisions;
- rejected approaches;
- open risks;
- next high-value frontier.

## Progress Ledger
Contains:
- most recent actions;
- evidence gained;
- measurable change;
- blockers;
- repeated attempts;
- quality/cost/runtime metrics.

A stall policy SHOULD trigger when configurable evidence shows repeated non-progress, such as:

- equivalent proposals repeated;
- same failure repeated;
- same sources reread without new evidence;
- wording changes without architectural change;
- rising cost without measurable quality/reliability gain.

On stall, the agent/controller SHOULD replan rather than continue the same loop.

---

# 17. Recursive evolution protocol v2

Generation 2 recursive enhancement is retained but upgraded from pattern discovery to controlled empirical evolution.

Candidate lifecycle proposal:

`DISCOVERED`
→ `NORMALIZED`
→ `THREAT_MODELED`
→ `SANDBOXED`
→ `TESTED`
→ `ADVERSARIALLY_TESTED`
→ `BENCHMARKED`
→ `REVIEWED`
→ `PRIMARY_ACCEPTED`
→ `INTEGRATED`
→ `RELEASE_VALIDATED`

Terminal/side states:

- `REJECTED`;
- `SUPERSEDED`;
- `BLOCKED`;
- `ROLLED_BACK`.

Every candidate SHOULD preserve:

- lineage/parent candidate(s);
- source inspiration;
- hypothesis;
- affected invariants;
- expected benefit;
- baseline metrics;
- benchmark definition;
- security tests;
- measured result;
- cost/complexity impact;
- rejection/acceptance reason;
- resulting revision if integrated.

The incumbent architecture is always a candidate.

New designs MUST beat or materially complement the incumbent under defined criteria before promotion.

---

# 18. Improvement algorithm versioning

The process that discovers and evaluates improvements is itself an evolvable artifact.

IPG3 SHOULD version:

- research strategy;
- candidate generation strategy;
- candidate scoring model;
- adversarial review procedure;
- benchmark set;
- promotion criteria;
- recursion bounds.

A change to the improvement algorithm MUST be evaluated using the same or stronger evidence gate as a framework change.

The system MUST retain previous versions so the optimizer itself can be rolled back.

---

# 19. Failure-domain containment

IPG3 SHOULD make cascading-failure containment explicit.

Each project is a default failure domain.

Controls SHOULD include:

- per-project queue/backpressure limits;
- per-project retry budgets;
- circuit breakers for failing external dependencies;
- maximum fan-out/delegation depth;
- bounded recursive research depth;
- tool error budgets;
- quarantine thresholds;
- per-project pause/drain;
- isolation of poisoned/invalid imported content.

Failure, overload, or compromise in one project MUST NOT automatically pause or mutate unrelated projects.

---

# 20. Security threat requirements

IPG3 validation SHOULD explicitly cover at least:

- goal hijacking;
- tool misuse;
- identity spoofing;
- privilege/capability escalation;
- supply-chain substitution;
- unexpected code execution;
- memory/context poisoning;
- insecure inter-agent communication;
- cascading failure;
- human-trust exploitation;
- rogue agents;
- replay attacks;
- forged approvals;
- forged effect receipts;
- stale-instance ownership;
- version downgrade;
- protocol feature confusion;
- external adapter confused-deputy attacks.

Security failures discovered during live use SHOULD become repeatable regression cases whenever feasible.

---

# 21. Compatibility with Generation 2

IPG3 SHOULD be introduced through compatibility adapters rather than a flag-day rewrite.

Suggested migration:

## Phase A — dual-read design validation
Message v2 remains authoritative. IPG3 schemas/tests exist only under design/experimental paths.

## Phase B — v3 shadow envelopes
For selected internal messages, generate a v3 shadow representation and compare semantics without changing execution.

## Phase C — v3 internal pilot
One test project uses Message v3 with a v2 compatibility projection for legacy tools.

## Phase D — durable/distributed pilot
Run more than one process/runtime with durable control-plane adapters and authenticated principals.

## Phase E — protocol 3 release candidate
Only after adversarial, recovery, interoperability, and reproducibility gates succeed.

---

# 22. Required new protocol objects

Before IPG3 can become executable, design and validate schemas for:

1. `message/v3`;
2. `delegation-contract/v1`;
3. `effect-receipt/v1`;
4. `human-approval/v1`;
5. `trust-record/v1` or trust/provenance fields shared across records;
6. `causal-event/v1`;
7. `protocol-capabilities/v1`;
8. `external-agent-descriptor/v1`;
9. `evolution-candidate/v2`;
10. `benchmark-result/v1`;
11. `stall-signal/v1`;
12. `cross-project-package/v2`.

---

# 23. First implementation tranche

The safest first tranche is **semantics before distributed infrastructure**.

Recommended order:

1. define Message v3 schema;
2. define delegation contract schema;
3. define effect receipt schema;
4. define trust/provenance classes;
5. define human approval schema;
6. write validators with no production transport changes;
7. write downgrade/upgrade projection between v2 and v3 where safe;
8. build adversarial tests;
9. add shadow-mode generation;
10. only then choose durable/broker/identity implementations.

This sequence prevents infrastructure choices from prematurely locking the protocol design.

---

# 24. Promotion gate

IPG3 must not replace Protocol 2.4 merely because the draft is complete.

Promotion requires evidence that the new system:

- preserves every relevant Generation 2 invariant;
- rejects forged project/agent/principal identity;
- rejects capability escalation;
- prevents duplicate protected effects under retry/replay;
- survives process failure and restart without stale ownership;
- reconstructs causal execution history;
- correctly downgrades imported/untrusted evidence;
- atomically consumes one-shot approvals;
- detects and contains at least one modeled cascading-failure scenario;
- supports observable stall/replan behavior;
- runs recursive improvement candidates without direct canonical overwrite;
- validates package dependency closure and synchronized role builds;
- demonstrates interoperability through an adapter without bypassing local authorization;
- passes reproducible release-gate validation from an exact source revision.

---

# 25. Working principle

Generation 2 made the system harder to mutate incorrectly.

Generation 3 should make the system harder to **deceive**, harder to **replay**, harder to **poison**, easier to **reconstruct**, easier to **measure**, and safer to **improve recursively**.

The intended end state is not autonomous mutation.

It is **autonomous proposal plus adversarial evidence plus conservative promotion**.
