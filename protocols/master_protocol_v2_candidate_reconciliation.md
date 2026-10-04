# Master Protocol V2 Candidate Reconciliation

Status: **CANDIDATE / NON-CANONICAL**

This document reconciles `GLOBAL_RECURSIVE_CONCURRENT_SWARM_PROTOCOL_V2_CLEAN_REWRITE(2).txt` with the current framework without changing accepted governance. It is implementation guidance for the candidate branch only.

## Authority model

The persistent authority roles remain exactly:

- PRIMARY
- MANAGER
- RESEARCH

Execution mode and coordination scope do not create new authority. An ecosystem coordinator is a human-designated existing PRIMARY for a bounded epoch and is not a fourth role or superuser.

Cross-project mutation remains denied unless an explicit approved bridge separately authorizes it.

## Generation is not swarm run identity

`generation_id` identifies an accepted integration boundary. `swarm_kernel.global_run_id` identifies one operational swarm execution run. They may be correlated but MUST NOT be treated as interchangeable identifiers.

The candidate `GenerationRegistry` provides a project-local crash-durable current-generation head with compare-and-set transition history. A V2-aware authoritative mutation SHOULD call `assert_current(project_id, generation_id)` immediately before accepting a generation-sensitive side effect.

Until all accepted-state mutation surfaces are integrated with that fence, the framework MUST NOT claim universal stale-generation enforcement.

A stale generation completion may still be preserved as evidence. It does not automatically gain authority to mutate current accepted state.

## Native message-envelope mapping

V2 section 33 is conceptual. The current native durable envelope remains `org-agent-mesh/message/v2`.

Conceptual V2 field | Native field
--- | ---
`message_id` | `id`
`sender.project_id` | `project_id`
`sender.agent_id` | `from_agent`
`sender.agent_instance_id` | `from_agent_instance_id`
`sender.role` | `from_role`
`destination.project_id` | `destination_project_id`
`destination.agent_id_or_group` | `to[]`
`message_type` | `kind`
`created_at` | `timestamp_utc`
`expires_at` | `expires_at_utc`
`ack_required` | `requires_ack`
`artifact_refs` | `artifacts[]`
`payload` | `summary`, `applies_to_state`, `evidence`, and typed artifacts as appropriate
`correlation_id` | `correlation_id`
`causation_id` | `causation_id`
`idempotency_key` | `idempotency_key`

No second incompatible message envelope is introduced by this candidate.

## Acknowledgement interpretation

Transport/delivery acknowledgement remains:

`RECEIVED -> ACCEPTED -> STARTED -> COMPLETED | FAILED | REJECTED`

`EXPIRED` is currently a validation/quarantine outcome. `SUPERSEDED` is a message/state interpretation relationship. Neither is added to `DeliveryLedger` merely to mirror V2 prose.

## Task/workflow state mapping

The current atomic TaskRegistry remains:

- OPEN
- ACTIVE
- BLOCKED
- COMPLETED
- FAILED
- CANCELLED

V2 terms such as `READY_FOR_HUMAN_LAUNCH`, `ASSIGNED`, `CLAIMED`, `WAITING`, `REVIEW_REQUIRED`, `SUPERSEDED`, `ABANDONED`, and `DEFERRED` are higher-level workflow/node states or Artifactory coordination states. They MUST NOT silently redefine the TaskRegistry CAS state machine.

If a future accepted implementation needs those states in runtime code, add a versioned workflow/node schema rather than breaking the current task registry.

## Agent lifecycle mapping

The current agent record remains:

- UNBOUND
- BOUND
- INITIALIZED
- ACTIVE
- DRAINING
- TERMINATED

`AWAITING_HUMAN_ASSIGNMENT`, `WAITING`, `BLOCKED`, and `LOST` are operational/presence states unless a separately reviewed schema evolution promotes them into the durable agent lifecycle.

## Human-manual launch plus authorized scheduled occurrences

The default launch model remains **HUMAN_MANUAL**.

An approved scheduled occurrence is permitted only when a human explicitly created, enabled, or authorized the scheduled task/workflow, or an accepted project contract explicitly delegates that scheduling authority within stated bounds.

A scheduled occurrence is a future invocation produced by previously authorized scheduler configuration. It is not evidence that one agent autonomously spawned another ChatGPT session.

Every scheduled project-bound occurrence must:

1. carry captured project identity, authorized role, repository/forum/artifact namespaces, routing-contract version, task identity, and occurrence identity from the bound project contract;
2. pass provider admission where an enforceable hook exists;
3. parse and validate launch context;
4. verify the current local contract and identity lock;
5. bind a fresh execution instance;
6. reach the normal bootstrap-ready barrier before project task state advances;
7. preserve occurrence identity and idempotency across retries;
8. fail closed if context is missing, stale, malformed, ambiguous, or conflicts with the current contract.

Project overlays may disable scheduled launching or narrow allowed roles/tasks.

## Dependency and rendezvous records

Candidate dependency and rendezvous records are project-local durable coordination state. They reuse the existing `DurableRecordBackend` and normal bound-session capability checks.

Dependency edges describe required work/output only. They do not carry authority. Cycles are rejected by the reference registry.

Rendezvous required membership is fixed in the versioned record. A rendezvous does not complete until every required member has supplied evidence. Timeout records missing required members rather than accepting them implicitly.

## Ecosystem coordinator epoch

A coordinator claim must name the existing PRIMARY, its project, epoch, scope, reads, writes, prohibited actions, start time, review/expiry condition, and human assignment reference.

If two different coordinator identities claim the same epoch:

`SPLIT_BRAIN_DETECTED -> FREEZE GLOBAL MUTATIONS -> PRESERVE BOTH CLAIMS -> COMPARE HUMAN/ACTIVE-CONTRACT AUTHORITY -> SUPERSEDE LOSING CLAIM -> RESUME`

The reference implementation detects this condition but does **not** claim distributed global consensus. The current SQLite durable backend is single-node crash-durable reference infrastructure.

## Sanitized ecosystem summaries

The candidate ecosystem summary is copy-by-value and allowlist-only. It may contain project identity, purpose/status, repository/branch, board root, protocol/package versions, capacity, backup/recovery posture, allowed cross-project links, and verification time.

Arbitrary project payloads, credentials, secrets, or undeclared fields are rejected by the reference validator.

## Promotion gate

This candidate cannot become canonical until:

- independent MANAGER review or an explicit human waiver of that independent-review requirement exists;
- independent RESEARCH security/concurrency review or an explicit human waiver exists;
- candidate implementation tests pass;
- package dependency closure includes the new shared runtime/protocol/schema components;
- synchronized PRIMARY/MANAGER/RESEARCH packages build reproducibly from one exact commit;
- a canonical DECISION/SUPERSESSION record explicitly promotes the accepted protocol version.

The current surrogate reviews are useful evidence but are not independent review evidence.
