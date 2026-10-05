# Communications v3 — Forensic Synthesis

Status: **EXPERIMENTAL ANALYSIS**

Evidence baseline: `intercommunicationsenhancements@1eb8e32b936d0fe534f68e26dc2af71f845df1ba`

## 1. What the external reviews got right

Across the supplied reviews, the strongest common conclusion is that the system's **internal control design is stronger than the external assurance chain around promotion and effect execution**.

The highest-value themes are:

- distinguish implemented controls from preventively enforced controls;
- require exact-SHA traceability;
- make independent review meaningful rather than nominal;
- authenticate identities at trust boundaries;
- bind authorization to exact action/effect;
- durably preserve replay/revocation/STOP state;
- distinguish `OBSERVED`, `INFERRED`, `CLAIMED`, `UNKNOWN`;
- preserve swarm behavior while hardening the substrate.

These themes remain compatible with the current architecture.

## 2. What must NOT be copied blindly from the reviews

### 2.1 Reviewer access limitations are not system findings

One independent review explicitly lacked authenticated/live GitHub access and therefore could not inspect several repositories or current rulesets/CI state.

That reviewer correctly disclosed the limitation.

Do not convert it into findings such as:

- repositories do not exist;
- a project is unrelated;
- current SHAs are false;
- governance is absent.

Those were limitations of that reviewer's vantage point.

Direct GitHub inspection from this analysis confirms the central repository and its current communication/runtime files are accessible, and the broader forensic baseline has direct metadata for all six authorized repositories.

### 2.2 The communication-hardening memo was written before AgentBus inspection

Its own caveat says AgentBus code was not inspected.

The recommendation to authenticate and context-bind messages is useful, but the current implementation is not a blank slate.

## 3. What the current message bus already does well

Direct inspection of `org_agent_mesh/message_bus.py`, `org_agent_mesh/delivery.py`, `schemas/message.schema.json`, communication-awareness policy, and existing message records shows that v2 already provides:

1. project-scoped internal messaging;
2. explicit rejection of cross-project internal bus traffic;
3. publication through an ACTIVE `AgentSession` with `PUBLISH_MESSAGE` capability;
4. claimed logical sender must match the bound session;
5. claimed execution-instance ID must match the bound session;
6. protocol-version checking;
7. message-kind and priority checking;
8. correlation and causation IDs;
9. project-scoped idempotency identity;
10. message expiry;
11. append-only atomic file creation;
12. duplicate detection;
13. quarantine of invalid/expired payloads;
14. bounded delivery retry states;
15. explicit acknowledgement state transitions;
16. communication-visibility truthfulness rules that distinguish direct forum access from mirrors/snapshots/handoffs.

These are preservation requirements for v3.

## 4. Communication-specific gaps confirmed by direct source inspection

### C-001 — Claimed role is not bound by `message_bus.validate_message`

The current publication path verifies:

- `from_agent` against `binding.agent_id`;
- `from_agent_instance_id` against `binding.agent_instance_id`.

`from_role` is required but remains a free-form non-empty message field. `ProjectBinding` itself does not contain role.

Impact:

A valid bound publisher could mislabel its role unless another layer detects the mismatch.

v3 response:

Make role a trusted session/principal claim issued or verified against the routing/authority registry rather than arbitrary payload content.

### C-002 — Delivery acknowledgement state is process-local

`DeliveryLedger` stores records in an in-memory dictionary protected by `RLock`.

Impact:

Acknowledgement state, attempts, and deduplication represented by that ledger do not themselves survive process restart.

The repository already has durable-state machinery; v3 should integrate with it rather than invent an unrelated persistence subsystem.

### C-003 — Message origin is session-bound, but not independently cryptographically attestable

Within the trusted process, active-session binding is meaningful and should be preserved.

Across a stronger trust boundary, a stored message does not carry an independently verifiable signature/attestation proving which trusted principal produced it.

v3 response:

Add broker/session attestation and, where signer/verifier trust separation is required, asymmetric signatures. Do not give raw private keys to model reasoning code.

### C-004 — Ordinary content and authoritative control should be machine-distinguishable

Current v2 kinds are semantically rich, but lifecycle commands are governed separately by supervision rather than represented as a strict communication class.

v3 response:

Introduce typed `CONTROL` envelopes whose authority is revalidated by supervision. Ordinary CONTENT containing words like STOP/REDIRECT must have no lifecycle effect.

### C-005 — Current schema is permissive relative to a high-assurance envelope

The v2 schema:

- uses draft-07;
- does not set `additionalProperties: false`;
- leaves many nested evidence/artifact structures unconstrained;
- treats timestamps as strings rather than schema `date-time` values.

This is acceptable for a flexible alpha protocol but weaker than the desired v3 integrity profile.

v3 response:

Use a strict experimental schema, versioned extension points, and explicit compatibility conversion rather than silently tightening v2 in place.

### C-006 — Existing causality fields can be strengthened for restart/clock anomalies

v2 already has:

- `correlation_id`;
- `causation_id`;
- `reply_to`;
- UTC timestamp.

v3 response:

Keep them and add a monotonic logical clock plus per-writer/stream digest linkage. Avoid one global chain that serializes concurrent agents.

## 5. System findings relevant to communications design

### S-001 — Green-before-promotion remains open

Current central `main` exact-SHA integrated validation is red while narrower review lanes pass.

The immediate failure is a user-control semantic/token mismatch, not proof that the lifecycle-aware behavior is wrong.

v3 work must remain experimental and must not be used to route around the red baseline.

### S-002 — GitHub preventive enforcement is still external to source-level governance

The source model is capable of expressing stronger invariants than GitHub currently prevents at the canonical branch boundary.

v3 must not claim production assurance merely because its tests pass on an experimental branch.

### S-003 — Signing does not solve authority by itself

The existing system correctly separates capabilities/lifecycle/project scope conceptually.

v3 must preserve that separation:

`authentic message ≠ authorized action`

### S-004 — Communication history must not become a second accepted-state authority

Existing handoff policy explicitly says the handoff and swarm operational state do not replace canonical project truth.

A tamper-evident v3 log should prove integrity/history, not decide accepted project state.

## 6. Recommended next-generation architecture

The preferred v3 design is therefore:

`existing project/session authority`

plus

`authenticated principal attestation`

plus

`strict typed envelope`

plus

`durable delivery/replay state`

plus

`control/content separation`

plus

`proof-carrying handoff`

plus

`tamper-evident causal history`

while retaining:

- v2 compatibility;
- same-project bus;
- explicit cross-project exchange;
- current role hierarchy;
- current scheduling rules;
- current consequence gateway;
- canonical project-state authority.

## 7. Design rule for every future v3 change

Before adding a v3 feature, answer:

1. Which observed defect or assurance gap does this close?
2. Which current swarm behavior could it accidentally change?
3. Can the fix be implemented below/around the swarm instead?
4. What negative test proves the bypass is closed?
5. What compatibility test proves v2 behavior is preserved?
6. Does the feature create new authority, or merely prove existing authority?

If the answer to question 6 is “creates new authority,” the change requires a separate governance decision and must not be smuggled into a communication-protocol upgrade.
