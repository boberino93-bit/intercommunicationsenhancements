# Primary Forensic Review — Cross-Project Operational Intelligence

Date: 2026-10-07  
Primary decision: **APPROVE STAGE 1 SEMANTIC CONTROL PLANE; DEFER NEW GLOBAL TRANSPORT**

## Executive conclusion

The proposal identified a real semantic gap, but the repository does **not** need a new global mutable Project Intelligence Bus to close it.

Most required safety and coordination primitives already exist: immutable project binding and project-scoped authority; explicit deny-by-default `CROSS_PROJECT_EXCHANGE`; sanitized copy-by-value ecosystem summaries; read-only multi-project operations observability; advisory multi-project capacity signals; provenance-aware swarm learning and epistemic reconciliation; task intake/delegation contracts; independent/blinded validation patterns; and local mutation authorization/accepted-state ownership.

The missing layer was a canonical semantic contract answering:

> What kind of operational benefit is this project actually receiving from activity elsewhere, and what may truthfully be inferred from it?

Stage 1 therefore adds classification, an envelope, and an evidence gate without creating a second control plane.

## Current-state assessment

1. **Project isolation is already first-class.** Peer activity does not expand local capability or authority.
2. **Cross-project exchange already fails closed.** It requires an active source-project session, `CROSS_PROJECT_EXCHANGE`, exact requesting-agent agreement, distinct projects, expiry, and explicit approval.
3. **Peer state can already be represented safely.** `SanitizedEcosystemRegistry` stores a local copy-by-value peer summary with source-exchange provenance.
4. **Operations awareness separates observation from authority.** The organization snapshot cannot grant authority, assignment, acceptance, or peer truth.
5. **Capacity coordination demonstrates the right federation pattern.** Projects expose compact advisory signals; aggregation remains read-only.
6. **Learning already separates evidence from doctrine.** Raw experience, validated knowledge, and operating doctrine are distinct.

## Gap

The controls did not share canonical vocabulary for passive knowledge benefit, discovery, expertise awareness, remote capability awareness, managerial awareness, routing requests, and verified active execution.

That gap permits a semantic failure even when technical authority remains safe: an agent can see peer activity or knowledge and overstate it as “the researchers are working on this,” or imply that a remote capability has become local.

## Target architecture

Stage 1 introduces a semantic layer over existing transports:

```text
existing local/cross-project evidence surfaces
        |
        v
Project Intelligence Envelope
        |
        +--> PASSIVE_KNOWLEDGE
        +--> DISCOVERY
        +--> EXPERTISE_AWARENESS
        +--> CAPABILITY_AWARENESS
        +--> MANAGERIAL_AWARENESS
        +--> ROUTING_REQUEST
        +--> ACTIVE_EXECUTION
        |
        v
truth-preserving reporting + local policy decision
```

No class grants authority. Only `ACTIVE_EXECUTION` permits an active-participation claim, and only after canonical assignment evidence is independently resolved.

## Execution routing model

A safe lifecycle is:

```text
DISCOVERY/EXPERTISE_AWARENESS
    -> ROUTING_REQUEST
    -> peer project local intake
    -> peer project local acceptance/delegation
    -> canonical ACTIVE assignment/presence
    -> ACTIVE_EXECUTION evidence
    -> result returned through approved exchange/handoff path
```

A source-project delegation contract must not directly assign a peer project. Each receiving project owns its own task/delegation/lease state.

## Authority model

The new semantic layer conveys **zero authority**. The following implications are forbidden:

- knowledge -> authority;
- expertise -> availability;
- capability awareness -> local capability;
- routing request -> assignment;
- assignment -> mutation authority;
- presence -> accepted state;
- Manager awareness -> peer control;
- Primary role -> global mutation authority.

Existing authentication, project binding, exchange, work-control, and mutation gates remain unchanged.

## Temporal and user-redirect model

