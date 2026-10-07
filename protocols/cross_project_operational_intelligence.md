# Cross-Project Operational Intelligence Protocol

Status: **ACTIVE — PRIMARY APPROVED STAGE 1 SEMANTIC CONTROL PLANE**

## Purpose

Allow a project to gain legitimate operational benefit from intelligence, expertise, capability awareness, and management activity elsewhere in the registered ecosystem without pretending that separate execution contexts share tools, authority, assignment, or mutable state.

The core invariant is:

> **Shared intelligence infrastructure is not shared execution.**

Knowledge, expertise, capability, authority, availability, assignment, execution, provenance, temporal state, and project scope are separate properties. No one property may be inferred merely from another.

This protocol defines the semantic/control-plane contract. It does **not** introduce a new global message transport or mutable global bus. Existing project-local coordination, approved `CROSS_PROJECT_EXCHANGE`, sanitized copy-by-value registries, live-operations observability, task intake/delegation, and local mutation authorization remain authoritative.

## Benefit classes

Every cross-project operational-benefit claim must be classified as exactly one of:

- `PASSIVE_KNOWLEDGE` — locally usable validated knowledge imported through an allowed path. This is not participation by the producer.
- `DISCOVERY` — awareness that relevant evidence, artifacts, investigation, or prior work exists elsewhere. Discovery is not acceptance or authority.
- `EXPERTISE_AWARENESS` — awareness that an agent/role/project has relevant expertise. Expertise is not availability, assignment, or capability transfer.
- `CAPABILITY_AWARENESS` — awareness that a capability exists elsewhere. A remote capability does not become a local capability.
- `MANAGERIAL_AWARENESS` — read-only knowledge of relevant coordination state or decisions where policy permits. It does not create local control authority.
- `ROUTING_REQUEST` — a request that another project or execution context consider work. A request is not acceptance, assignment, or execution.
- `ACTIVE_EXECUTION` — independently verified evidence that another execution context has an active local assignment that is currently producing work relevant to the consumer project.

Only `ACTIVE_EXECUTION` permits language that another agent, researcher, manager, or project **is actively working on** the relevant task.

## Canonical envelope

Cross-project operational-benefit metadata conforms to `schemas/project_intelligence_envelope.schema.json` and is validated by `org_agent_mesh.operational_intelligence`.

The envelope preserves source/consumer project identity, benefit class, creation/expiry, correlation, bounded subject/scope, artifact/provenance references, validation state, availability state, capability references, routing/assignment references, and the invariant `authority_conveyed=false`.

The envelope is metadata. It never authenticates a principal, grants a capability, authorizes a mutation, or creates an assignment.

## Existing mechanisms composed by this protocol

### Knowledge and evidence

Use `protocols/swarm_learning.md` and `protocols/collective_intelligence_epistemic_coordination.md` for evidence quality, validation, disagreement, provenance, and local promotion. `PASSIVE_KNOWLEDGE` requires `VALIDATED` state before it is represented as automatically reusable knowledge.

Raw/candidate findings may still be discovered or reviewed, but must not be silently promoted to validated knowledge.

### Cross-project data movement

Use `protocols/cross_project_exchange.md` and `org_agent_mesh.cross_project` for explicit bounded exchange. Exchange remains deny-by-default, copy-by-value, provenance preserving, and non-authoritative with respect to peer mutation.

This Stage 1 protocol does not implement the future durable sanitized export/import bridge described by `cross_project_exchange.md`.

### Ecosystem summaries

Use `org_agent_mesh.ecosystem_coordination.SanitizedEcosystemRegistry` for project-owned copy-by-value peer summaries after the source data has been obtained through an independently authorized read/export path.

### Live availability / activity awareness

Use `protocols/live_operations_observability.md` and `org_agent_mesh.operations_view` only as read-only derived observability. Count only fresh canonical presence as active. Stale, missing, or unattributed activity must stay stale, missing, or unattributed.

`EXPERTISE_AWARENESS`, `CAPABILITY_AWARENESS`, and `MANAGERIAL_AWARENESS` must preserve an explicit availability state. When availability cannot be verified, use `UNKNOWN` rather than inferring availability.

### Work routing

A `ROUTING_REQUEST` is only a request. Cross-project work becomes `ACTIVE_EXECUTION` only after the performing project independently accepts the work under its own local policy and creates/verifiably activates the relevant local assignment.

