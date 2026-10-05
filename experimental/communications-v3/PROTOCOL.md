# Organization Agent Mesh Communications Protocol v3 — Experimental

Status: **EXPERIMENTAL / NON-AUTHORITATIVE**

Schema family: `org-agent-mesh/message/v3-experimental`

This protocol is an additive evolution of the existing v2 project-scoped append-only message bus.

## 1. Core principle

A v3 message is a **verifiable statement from an authenticated principal in a bounded context**.

It is not itself authority.

Every receiver still evaluates:

- project identity;
- sender principal/session;
- role;
- capabilities;
- lifecycle state;
- lease/fence state;
- policy revision;
- message class;
- target scope.

Cryptographic validity is necessary for strong provenance, but never sufficient for permission.

## 2. Compatibility model

v3 MUST NOT make existing v2 messages unreadable.

Compatibility modes:

- `V2_NATIVE` — current behavior unchanged.
- `V3_SHADOW` — a v3 envelope is generated/validated for comparison but does not control execution.
- `DUAL_RECORD` — v2 canonical message plus linked v3 experimental envelope.
- `V3_NATIVE_CONTENT` — v3 used for content/evidence while control remains existing runtime authority.
- `V3_NATIVE_CONTROL` — allowed only after authority, durability and replay tests pass and promotion is explicitly authorized.

Downgrade must fail closed for control messages: a v3 control message cannot be stripped to unsigned v2 content and retain control semantics.

## 3. Message classes

Every v3 envelope has exactly one `message_class`:

### `CONTENT`

Research, findings, requests, contradictions, reviews and ordinary coordination.

`CONTENT` carries **no executable lifecycle authority**.

### `EVIDENCE`

Evidence-bearing statements with explicit epistemic classification and evidence references.

`EVIDENCE` carries no authority merely because the evidence is strong.

### `CONTROL`

Typed lifecycle command only:

- `CONTINUE`
- `REDIRECT`
- `PAUSE`
- `STOP`
- `STOP_TREE`

A CONTROL envelope MUST include an authenticated supervisor attestation and the receiver MUST independently evaluate supervisory authority.

### `ACK`

Delivery or handoff acknowledgement.

An ACK proves a principal reported a delivery state. It does not transfer authority.

### `HANDOFF`

Proof-carrying transfer of state/context between authorized agents.

A handoff transfers information/responsibility only within existing authority ceilings.

## 4. Envelope layers

A v3 message is separated into layers so provenance cannot be confused with authority.

### 4.1 Identity layer

Required concepts:

- `project_id`
- `repository_identity`
- `sender.agent_id`
- `sender.agent_instance_id`
- `sender.role_id`
- `sender.principal_id`
- `sender.session_attestation_id`

The role claim MUST be derived from or checked against trusted session/routing authority. It must not remain an arbitrary free-form label.

### 4.2 Causal layer

Required:

- `message_id`
- `correlation_id`
- `causation_id`
- `reply_to`
- `logical_clock`
- `timestamp_utc`
- `stream_id`
- `previous_envelope_digest`

UTC time is useful operational metadata but not the sole ordering mechanism.

`logical_clock` is monotonic per sender/stream.

### 4.3 Governance context

Optional for low-risk content; required where a statement depends on mutable authority/state:

- `protocol_version`
- `governance_revision`
- `policy_digest`
- `assignment_revision`
- `ownership_epoch`
- `fence_token`
- `source_revision`

A stale governance or fence context cannot be silently treated as current.

### 4.4 Payload layer

Contains:

- `kind`
- `subject`
- `summary`
- `body`
- `artifacts`
- `evidence`
- `tags`

For CONTROL messages, `body` is not free-form executable prose. It contains a typed command object.

### 4.5 Delivery layer

Contains:

- `idempotency_key`
- `requires_ack`
- `expires_at_utc`
- `delivery_class`
- optional retry policy identifier

Idempotency/replay state must be durable before v3 CONTROL is production-capable.

### 4.6 Integrity layer

Contains:

- canonicalization identifier;
- payload/envelope digest;
- signature algorithm;
- key identifier;
- signature;
- optional broker/session-attestation digest.

Initial production target: asymmetric signatures such as Ed25519 where signer/verifier separation is required.

The protocol does not mandate that model code hold private keys. Preferred design is a trusted broker/signing boundary associated with the authenticated session.

## 5. Canonicalization

Signatures must cover a deterministic representation.

Experimental rule:

1. Remove only the signature bytes themselves from the object being signed.
2. Serialize UTF-8 JSON with sorted object keys and no insignificant whitespace.
3. Arrays preserve order.
4. Numbers must use the schema-constrained representation; non-finite numbers are forbidden.
5. Compute SHA-256 over canonical bytes.
6. Sign the digest or canonical bytes according to the signature profile.