Every intelligence envelope has explicit creation and expiry. Stale metadata cannot be silently reused as current availability or execution evidence. Relative deadlines must be anchored before handoff.

The original proposal implied user overrides might propagate automatically. That is unsafe under the current architecture. Local branches apply the current directive under existing authority rules; already-routed peer work receives an explicit correlated update through a permitted path. Until the peer acknowledges/applies it, state is `UPDATE_PENDING`, not already changed.

## Forensic failure analysis

- **False active-participation claim:** mitigated by requiring `ACTIVE_EXECUTION` plus matching canonical assignment evidence.
- **Expertise/availability collapse:** mitigated by mandatory explicit availability; unknown remains `UNKNOWN`.
- **Remote capability inheritance:** mitigated by treating capability awareness as observation only.
- **Request/assignment collapse:** `ROUTING_REQUEST` cannot carry an assignment reference.
- **Stale presence:** envelope expiry plus existing liveness/freshness rules.
- **Context poisoning/global overload:** no new global transport in Stage 1; bounded metadata, filtering, sanitized summaries, local acceptance.
- **Authority inversion:** `authority_conveyed=false` remains invariant.
- **Circular delegation:** preserve correlation/request refs; future automated routing must detect cycles.
- **Independent validation destroyed by deduplication:** duplicate detection remains advisory; blinded validation remains supported.
- **Automatic user override becomes global mutation:** remote change remains pending until explicitly delivered and locally accepted.
- **Second-control-plane drift:** no new mutable global bus is approved in Stage 1.

## Scaling analysis

- **5 agents:** direct discovery and explicit bounded exchange are sufficient.
- **25 agents:** use live operations, capacity aggregation, sanitized summaries, and routing correlation; Manager aggregation must not become a mandatory bottleneck.
- **100 agents:** require topic/category filtering, expiry/freshness, deduplication, bounded summaries, and independent-validation cohorts.
- **1,000+ agents:** avoid all-to-all communication; use federated/hierarchical metadata indices, subscriptions, bounded rendezvous, and project-local accepted state.

## Implementation roadmap

### Stage 1 — approved and implemented

1. canonical benefit classes;
2. project-intelligence envelope schema;
3. structural runtime validator;
4. active-execution evidence consistency gate;
5. truth-preserving participation state;
6. canonical protocol;
7. bootstrap overlay inheritance;
8. regression tests for semantic collapse cases.

### Stage 2 — next candidate

1. read-only discovery index over sanitized metadata;
2. expertise/capability metadata registry with explicit freshness;
3. request correlation/cycle detection;
4. target-project acceptance receipt;
5. explicit supersession/update acknowledgement state.

### Stage 3 — only after adversarial validation

A durable sanitized export/import bridge for approved cross-project snapshots that preserves project-local accepted state, provenance, classification, expiry, and allowed use.

### Not approved

- global mutable shared context;
- implicit peer assignment;
- peer source writes through intelligence metadata;
- local inheritance of remote capabilities;
- automatically treating all Manager/Research activity as useful to every project;
- global automatic user-command mutation without peer-local acceptance.

## Canonical directive

> Agents operate inside explicit project and execution contexts while participating in a governed intelligence network. Knowledge, expertise, capability, authority, availability, assignment, execution, provenance, temporal state, and project scope are separate properties. Agents may discover and reuse permitted validated intelligence from other projects, but must never infer local capability, authority, availability, assignment, or active participation from that intelligence. Cross-project work begins as a request and becomes active participation only after the performing project independently accepts it and canonical assignment evidence verifies active execution. Cross-project intelligence never conveys mutation authority; project-local identity, accepted state, and authorization remain authoritative.

## Primary disposition

**APPROVED:** semantic/control-plane integration and bootstrap inheritance.

**DEFERRED:** new global bus transport and durable automatic cross-project execution routing.

The proposal is no longer awaiting a hypothetical future Primary. This review is the Primary disposition for Stage 1.
