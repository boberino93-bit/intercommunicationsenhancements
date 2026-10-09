# Memory Retention and Continuity — Pending Implementation Plan

**Status:** CANDIDATE / NON-CANONICAL / NOT DEPLOYED  
**Parent active controls:** `IEP-MEM-001`, `IEP-CTX-001`  
**Objective:** Reduce silent loss of material context while preserving the existing external-only swarm-memory boundary, project isolation, privacy, provenance, and authority separation.

## 1. Non-negotiable invariants

```text
NATIVE CHATGPT MEMORY != SWARM STATE
VISIBLE TURN != PRIVATE CHAIN OF THOUGHT
MEMORY != CANONICAL STATE
RESTORED CONTEXT != AUTHORITY
RETAINED CONCLUSION != RETAINED EVIDENCE
SUMMARY != SOURCE
DISTRIBUTED PRESERVATION != DISCOVERABLE CONTINUITY
LOSS OF CHAT != LOSS OF AUTHORSHIP
CROSS_PROJECT DISCOVERY != CROSS_PROJECT WRITE
METADATA VISIBILITY != PAYLOAD ACCESS
CAPTURE FAILURE MUST BE VISIBLE
```

## 2. What must be retained

The target design keeps four distinct representations.

### 2.1 Visible-turn journal

Where the host surface and privacy rules permit, preserve exact visible human/assistant turns or immutable authorized external references with:

- project ID;
- conversation/run ID where available;
- turn/event ID;
- sequence / parent event;
- visible content digest;
- attachment/tool-result references;
- sensitivity class;
- timestamp plus causal ordering metadata;
- capture status;
- authority-conveyed = false.

Do not attempt to preserve private model chain-of-thought.

### 2.2 Semantic continuity capsule

A derived materialized view containing:

- current objective;
- material decisions;
- claims and epistemic status;
- evidence refs;
- contradictions;
- authorship deltas;
- hold / authority state;
- unfinished work;
- unresolved questions;
- source coverage;
- next safe action.

The capsule must link back to source events and may never silently replace them.

### 2.3 Concept / provenance graph

Preserve relationships such as:

```text
ORIGINATED_IN
FORMALIZED_AS
IMPLEMENTED_AS
TESTED_BY
REPRODUCED_IN
GENERALIZED_TO
CONTRADICTED_BY
SUPERSEDED_BY
DEPENDS_ON
RELATED_TO
PRIVATE_PROVENANCE_REF
EXTERNAL_PRIOR_ART_REF
```

This is specifically intended to prevent the observed failure where the nodes survived in separate projects but the edges connecting them were lost.

### 2.4 Federated discovery index

Publish safe metadata pointers showing where relevant context exists without automatically importing private payload or authority.

A pointer must carry at minimum:

```text
concept_id
source_project_id
reference
revision / digest where available
visibility
sensitivity
safe summary
payload access class
epistemic status
freshness
AUTHORITY_CONVEYED = FALSE
```

## 3. Capture semantics

A turn/event is material when it changes or adds:

- objective;
- architecture;
- evidence;
- forensic finding;
- contradiction;
- safety rule;
- authorization / hold state;
- implementation plan;
- authorship / provenance;
- blocker;
- unfinished work;
- research hypothesis;
- deployment decision;
- explicit preservation request.

Explicit preservation requests force materiality.

Expected result states:

```text
CAPTURED_DURABLE
CAPTURED_DEGRADED_SINGLE_STORE
CAPTURE_PENDING
CAPTURE_FAILED_VISIBLE
CAPTURE_NOT_SUPPORTED_ON_THIS_SURFACE
```

No silent success.

## 4. Event / ordering model

Wall-clock time must not be treated as a complete causal order.

A material event should support:

```yaml
event_id:
trace_id:
parent_event_id:
project_id:
source_actor:
source_surface:
source_revision:
event_type:
payload_ref:
payload_sha256:
epistemic_class:
authority_class:
sensitivity_class:
schema_version:
wall_time:
logical_sequence:
```

Required distinctions:

```text
WALL CLOCK != CAUSAL ORDER
LATER INGESTION != LATER EVENT
LATER SUMMARY != SUPERSEDING TRUTH
```

## 5. Epistemic integrity

If evidence lineage is unavailable, a retained claim must be downgraded rather than trusted more strongly because it appears in a durable summary.

```text
SUPPORTED_INFERENCE
→ source lineage unavailable
→ INHERITED_INFERENCE_UNVERIFIED
```

Contradictions remain first-class state. Last-writer-wins must not flatten unresolved evidence conflicts.

## 6. Human authorship integrity

Material contributions should preserve:

```text
contribution_id
concept_id
originator
contributors
human contribution summary
model contribution summary
first observed source
first durable source
source refs
confidence in attribution
dispute state
```

Invariant:

