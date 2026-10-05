# Reliability Kernel v1.8 — full reference implementation candidate

Status: **IMPLEMENTATION_CANDIDATE — EXACT-HEAD CI PENDING**  
Integration baseline: `72e87ce7cddca17fd78c8ece3ecb5f523c7021e2`  
Frozen normalized runtime source: `fb592418f700fc5e540e76bfa42b043e03fe6ed9`

## Architectural rule

The Reliability Kernel is a constrained enforcement and verification layer, not a second control plane. Existing project identity, role/capability authority, ownership/lease state, durable state, message routing, scheduled-task semantics, package verification, and canonical governance remain authoritative. The kernel may narrow, verify, fence, defer, quarantine, or fail closed; it may not invent authority.

## Implemented v1.8 control surface

The reference implementation now covers the v1.8 reliability extension across sections 233–265:

1. **Executable constitution / policy compilation** — existing authority is projected into reconstructable effective policy slices and signed policy certificates; compilation is non-escalating and certificates are expiry/replay/project/repository/work-instance/ownership fenced.
2. **Machine invariants** — critical authority, identity, ownership and compatibility invariants have explicit machine checks and stable reason codes.
3. **Admission / resource governance** — aggregate ceilings, bounded queues, optional-work shedding, weighted fairness, starvation protection, priority inheritance, and backpressure are implemented without replacing the existing provider-launch admission controller.
4. **Governance liveness** — cyclic dependencies, split-brain control state, conflicting owners, incompatible schemas, unavailable authentication dependencies, and self-referential recovery can drive bounded SAFE_MINIMAL operation.
5. **SAFE_MINIMAL / degraded service** — explicit modes constrain mutation, fan-out, external effects, optional work and recovery behavior; ordinary work cannot silently escape safe mode.
6. **Authenticated human break-glass** — the kernel can verify externally minted strong-auth human assertions, issue short-lived capability-bounded recovery grants, reject agent-originated assertions, enforce replay/expiry/target fences, revoke grants, and append tamper-evident audit events. It intentionally cannot mint a human identity assertion.
7. **Schema/protocol evolution** — explicit compatibility metadata gates writers; parse success alone is not compatibility.
8. **Transactional migration** — planned/canary/in-progress/paused/verified/complete and rollback states support idempotent batch resume and checkpoint-fenced rollback.
9. **Capability evidence / anti-poisoning** — trusted evaluators, signatures, expiry, immutable history, sample/confidence checks, anomaly detection, revocation, and contamination exclusion protect routing evidence.
10. **Holdouts / contamination** — evaluation provenance records held-out status, hidden canaries, prompt/answer/rubric/prior-feedback exposure and independent-evidence weighting.
11. **Blast-radius rings** — `RING_0_LOCAL` through `RING_5_DEFAULT` are strictly sequential; evidence, error/SLO thresholds and human review gates prevent skipping.
12. **Abort / quarantine / rollback** — canary regressions, security violations and backup failures halt promotion; automatic rollback is version- and artifact-digest-fenced.
13. **Catastrophic reconstruction** — durable snapshots are integrity checked; corrupt survivors are rejected; same-revision divergence fails safe; reconstruction emits trusted/rejected survivor sets and a conservative service mode.
14. **Recovery objectives / game day** — RPO/RTO and related freshness objectives are machine-readable; the reference corruption/reconstruction drill records measured observed RPO/RTO.
15. **Proof-carrying handoff** — receiver authority cannot expand and stale ownership epochs are rejected by the first-tranche handoff verifier.
16. **Control-loop damping / churn protection** — hysteresis, dwell time, cooldown and bounded change windows stabilize adaptive control loops and freeze excessive routing churn.
17. **SLOs / reliability budgets** — formal SLO records and separate error, durability, liveness and change budgets alter admission/degradation decisions.
18. **State integrity** — snapshot digests, divergent-revision detection and last-verified-common-revision reporting make consistency checkable.
19. **Dependency cycles / bootstrap root** — explicit graph analysis detects cycles and identifies acyclic bootstrap-root dependencies.
20. **Trusted time** — wall/monotonic/provider time observations detect rollback and material skew; time ambiguity fails safe.
21. **Supply-chain provenance** — signed builder attestations bind source revision, toolchain, dependency inventory, environment, artifact digest, vulnerability state, trust decision and rollout-ring eligibility.
22. **Credential lifecycle** — project/environment/capability-scoped credentials are short-lived, revocable and zeroizable; project teardown revokes residual leases.
23. **Protected-transition assurance** — assurance cases require exact artifact, policy certificate, ownership, tests, independent validation, risks, rollback, ring, supply-chain, backup, monitoring and acceptance evidence.
24. **Explainable control decisions** — material denials, defers, throttles, degraded states, migration blocks, certificate/recovery faults and rollout holds use stable machine-readable reason codes with human-readable explanations.

## Validation strategy

The repository contains two focused v1.8 suites: the original reliability-kernel suite and the expanded adversarial/reliability suite. The expanded suite exercises fairness starvation, aggregate overcommit, load shedding, deadlock, safe-mode escape, agent-initiated break-glass, authenticated break-glass replay/expiry/audit, schema skew, partial migration/resume/rollback, capability-registry poisoning and anomalous evidence, contamination, rollout ring skipping, canary regression and fenced rollback, corrupt backup and split-brain reconstruction, measured recovery objectives, oscillation damping, routing churn, SLO exhaustion, integrity divergence, dependency cycles, clock rollback/skew, supply-chain artifact substitution, credential scope/revocation/expiry/zeroization, assurance-case completeness and protected-transition preflight.

A reference/CI rollout may progress through local, isolated and project-canary rings. No production/default ring promotion is implied by test execution.

## Authority and production boundary

This implementation provides the *verification side* of human-only break-glass and protected-transition authorization. It deliberately does not give ordinary agents the ability to mint trusted human identity assertions, root credentials, deployment approval, or production authority. External root identity/authentication and the canonical deployment-authority path remain separate trust roots.

Likewise, the presence of a `RING_5_DEFAULT` policy does not authorize entering that ring. The v1.8 directive itself forbids manufacturing `APPROVED_FOR_DEPLOYMENT` or `DEPLOYED` without the separately authorized canonical path.

## Completion gate

The reference implementation becomes `VERIFIED` only when the exact candidate tree passes the repository's complete CI composition: legacy/full tests, MANAGER structural review, RESEARCH adversarial review, synchronized package build, dependency-closure verification, independent rebuild and deterministic reproduction. Until then it remains `IMPLEMENTATION_CANDIDATE`.
