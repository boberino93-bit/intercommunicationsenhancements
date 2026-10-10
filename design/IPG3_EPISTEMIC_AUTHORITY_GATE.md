# IPG3 Epistemic Authority Gate

Status: **EXPERIMENTAL / NON-AUTHORITATIVE**

## Kernel invariant

> No generative output, model consensus, or unverified derivative claim may manufacture mutation authority for itself.

The base model is probabilistic. The control plane must therefore assume that any model-produced statement can be wrong, even when fluent, repeated, or agreed upon by many agents. Reliability comes from constraining how claims cross the boundary into accepted state.

## Two-plane architecture

### Generative plane

May create:

- hypotheses;
- analyses;
- reflections;
- proposed decisions;
- candidate artifacts;
- research findings;
- disagreement;
- abstentions;
- swarm recommendations.

Generative-plane output is **not authority**. Agent count does not change this.

### Control plane

May authorize protected effects only after normal project/session/capability/lifecycle checks plus any operation-specific evidence/promotion gate.

For accepted-state promotion the gate binds authorization to:

- exact project;
- exact knowledge record;
- source and target trust class;
- durable decision ID;
- exact operation;
- exact target resource;
- expected state version;
- exact payload SHA-256;
- exact issuing agent execution instance;
- validators;
- independent evidence lineages;
- issue/expiry times;
- one use.

A grant is therefore not a transferable statement like "approved." It is a narrow capability for one exact state transition.

## Independence rule

Consensus is not independent evidence.

If ten agents inspect the same source revision and reproduce the same interpretation, the system has ten opinions over one evidence lineage, not ten independent pieces of evidence. `EvidenceRef.independence_key` collapses evidence by source type, source identity, source revision, and content digest.

This directly addresses correlated hallucination and correlated premise error.

## Trust promotion rules

The design keeps the existing IPG3 trust lattice and adds stronger promotion semantics:

- `AGENT_REFLECTION` may become `DERIVED_KNOWLEDGE`;
- `DERIVED_KNOWLEDGE` may become `VERIFIED_FACT`;
- `EXTERNAL_UNTRUSTED` may become `DERIVED_KNOWLEDGE` or `VERIFIED_FACT`;
- `VERIFIED_FACT` may become `AUTHORITATIVE_CONFIG`;
- `EXECUTION_EVIDENCE` may become `VERIFIED_FACT` or `AUTHORITATIVE_CONFIG`;
- `QUARANTINED` cannot be promoted.

Low-trust classes cannot jump directly to `AUTHORITATIVE_CONFIG`.

Promotion to `VERIFIED_FACT` from low-trust material requires at least two independent evidence lineages. Promotion to `AUTHORITATIVE_CONFIG` requires at least two independent evidence lineages plus a PRIMARY issuer holding both `WRITE_ACCEPTED_STATE` and `APPROVE_CHANGE`.

These are minimum design thresholds, not proof that a claim is true.

## Effect binding and replay resistance

Promotion authorization is bound to an expected resource version and payload digest. If either changes, the grant cannot be reused. The reference ledger allows one successful consumption only.

This prevents:

- replaying an old approval against new state;
- substituting a different payload after review;
- using a grant on another resource;
- using a grant for a different operation;
- using a grant from another execution instance.

## Relationship to existing runtime controls

This gate supplements rather than replaces:

1. project identity binding;
2. active execution instance;
3. capability validation;
4. lifecycle validation;
5. lease/CAS/version checks;
6. approval objects where human authorization is required;
7. effect receipts and idempotency;
8. audit/causal-event recording.

A valid promotion grant without a valid active runtime session still must fail. A valid runtime session without a required promotion grant also must fail for governed accepted-state promotion.

## Non-goals

This design does not claim:

- cryptographic proof of source independence;
- semantic truth verification;
- production signature infrastructure;
- automatic human approval;
- authority to mutate the current G2 runtime.

It is a reference contract to make the epistemic/control boundary testable before large-scale swarm execution.