Do not reuse a source-project delegation contract as if it directly assigned a peer project. The receiving project owns its local task/delegation/lease state.

## Active-execution truth gate

Before representing that another agent/project is actively participating:

1. validate the project-intelligence envelope;
2. resolve assignment evidence independently from the performing project's canonical local assignment/presence surface;
3. require the evidence project to match the envelope source project;
4. require assignment status `ACTIVE`;
5. require a concrete task and assignee identity;
6. require the envelope `assignment_ref` to match the canonical evidence reference;
7. enforce evidence freshness under the governing local/observability policy; and
8. continue to treat the resulting evidence as participation proof only — not mutation authority.

`org_agent_mesh.operational_intelligence.assert_active_execution_claim()` performs consistency checks after canonical evidence has been independently resolved. Supplying a self-asserted evidence object does not make it authoritative.

## Truthful reporting rules

Allowed examples:

- “This project can reuse a validated finding produced elsewhere.”
- “Relevant expertise exists in another registered project; current availability is UNKNOWN.”
- “A routing request has been sent/recorded; it is not yet an active assignment.”
- “Active participation is verified from canonical assignment evidence.”

Disallowed without active-execution proof:

- “The researchers are working on this.”
- “The other project is handling it.”
- “We have that capability now.”
- “The manager has assigned it.”

Remote capability awareness may inform a routing decision; it does not extend the local capability set.

## Discovery before duplication

Before a substantial new investigation, a bound agent should, when relevant read-only surfaces are available and policy permits, check for validated prior findings, relevant artifacts, active/recent related investigations, suitable expertise/capabilities, current availability/freshness, conflicts/supersessions, and existing routing requests.

Reuse remains subject to provenance, validation, freshness, and project-local acceptance. Duplicate work may be retained deliberately for blinded or independent validation.

## Conflict and independent validation

Conflicting findings are preserved, not overwritten. Use existing epistemic reconciliation rules to retain minority findings, evidence, assumptions, and supersession chains. Where independent validation is desired, do not expose prior conclusions to the validating researcher until its first-pass result is committed through the appropriate local coordination path.

## Temporal semantics

Every envelope has explicit creation and expiry timestamps. Stale metadata cannot be silently reused as current availability or execution evidence. Relative deadlines must be anchored before cross-project routing and the original due time/timezone preserved.

## User redirects and supersession

A user redirect does not magically mutate peer-project state. Local branches apply the current authenticated directive under existing rules. For already-routed cross-project work, create and deliver an explicit correlated control/update message through the permitted path; the receiving project applies it under its own authority and work-control rules. Until receipt/acceptance is verified, represent the remote branch as **update pending**, not already changed.

## Security and least privilege

Cross-project operational intelligence must minimize payloads, use sanitized metadata/bounded snapshots where possible, preserve provenance/classification, never bypass identity or mutation authorization, never convert observability into control authority, never convert expertise into availability, never convert a request into assignment, never convert assignment into mutation authority, and never allow a consumer project to write peer accepted state through this protocol.

## Event/subscription model

Stage 1 defines message semantics but does not create a new event transport. Projects may implement subscriptions only over existing approved transports/sanitized registries. Recommended high-value event classes are validated finding, supersession, material warning, conflict, capability/expertise metadata change, routing request/response, assignment-state change, dependency update, and temporal/deadline event.

## Scaling model

At small scale, direct read-only discovery and explicit bounded exchange are sufficient. At tens to hundreds of projects/agents, prefer indexed sanitized metadata, topic/category subscriptions, freshness windows, deduplicated events, project-level summaries, Manager aggregation without mandatory Manager mediation, and explicit routing state machines. At 1,000+ agents, avoid all-to-all communication; use hierarchical/federated indices, interest subscriptions, bounded rendezvous, and independent-validation cohorts while keeping accepted state project local.

## Stage 1 Primary decision

Approved now:

- canonical benefit classes;
- truthful participation semantics;
- canonical envelope/schema;
- structural runtime validation;
- active-execution evidence gate;
- bootstrap inheritance rule;
- composition with existing exchange/observability/learning/delegation controls.

Explicitly deferred:

- a new global mutable Project Intelligence Bus;
- implicit cross-project task assignment;
- automatic global user-override mutation;
- cross-project capability inheritance;
- a durable sanitized export/import bridge beyond existing validator/registry mechanisms.

Those require separate design, adversarial testing, and authorization because implementing them prematurely would create a second control plane and weaken existing isolation guarantees.
