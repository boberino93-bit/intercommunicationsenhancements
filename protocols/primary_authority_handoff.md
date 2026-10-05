# Primary Authority-Isolated Handoff Protocol

Status: ACTIVE
Version: 1.0.0

## Core rule

A handoff communicates proposed work and evidence. It never transfers execution authority.

## Roles

RESEARCH and MANAGER may prepare and publish a `PRIMARY_ACTION_REQUEST` through the constrained non-authoritative coordination path. They may not execute privileged production mutation, self-promote to PRIMARY, impersonate PRIMARY, mint or carry human authorization, or claim that a handoff authorizes execution.

PRIMARY may inspect globally visible handoffs, but may execute only when bound to the target project and independently eligible under current project, capability, hold, authentication, and authorization state.

## Handoff requirements

A durable Primary request should contain:

- request_id / prompt_id;
- title and concise objective;
- originating project and role;
- target project and target role;
- current source revision where relevant;
- evidence and artifact references;
- proposed bounded mutations;
- dependencies and blockers;
- consequence classification;
- test/verification expectations;
- provenance with unknowns preserved;
- explicit `authority_conveyed: false`.

The handoff MUST NOT contain reusable authentication or authorization secrets, human tokens, credentials, nonces, or bearer material. A non-secret authorization case reference may be recorded only for audit correlation.

## Registration

A legitimately persisted Primary request is registered in `governance/SWARM_PROMPT_REGISTRY.json`, normally as `PENDING`. Registration and message publication are not execution authority. The request remains pending until an eligible project-local Primary claims it.

## Claim and execution

A Primary claim changes work-review responsibility, not authorization. Before a consequential action, the executing Primary independently verifies:

1. exact target project;
2. role exactly PRIMARY;
3. current human-explicit Primary launch/admission;
4. local project binding and canonical repository;
5. current local contract and security overlay;
6. project hold/quarantine state;
7. required capability/session/lease/fence;
8. fresh bounded human authorization where required.

Failure of any gate denies the affected mutation.

## Foreign Primary

A Primary in Project A may read a Project-B handoff where policy permits, but disposition is `VISIBLE_NOT_EXECUTION_ELIGIBLE`. It may analyze, identify dependencies/duplicates, route, notify, or report. It may not perform Project-B privileged mutation. Human authorization does not override project locality.

## Completion

A request is not `COMPLETED` merely because it was registered, claimed, discussed, or partially implemented. Completion requires objective evidence and durable references. Completed, cancelled, superseded, rejected, expired, and quarantined records remain discoverable for audit.