```text
LOSS OF CHAT != LOSS OF CREDIT
```

Sensitive/private provenance should remain behind least-privilege access rather than becoming global/public context.

## 7. Storage classes

### Public governance

May contain:
- schemas;
- policies;
- tests;
- non-sensitive pointers;
- public-safe summaries/digests.

### Project canonical

May contain:
- accepted project state;
- project-local evidence refs;
- handoffs;
- validated project knowledge.

### Private continuity

May contain:
- raw visible private conversation turns;
- private human continuity;
- sensitive project context;
- private authorship evidence.

### Restricted

Examples:
- medical;
- intimate relationship / sexuality;
- financial;
- security incident evidence;
- employer/customer restricted information;
- credentials/authentication material.

Restricted material must not appear in public bridge packets or global indexes.

## 8. Required private durable store

Before production-grade raw-turn capture is enabled, designate an approved private continuity store with:

- private access boundary;
- versioned/append-preserving history;
- content digests;
- readback verification;
- export/recovery capability;
- retention/redaction procedure;
- no silent fallback to another project's store.

The public Intercommunication Enhancements GitHub repository is not an acceptable raw private conversation store.

## 9. Restore sequence

Candidate cold-start flow:

```text
BIND PROJECT
→ LOAD LOCAL BOOTSTRAP
→ LOAD CONTINUITY POLICY
→ RESTORE LOCAL CANONICAL CAPSULE
→ RESTORE AUTHORSHIP / CONTRADICTIONS
→ DOWNGRADE ORPHANED INFERENCE
→ LOAD FEDERATED METADATA INDEX
→ DISCOVER MATERIAL RELATED CONTEXT IF GAP REMAINS
→ DEREFERENCE ONLY AUTHORIZED SOURCES
→ RECONCILE AGAINST CURRENT AUTHORITATIVE STATE
→ EMIT RESTORATION RECEIPT
→ RECOVER CURRENT TASK BEFORE ASKING HUMAN TO REPEAT
```

Restoration is read-only and conveys no mutation authority.

## 10. Historical backfill

"All chats restored" may be claimed only when source inventory proves completeness.

Supported future sources may include explicitly authorized:

- user-exported conversation archives;
- Project transcript files;
- repository-backed message snapshots;
- connector-accessible records;
- prior project artifacts.

Backfill flow:

```text
INVENTORY SOURCE
→ HASH INVENTORY
→ PARSE VISIBLE TURNS
→ DEDUPLICATE
→ CLASSIFY SENSITIVITY
→ PERSIST PRIVATE JOURNAL
→ DERIVE SEMANTIC CAPSULES
→ EXTRACT PROVENANCE EDGES
→ LINK PROJECT ARTIFACTS
→ REPORT COVERAGE
```

Coverage labels:

```text
COMPLETE_PROVEN
PARTIAL_KNOWN
PARTIAL_UNKNOWN
UNAVAILABLE
```

## 11. Safety and liveness

Fail-closed controls must remain localized.

Safety examples:
- no unauthorized mutation;
- no private payload leak;
- no authority transfer through memory;
- no unsupported epistemic promotion.

Liveness examples:
- unrelated safe work continues when one branch is blocked;
- store outage does not cause unrelated project-wide deadlock;
- restoration identifies exact missing fields instead of forcing full human retelling.

## 12. Required tests before promotion

- lost-chat cold start;
- exact visible-turn integrity;
- explicit preservation command;
- distributed concept fragmentation;
- private-project pointer isolation;
- historical authorization poisoning;
- orphaned inference downgrade;
- contradiction survival;
- stale pointer;
- wrong-project context injection;
- malformed / tampered portable recovery artifact;
- malicious instruction embedded in historical evidence;
- schema-version mismatch;
- duplicate/replayed event;
- capacity pressure;
- capture-surface limitation disclosure;
- archive completeness proof;
- human reconstruction burden.

## 13. Pending implementation modules

Candidate runtime modules:

```text
org_agent_mesh/context_capture.py
org_agent_mesh/semantic_continuity.py
org_agent_mesh/concept_provenance.py
org_agent_mesh/context_restoration.py
org_agent_mesh/context_discovery.py
org_agent_mesh/reserve_capacity.py
```

Candidate schemas:

```text
conversation_turn_record.schema.json
conversation_capture_receipt.schema.json
retained_context_capsule.schema.json
context_restoration_receipt.schema.json
context_source_inventory.schema.json
authorship_record.schema.json
concept_provenance_edge.schema.json
context_discovery_pointer.schema.json
bridge_transport_envelope.schema.json
```

## 14. Promotion gate

This document is staging material only.

Promotion requires fresh-state readback, security/privacy review, independent herd review, no unresolved critical objection, exact changeset digest, fresh case-bound authorization, read-only shadow deployment, controlled canary, failure injection and rollback evidence.
