---
title: Governed Proposal Artifact Persistence and Primary Execution Routing Protocol
protocol_id: IE-GOVERNED-PROPOSAL-ARTIFACT-ROUTING
protocol_version: 1.0.0
status: ACTIVE_CANONICAL
source_proposal: IE-2026-10-07-PSPA-01
activated_date: 2026-10-07
authorization_case: AUTH-05CD5C8D
clarification_required: false
---

# Governed Proposal Artifact Persistence and Primary Execution Routing Protocol

## Canonical invariant

**SUBSTANTIAL EXECUTABLE PROMPTS ARE DURABLE PROJECT ARTIFACTS.**

A substantial prompt, proposal, directive, forensic remediation plan, implementation plan, or architecture change intended for later execution MUST NOT depend on chat history as its only durable representation. Persist it as Markdown in the canonical proposal/recommendation surface of the project that owns implementation authority.

For Intercommunication Enhancements, the canonical candidate surface is `swarm-governance/recommendations/`.

## Routing

- Project-local change -> owning project -> owning project PRIMARY.
- Cross-project compatibility change -> designated coordinating governance project -> authorized coordinating PRIMARY.
- Universal swarm change -> Intercommunication Enhancements -> Intercommunication Enhancements PRIMARY -> authorized global propagation path.

Do not create multiple independent sources of truth for the same proposal. Other projects may retain references or handoff receipts.

## Primary execution boundary

Producing, storing, retrieving, reviewing, validating, accepting, executing, and propagating a proposal are separate state transitions.

Non-Primary roles MAY analyze, critique, validate, test, and recommend. They MUST NOT infer protected mutation authority.

Protected project-wide, cross-project, bootstrap, security, authority, registry, shared-schema, orchestration, or universal-swarm mutations require the appropriately authorized PRIMARY unless a higher-authority canonical rule explicitly states otherwise.

**Role is not authorization.** This protocol does not weaken `protocols/authority_authentication.md` or `protocols/mutation_authorization.md`.

## Required proposal metadata

A persisted executable proposal SHOULD record at least: artifact/proposal ID, title, source project/agent/session where available, target project, target role, change class, status, creation time, source revision, dependencies, affected components, known risks, authorization requirements, whether Primary execution is required, and clarification state.

Recommended lifecycle states: `CANDIDATE`, `UNDER_REVIEW`, `NEEDS_CLARIFICATION`, `VALIDATING`, `ACCEPTED`, `IMPLEMENTING`, `IMPLEMENTED`, `REJECTED`, `SUPERSEDED`, `ARCHIVED`.

## Primary bootstrap recall

During bootstrap, takeover, recovery, or review initialization, a PRIMARY MUST discover pending governed proposal artifacts relevant to its authority. It SHOULD identify candidates, clarification blockers, validation state, accepted-but-unimplemented work, supersession, dependencies, current repository revision, active claims/leases, authorization state, and related handoffs.

Retrieval begins evaluation. It does not imply acceptance or authorization.

## Pre-implementation clarification gate

Before implementation, the responsible PRIMARY MUST scan for unresolved material ambiguity affecting scope, naming, migration, repository target, security posture, canonical communication location, destructive behavior, public/private exposure, backward compatibility, dependency ordering, execution authority, or deployment boundary.

If material ambiguity remains after authoritative project context is reviewed, ask the human owner before implementation. If no material ambiguity remains, record `clarification_required: false` and continue without redundant questions.

## Concurrency and stale-state safety

Before durable mutation use the current-state sequence where applicable:

`READ -> MODEL -> DIFF -> COORDINATE -> RE-READ -> AUTH -> WRITE -> RE-READ -> TEST -> CHECKPOINT`

Classify stale proposals as `UNCHANGED`, `PARTIALLY_STALE`, `MATERIALLY_STALE`, `CONFLICTING`, or `SUPERSEDED` and reconcile before execution.

## Semantic separations

`CAPTURE != HANDOFF`

`HANDOFF != ACCEPTANCE`

`ACCEPTANCE != AUTHORIZATION`

`AUTHORIZATION != EXECUTION`

`EXECUTION != GLOBAL PROPAGATION`

Storage is not acceptance. Retrieval is not authorization. Possession of a prompt is not permission to mutate the Global Swarm.

## Receipts

Material proposal lifecycle transitions SHOULD leave a compact receipt with proposal ID, prior/new state, acting role/agent, time, repository revision, authorization reference, validation reference, result, and next owner.
