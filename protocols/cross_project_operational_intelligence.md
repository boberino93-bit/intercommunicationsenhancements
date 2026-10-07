# Cross-Project Operational Intelligence Protocol

Status: **ACTIVE — PRIMARY APPROVED REFERENCE FEDERATION COMPLETE**

## Purpose

Allow a project to gain legitimate operational benefit from intelligence, expertise, capability awareness, management activity, and explicitly routed work elsewhere in the registered ecosystem without pretending that separate execution contexts share tools, authority, assignment, or mutable accepted state.

The core invariant is:

> **Shared intelligence infrastructure is not shared execution.**

Knowledge, expertise, capability, authority, availability, assignment, execution, provenance, temporal state, and project scope are separate properties. No one property may be inferred merely from another.

The reference implementation composes project-local state, approved `CROSS_PROJECT_EXCHANGE`, sanitized copy-by-value metadata, explicit acceptance/update receipts, immutable snapshot exchange, live-operations observability, task intake/delegation, and local mutation authorization. It does **not** create a mutable global control plane.

## Benefit classes

Every cross-project operational-benefit claim is exactly one of:

- `PASSIVE_KNOWLEDGE` — locally usable validated knowledge imported through an allowed path. This is not participation by the producer.
- `DISCOVERY` — awareness that relevant evidence, artifacts, investigation, or prior work exists elsewhere.
- `EXPERTISE_AWARENESS` — awareness that another project has relevant expertise. Expertise is not availability or assignment.
- `CAPABILITY_AWARENESS` — awareness that a capability exists elsewhere. Remote capability does not become local capability.
- `MANAGERIAL_AWARENESS` — read-only knowledge of permitted coordination state or decisions. It does not create control authority.
- `ROUTING_REQUEST` — a request that another project consider work. A request is not acceptance, assignment, or execution.
- `ACTIVE_EXECUTION` — independently verified evidence that another execution context has an active local assignment producing work relevant to the consumer project.

Only `ACTIVE_EXECUTION` permits language that another agent/project **is actively working on** the task.

## Canonical semantic envelope

Cross-project operational-benefit metadata conforms to `schemas/project_intelligence_envelope.schema.json` and is validated by `org_agent_mesh.operational_intelligence`.

The envelope preserves source/consumer project identity, benefit class, creation/expiry, correlation, bounded subject/scope, artifact/provenance references, validation state, availability state, capability references, routing/assignment references, and `authority_conveyed=false`.

The envelope is metadata. It never authenticates a principal, grants a capability, authorizes mutation, or creates an assignment.

## Federated discovery registry

`org_agent_mesh.operational_intelligence_federation.OperationalIntelligenceRegistry` provides a project-owned copy-by-value index of sanitized peer metadata.

Registry entries conform to `schemas/operational_intelligence_registry_entry.schema.json` and contain only bounded themes, expertise tags, capability references, explicit availability, validation/expiry timestamps, provenance, source-exchange reference, and `authority_conveyed=false`.

Rules:

1. the registry record is stored only under the consumer project;
2. the peer project remains metadata inside that local record;
3. unknown or stale availability is never promoted to `AVAILABLE`;
4. expired entries are excluded from discovery;
5. unknown fields fail closed as unsanitized input;
6. discovery is read-only and cannot assign work or change peer/local accepted state.

## Routing lifecycle and cycle prevention

A safe routing lifecycle is:

```text
DISCOVERY / AWARENESS
    -> ROUTING_REQUEST
    -> target-project local intake
    -> ACCEPTED or DECLINED receipt
    -> target-project local task/delegation/lease
    -> independently verified ACTIVE assignment/presence
    -> ACTIVE_EXECUTION
    -> result returned through approved exchange
```

`validate_routing_lineage()` preserves origin/target identity and rejects duplicate project visits or a target already present in the lineage. This prevents automated routing from silently creating circular delegation.

A source-project delegation contract must never directly assign a peer project. The receiving project owns its local task, delegation, lease, work-control, and mutation authorization state.

## Acceptance and update receipts

Target-project acceptance and later user redirects are represented by `schemas/cross_project_acceptance_receipt.schema.json` and validated by `validate_acceptance_receipt()`.

Receipt states are:

- `ACCEPTED`
- `DECLINED`
- `UPDATE_PENDING`
- `UPDATE_ACCEPTED`
- `UPDATE_REJECTED`
- `SUPERSEDED`

An `ACCEPTED` receipt requires a target-local task reference but is still **not** proof of active execution. Active participation still requires the separate `ACTIVE_EXECUTION` truth gate.