Before production, replace this provisional rule with a formally specified canonical JSON profile and conformance vectors.

## 6. Epistemic status

Evidence-bearing claims include one of:

- `OBSERVED`
- `INFERRED`
- `CLAIMED`
- `UNKNOWN`

Rules:

- forwarding a claim preserves its original status unless new evidence justifies promotion;
- consensus does not automatically change status;
- a message may contain multiple claims with different statuses;
- receivers may downgrade status if evidence cannot be verified;
- evidence status cannot grant capabilities or lifecycle authority.

## 7. Control/data separation

Research/content messages MUST NOT be interpreted as lifecycle commands merely because their prose contains strings like `STOP` or `REDIRECT`.

Lifecycle change occurs only when:

1. a CONTROL envelope is parsed successfully;
2. its identity/integrity checks succeed;
3. the supervisor principal is authorized for the target agent/project;
4. lifecycle preconditions permit the transition;
5. the decision is persisted with the required durability.

Human natural-language messages may still produce lifecycle changes through the existing user-control interpreter, but the resulting machine action should be represented as a typed authoritative control decision.

## 8. Same-project internal bus invariant

The v3 internal message bus remains same-project-only.

`project_id` MUST equal `destination_project_id` for internal bus publication.

Cross-project communication continues through the explicit cross-project exchange protocol and must not be smuggled through a signed internal message.

A valid signature does not override project isolation.

## 9. Durable delivery and replay

The current acknowledgement state machine is preserved conceptually:

`RECEIVED → ACCEPTED → STARTED → COMPLETED`

with bounded failure/retry paths.

For v3, the authoritative delivery ledger must durably store at least:

- project-scoped idempotency identity;
- message/envelope digest;
- recipient principal/instance;
- current ACK state;
- attempts/max attempts;
- consumed nonce/replay identity;
- rejection/quarantine reason;
- update version;
- timestamp/logical clock as evidence, not sole synchronization primitive.

A process restart must not permit a terminal/replayed message to appear fresh.

## 10. Tamper-evident history

Do not impose one global linear hash chain across concurrent writers.

Instead:

- each deterministic writer/stream maintains `previous_envelope_digest`;
- messages are content-addressed by envelope digest;
- periodic checkpoint records contain a deterministic set/Merkle root of accepted envelope digests;
- checkpoint records are signed by an authorized checkpoint service;
- high-assurance deployments may anchor checkpoint digests outside the writable swarm trust domain.

This detects deletion/reordering/substitution while preserving concurrency.

The communication log remains evidence/history, not accepted project truth.

## 11. Handoff protocol

A HANDOFF envelope contains or references a state capsule and binds:

- project;
- sender instance;
- intended receiver/role;
- task/work ID;
- state capsule digest;
- exact source revision;
- assignment revision;
- current lease/fence context when applicable;
- blockers;
- continuation instructions;
- evidence references;
- expiry.

The receiver returns a signed/attested ACK identifying the handoff digest.

ACK states for handoff should distinguish:

- `RECEIVED`
- `VALIDATED`
- `ACCEPTED`
- `REJECTED`

Acceptance does not renew the sender's lease or grant capabilities absent normal authority.

## 12. Cross-project approval integration

A v3 cross-project exchange approval should be a signed/attested object outside the internal bus, binding:

- exchange ID;
- requester principal;
- approving principal;
- source project;
- destination project;
- exact artifact digests;
- allowed use;
- expiry;
- policy revision;
- approval nonce.

It must be replay-protected and independently validated by the destination/source policy as appropriate.

## 13. Consequential-effect linkage

When a message references or requests a protected external effect, the communication layer must not itself execute it.

It can carry the `prepared_action_digest`, `grant_id`, or effect receipt ID as evidence/context.

The consequence gateway remains the effect authority boundary.

## 14. Failure semantics

Fail closed for mutation/control when any of these are invalid or ambiguous:

- project identity;
- sender principal;
- sender role binding;
- signature/attestation;
- policy revision required for the operation;
- lease/fence required for the operation;
- replay/nonce state;
- control authority;
- handoff state digest.

Read-only quarantine/diagnosis remains allowed.

## 15. Privacy and reasoning boundary

The protocol carries decisions, claims, evidence references, summaries and state required for coordination.

It does not require private hidden reasoning or chain-of-thought.

## 16. Success criteria

v3 is successful only if it improves proof of:

- who sent a message;
- in what project/session/role context;
- what exact content was sent;
- whether it was replayed or modified;
- what caused it;
- what evidence status it carries;
- whether a valid authority path existed for any control consequence;
- how the system recovered after restart;

without reducing useful swarm autonomy or changing legitimate role behavior.
