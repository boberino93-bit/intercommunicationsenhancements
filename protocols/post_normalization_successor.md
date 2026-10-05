# Post-normalization successor control overlay

Status: **CANONICAL REFERENCE OVERLAY ON MAIN**  
Production/service deployment: **NOT IMPLIED BY REPOSITORY COMMIT**  
Authority source: authenticated Human Root instruction plus canonical repository root-change policy.

## 1. Purpose and placement

This overlay implements the missing universal mechanisms from the 2026-10-05 post-normalization successor directive without creating a second control plane. It composes with the current PRIMARY recurring swarm protocol, project binding, role/capability state, leases/fencing, v1.8 Reliability Kernel, v1.8.1 consequence gateway, and communication-awareness controls.

Existing stronger controls win. The overlay may narrow or structure execution; it cannot mint authority, ownership, deployment status, or target-system success.

## 2. Predecessor evidence state

The repository contains contradictory historical predecessor evidence: `reconciliation/POST_NORMALIZATION_RECONCILIATION_REPORT.md` says the normalization entry condition was satisfied, while `reconciliation/HUMAN_ROOT_CANDIDATE_OVERRIDE_2026-10-05.md` records that the concrete retirement packet was not located and therefore remained unproven.

This overlay does **not** rewrite that contradiction as a passed predecessor gate. The current Human Root instruction authorizes this exact `main` integration despite that unresolved historical evidence state. Machine-readable state is `HUMAN_ROOT_OVERRIDE_UNPROVEN`, not `VERIFIED`.

## 3. Cold-start orientation and priority frontier

A fresh agent must establish a compact situational view before claiming new work. `org_agent_mesh.successor_bootstrap.PriorityFrontierSnapshot` is a freshness-bounded derived view; it is not authority.

Priority provenance is explicit: `HUMAN_SET`, `POLICY_SET`, `DERIVED`, or `INCOMPLETE`. Human-set priority wins. For this directive the human-set order is:

1. Duo Screen / Duo Open
2. Intercommunication Enhancements
3. BenefitFlow
4. AI Behavioral Control Lab
5. Samsung Power Bootstrap
6. Warp Propulsion Lab

Missing priority is reported as `INCOMPLETE`; recency, list order from unrelated material, or model preference must not be silently promoted to human priority.

## 4. Deterministic research bootstrap

The phrase `get started` resolves to the deterministic sequence encoded in `GET_STARTED_SEQUENCE`: orient, hydrate project capsule, read priority/frontier and existing task/claim/liveness/material state, identify an appropriate unclaimed lane, classify duplication, claim through the canonical path, publish start status, execute, persist material deltas, reassess, then hand off/close.

Research claims use `OBSERVED`, `SUPPORTED`, `INFERRED`, `HYPOTHESIS`, `DISPUTED`, or `BLOCKED`. These are epistemic labels, not authority.

## 5. Research-swarm launcher contract

`ResearchLaunchEnvelope` defines the launcher-facing contract independently of launcher topology. Before work begins, the launch must validate project/run/task identity, capabilities, data boundaries, priority/frontier reference, stop criteria, checkpoint/liveness/material-delta destinations, and policy/protocol versions.

A semantic launch identity prevents accidental duplicate swarms. A healthy equivalent active launch is attached to rather than sharded again; a resumable unhealthy launch is recovered through the canonical path.

For the first Duo Screen / Duo Open kickoff only, the initial execution profile is one MASTER, one MANAGER, and three RESEARCH workers. This is not a universal agent-count rule.

## 6. Capability and data-boundary discovery

Agents must discover actual capability availability and authorization before use. Missing capability is `DEPENDENCY_UNAVAILABLE`; present-but-unauthorized capability is `PERMISSION_DENIED`. No fallback to employer/private/connected sources is allowed unless those sources are already inside the project boundary.

Native capability is preferred only when it is equivalent or stronger for the required guarantee. Provider/tool identity never creates authority.

## 7. Human step-up and exact action binding

`StepUpVerifier` consumes externally issued, signed, short-lived, non-replayable attestations. It cannot mint them. The attestation is bound to subject, authority class, project, authentication strength, exact action digest, issuance/expiry, nonce, verifier, and status.

Conversational identity remains insufficient for a protected Human Root transition. The underlying authentication secret is not placed in model context.

This overlay does not replace the existing `HumanRootAuthenticator`, `CommitAuthorizationGrant`, or consequence gateway. Human identity/step-up establishes who may authorize; the consequence gateway still binds a consequential commit to its exact prepared action and current state.

## 8. Architecture complexity governance

`org_agent_mesh.architecture_governance` makes mechanism class, boundary contracts, dependency impact, failure semantics, recovery disposition, deprecation lifecycle, and complexity delta mechanically visible without making them a second authority plane.

An invariant, policy, protocol, contract, implementation, registry entry, score, or recommendation cannot create authority merely by existing.

Canonical failure equivalents include `INPUT_INVALID`, `CONTRACT_VIOLATION`, `DEPENDENCY_UNAVAILABLE`, `POLICY_CONFLICT`, `INVARIANT_VIOLATION`, `TIMEOUT`, `STATE_CONFLICT`, `VALIDATION_FAILURE`, `PERMISSION_DENIED`, `AUTHENTICATION_REQUIRED`, `AUTHORITY_NOT_ESTABLISHED`, `STALE_OWNER`, `STALE_POLICY`, `UNKNOWN_EFFECT`, `QUARANTINED`, and `UNKNOWN_FAILURE`.

`UNKNOWN_EFFECT` may not use blind `RETRY`; it must enter `VERIFY_OR_RECOVERY` or another bounded non-duplicating disposition.

## 9. Reused hard controls

This overlay reuses rather than duplicates:

- project/session/capability/lease/fence controls in the canonical control plane;
- v1.8 policy, recovery, assurance, and reliability controls;
- v1.8.1 45-second nominal / 60-second maximum-normal liveness and durable material-delta semantics;
- the existing `PreparedAction -> exact CommitAuthorizationGrant -> pre-commit revalidation -> effect receipt` consequence path;
- target/effect verification and `UNKNOWN_EFFECT -> VERIFY_OR_RECOVERY`;
- package exact-revision and reproducibility gates;
- project isolation and deny-by-default cross-project mutation.

## 10. Promotion and deployment truth

A commit to `main` makes this repository overlay canonical source material. It does not, by itself, prove that every external runtime host, scheduler, distributed backend, AgentBus/Artifactory adapter, branch protection rule, or production/default-ring deployment is configured with it.

Repository CI must validate the committed head. Runtime-dependent properties remain `UNPROVEN` or `PARTIAL` until the real runtime/target supplies evidence. Never convert an unknown runtime effect into `VERIFIED` for presentation convenience.