Update states require explicit update and supersession references. Until the target project acknowledges a redirect, the correct state is `UPDATE_PENDING`, not “changed everywhere.”

Receipts always preserve `authority_conveyed=false`.

## Active-execution truth gate

Before representing that another agent/project is actively participating:

1. validate the project-intelligence envelope;
2. independently resolve assignment evidence from the performing project's canonical local assignment/presence surface;
3. require the evidence project to match the envelope source project;
4. require assignment status `ACTIVE`;
5. require concrete task and assignee identity;
6. require the envelope `assignment_ref` to match the canonical evidence reference;
7. enforce evidence freshness under the governing local/observability policy; and
8. treat the result as participation proof only, never mutation authority.

`assert_active_execution_claim()` performs consistency checks after canonical evidence is independently resolved. Supplying a self-asserted object does not make it authoritative.

## Sanitized snapshot bridge

`SanitizedSnapshotBridge` is the reference durable export/import bridge.

It is deliberately two-phase and immutable:

### Source export

- requires an active source-project session;
- requires `CROSS_PROJECT_EXCHANGE` and the local durable-write capability;
- validates the existing approved exchange contract;
- accepts only `PUBLIC` or `INTERNAL_SANITIZED` classification;
- rejects unknown snapshot fields;
- bounds the summary payload;
- requires provenance and expiry;
- prevents the snapshot from outliving the approved exchange;
- stores the immutable export under the source project;
- binds the package to a deterministic SHA-256 digest.

### Destination import

- reads the canonical immutable source export referenced by exact source project and snapshot ID;
- verifies the digest and source/destination identities;
- requires an active destination-project session with `CROSS_PROJECT_EXCHANGE` and local durable-write capability;
- rejects expired exchanges/snapshots or unsafe classifications;
- writes only a copy-by-value record under the destination project;
- stamps the imported record `accepted_state=false` and `authority_conveyed=false`.

Import is evidence acquisition, **not knowledge promotion or accepted-state mutation**. Any later promotion must use the consumer project's ordinary validation/acceptance mechanisms.

There is intentionally no peer-write API and no API that automatically promotes an imported snapshot into doctrine, assignment, release state, or accepted project truth.

## Knowledge and conflict handling

Use `protocols/swarm_learning.md` and `protocols/collective_intelligence_epistemic_coordination.md` for evidence quality, disagreement, validation and promotion. `PASSIVE_KNOWLEDGE` requires `VALIDATED` state before being represented as automatically reusable knowledge.

Conflicting findings are preserved rather than overwritten. Independent/blinded validation remains legitimate duplicate work and must not be suppressed by deduplication logic.

## Temporal semantics

Every envelope, registry entry, acceptance receipt, exchange and snapshot has explicit time semantics. Stale metadata cannot be silently reused as current availability or execution evidence. Relative deadlines must be anchored before cross-project routing with the original due time/timezone preserved.

## Security and least privilege

The federation must never:

- infer authority from knowledge or expertise;
- infer availability from expertise;
- inherit remote capabilities locally;
- infer assignment from a routing request;
- infer mutation authority from assignment;
- infer accepted state from presence or import;
- write peer accepted state;
- use observability as a control channel;
- create a second mutable global controller.

Cross-project intelligence is bounded, provenance-preserving, expiry-aware and copy-by-value.

## Scaling model

At small scale, direct read-only discovery and explicit bounded exchange are sufficient. At tens to hundreds of projects/agents, use sanitized indexed metadata, topic/category filtering, expiry, deduplication, project summaries and explicit routing receipts without mandatory Manager mediation. At 1,000+ agents, avoid all-to-all communication: use federated/hierarchical indices, interest subscriptions, bounded rendezvous and independent-validation cohorts while accepted state remains project-local.

## Reference implementation completion

Implemented and active in the reference runtime:

- canonical benefit classes and semantic envelope;
- truthful participation reporting;
- active-execution evidence gate;
- project-local sanitized discovery/expertise/capability registry;
- explicit freshness handling;
- routing lineage and cycle detection;
- target-project acceptance/decline receipts;
- explicit update/supersession acknowledgement states;
- immutable approved sanitized snapshot export/import bridge;
- bootstrap inheritance;
- adversarial regression tests;
- deterministic deployment-package inclusion through existing wildcard dependency closure.

Still intentionally not implemented:

- mutable global shared context;
- implicit peer assignment;
- cross-project source writes through intelligence metadata;
- remote capability inheritance;
- automatic global user-command mutation without target-local acceptance;
- treating all peer activity as relevant or trusted by default.

Those are prohibited architectural shortcuts, not unfinished items.
