# Kernel / Swarm Architecture Forensic Analysis — 2026-10-07

Status: **EXPERIMENTAL DESIGN REVIEW — NON-AUTHORITATIVE**

Repository: `boberino93-bit/intercommunicationsenhancements`  
Reviewed branch: `design/next-gen-intercommunication-protocols`  
Reviewed branch head at start: `b24a1d3e48974a49a3f53aa53286aa907fe38088`

## Executive finding

The architecture is materially stronger than an ordinary multi-agent orchestration stack because authority is already treated as a local, project-bound capability rather than as a property of model text. The strongest existing properties are identity-first bootstrap, immutable project binding, fresh execution-instance identity, role/capability separation, project isolation, CAS/versioning, lease ownership, bounded retry/idempotency, explicit cross-project exchange, reproducible package closure, and design-only swarm recommendations.

The principal remaining kernel risk is **epistemic-to-authority transduction**: the G2 runtime strongly constrains *who* may mutate accepted state, but the accepted-state write API itself does not encode *what epistemic class the proposed value belongs to* or *which evidence promotion gate justified it*. If a correctly authorized PRIMARY is induced by hallucination, correlated swarm error, stale evidence, or poisoned context, the runtime can faithfully persist the wrong value.

This is not an identity failure. It is a missing typed boundary between probabilistic cognition and authoritative state.

The experimental changes accompanying this review introduce an IPG3 **Epistemic Authority Gate** that treats generative output as proposal/evidence only and binds promotion authority to an exact project, knowledge record, operation, resource, payload digest, state version, issuer execution instance, evidence set, decision, expiry, and one-shot consumption.

## Scope

The review covered the architecture visible in:

- bootstrap and identity lock;
- project/session/capability model;
- project lifecycle;
- message publication and delivery;
- tasks, leases and versioned state;
- artifacts and audit;
- cross-project exchange;
- recursive self-enhancement;
- IPG3 trust/provenance and evolution;
- adaptive swarm regulation;
- release/package closure;
- design CI and promotion status.

The review distinguishes **enforced runtime controls** from **design-only intended controls**.

## Architectural model

The system can be understood as five interacting planes:

1. **Human/root intent plane** — establishes current project intent and high-level authorization boundaries.
2. **Control plane** — project binding, execution identity, capabilities, lifecycle, leases, CAS and protected mutation.
3. **Generative plane** — model reasoning, research, synthesis, critique and swarm recommendations.
4. **Evidence plane** — provenance, trust class, benchmark/test results, receipts and causal records.
5. **Deployment plane** — package dependency closure, exact source revision, reproducibility and coordinated role release.

The design is strongest when these planes remain separated. Most serious residual risks are plane-confusion failures.

## Confirmed strengths

### 1. Identity is not inferred from conversation state

The bootstrap contract correctly rejects handoffs, queues, forums, accepted state, working-directory state and semantic similarity as authorization inputs. `ProjectBinding` is immutable and mutation requires an ACTIVE bound `AgentSession`.

This is a major protection against context contamination and accidental cross-project action.

### 2. Capability attenuation is one-way

Children receive fresh execution identities and cannot exceed parent capability ceilings. This prevents a specialist from creating a more privileged descendant merely through prompt semantics.

### 3. Project isolation is fail-closed

Internal messages cannot cross project boundaries. Cross-project exchange is a separate capability-gated path. Project IDs are canonicalized by rejection rather than lossy sanitization, avoiding alias collisions.

### 4. Mutable state uses concurrency controls

Leases are execution-instance-owned and expiring. State mutation uses compare-and-set. Task transitions use versions and ownership checks. This substantially reduces stale-writer and duplicated-work corruption.

### 5. Message persistence is idempotency-aware

Internal publication uses atomic exclusive creation keyed by a project-scoped idempotency identity. Duplicate publication does not silently create a second accepted message.

### 6. Swarm sizing is recommendation-only

The adaptive swarm regulator cannot spawn agents. It emits an allocation recommendation that requires ACTIVE PRIMARY authorization elsewhere. This is exactly the correct separation for scaling probabilistic workers.

### 7. Recursive enhancement is not self-promoting

The recursive enhancement engine performs read-only peer observation and persists local candidates. IPG3 evolution separates candidate evidence from promotion and retains the incumbent architecture as a candidate.

### 8. Deployment closure is unusually disciplined

Role packages are tied to exact source revisions and reproducible dependency closure. This gives a strong bridge from reviewed source to deployed agent behavior.

## Findings

### F-01 — Epistemic promotion is not enforced by the G2 accepted-state API
**Severity: HIGH**  
**Type: architectural / control-plane boundary**

`VersionedStateStore` requires `WRITE_ACCEPTED_STATE`, project binding and CAS, which correctly controls *actor authority*. It accepts an arbitrary Python value, however, with no trust class, provenance record, decision reference, independent evidence threshold or promotion grant.

Consequence: a fully authorized PRIMARY can persist a hallucinated or poisoned synthesis without the storage boundary knowing that the input is epistemically weak.

**Experimental mitigation implemented:** `ipg3_epistemic_authority.py`, promotion-grant schema, adversarial tests, and the accompanying protocol note.

### F-02 — Correlated swarm agreement can masquerade as confidence
**Severity: HIGH**  
**Type: epistemic / swarm**

The current architecture recognizes verification cells and conflicting evidence, but a generic validator count is not evidence independence. Multiple agents can share the same premise, source artifact, retrieval result or model failure mode.

Consequence: increasing swarm size can increase confidence faster than truth.

**Experimental mitigation implemented:** evidence independence is counted by source lineage, not agent count. Re-reading one source does not satisfy a two-lineage gate.

### F-03 — Artifact replacement does not enforce creator/owner continuity
**Severity: MEDIUM-HIGH**  
**Type: runtime integrity**

`ArtifactRegistry.replace` checks project, capability and version but does not require the replacing execution instance to own the artifact, nor a dedicated override capability. MANAGER and RESEARCH both hold `WRITE_ARTIFACTS`.

Consequence: a peer agent with the current version can replace another agent's artifact and become the recorded creator of the new version. Provenance remains attributable but ownership isolation is weaker than task ownership.

**Recommended production change:** distinguish artifact append/version authorship from replacement authority. Require owner instance or explicit integration/review override, and preserve creator separately from last modifier.

### F-04 — Delivery registration can validate shape without authenticating original sender
**Severity: MEDIUM**  
**Type: provenance / ingress**

`DeliveryLedger.register` validates a message without a `sender_session`. This is safe for effect authority because downstream mutation still requires local authorization, but a fabricated message object can potentially enter delivery state if supplied through a path that bypasses authenticated publication.

**Recommended production change:** delivery registration should consume an immutable persisted-message handle or authenticated ingress receipt, not a free-standing message dictionary.

### F-05 — Recursive enhancement local persistence bypasses the session/capability API
**Severity: MEDIUM**  
**Type: mutation consistency**

`RecursiveEnhancementEngine` carefully constrains writes beneath the local project root, but it receives no `AgentSession` and no capability. Candidate persistence therefore does not obey the otherwise global principle that mutation requires an ACTIVE bound session.

The writes are non-authoritative candidate state, which reduces consequence, but the exception should be explicit rather than accidental.

**Recommended production change:** either classify candidate cache writes as a deliberately non-authoritative local scratch plane or require a bounded capability such as `WRITE_WORKING_ARTIFACTS`.

### F-06 — Self-enhancement cycle persistence is not atomic
**Severity: MEDIUM-LOW**  
**Type: crash consistency**

Candidate files use temporary file + fsync + replace. Cycle files use direct `write_text`.

**Recommended change:** use the same atomic persistence discipline for cycle manifests.

### F-07 — Generic audit append is attributable but not authoritative
**Severity: MEDIUM-LOW**  
**Type: semantics**

Any ACTIVE bound session can append audit records because `AuditLedger.record` has no specific capability. This is defensible if the audit ledger is a record of attributed claims/events, not a source of truth. The distinction must remain explicit.

**Recommended change:** classify audit entries as execution evidence and avoid treating an audit statement itself as proof of the claimed event without corroborating state/effect evidence.

### F-08 — G2 cross-project approval is structurally weak
**Severity: MEDIUM**  
**Type: approval semantics**

The current exchange validator checks `approval.status == APPROVED` and `approved_by`, but does not consume a first-class one-shot approval object. PRIMARY capability is still required, so arbitrary lower-tier escalation is blocked.

IPG3 Human Approval v1 correctly addresses the missing replay/expiry/use semantics. Production promotion should use the stronger object before enabling a live cross-project bridge.

### F-09 — Design evolution transition function is intentionally non-authoritative but easy to misuse
**Severity: MEDIUM**  
**Type: future integration risk**

`transition_candidate` can represent `REVIEWED -> PRIMARY_ACCEPTED` without itself authenticating a Primary. The module correctly states that it has no mutation authority. A later integrator could nevertheless mistake a pure state-machine transition for authorization.

**Recommended change:** keep transition calculation pure, but require an external Primary-bound acceptance receipt/grant before durable state adopts `PRIMARY_ACCEPTED`.

### F-10 — Experimental branch divergence creates integration risk
**Severity: HIGH operational / LOW immediate security**  
**Type: release engineering**

At review time the experimental branch was 90 commits ahead of and 702 commits behind `main`, with a common merge base substantially behind both heads.

Consequence: direct promotion or runtime patching on this branch can resurrect stale production code or hide conflicts even when design CI is green.

**Required before production promotion:** rebase/reconstruct the IPG3 design on current `main`, rerun both G2 and IPG3 gates, and treat runtime changes made only on the divergent branch as prototypes, not production candidates.

## Threat model against large swarms

The kernel should assume all of the following can happen simultaneously:

- one or more agents hallucinate;
- many agents share the same hallucinated premise;
- retrieval returns stale or poisoned material;
- a manager compresses disagreement into false consensus;
- a correct decision is replayed against changed state;
- an approval is copied to a different target;
- an agent restarts and loses local context;
- a stale worker wakes after ownership has moved;
- a malicious or erroneous prompt claims a more privileged role;
- a peer project emits persuasive but untrusted artifacts;
- a model-generated proposal attempts to become configuration.

The existing identity/capability/lease/CAS model handles many of these. The epistemic authority gate addresses the last group: wrong-but-authorized cognition.

## New kernel invariant

The recommended invariant is:

> **Stochastic workers may generate claims, but only deterministic local governance may convert bounded, evidence-backed claims into protected state transitions.**

Operationally:

`model output -> trust/provenance record -> independent evidence -> validation -> decision -> narrowly-bound promotion grant -> normal session/capability/lifecycle checks -> CAS/effect commit -> receipt/audit`

No step may be skipped because multiple agents agree.

## Experimental implementation in this branch

This forensic review adds:

- `design/IPG3_EPISTEMIC_AUTHORITY_GATE.md`;
- `design/epistemic-promotion-grant-v1.draft.schema.json`;
- `design/ipg3_epistemic_authority.py`;
- `design/test_ipg3_epistemic_authority.py`;
- validation-harness inclusion.

The reference implementation enforces:

- no low-trust direct jump to authoritative configuration;
- evidence-lineage independence rather than validator-count independence;
- PRIMARY + `WRITE_ACCEPTED_STATE` + `APPROVE_CHANGE` for authoritative-config promotion;
- exact operation/resource/version/payload/instance binding;
- expiry;
- atomic single-use consumption.

## Promotion criteria before high-count swarm execution

Before increasing swarm count materially, the system should demonstrate all of these properties under adversarial tests:

1. a hallucinating research agent cannot alter accepted state;
2. a hallucinating manager cannot grant itself or children more authority;
3. ten correlated agents cannot satisfy a two-source evidence gate using one lineage;
4. stale approvals fail after resource-version changes;
5. payload substitution fails after review;
6. restarted instances cannot consume grants issued to prior instances;
7. disagreement survives synthesis instead of being silently averaged away;
8. failed branches can be discarded without damaging accepted state;
9. swarm resize recommendations cannot spawn agents without PRIMARY authorization;
10. no design-only artifact enters authoritative deployment closure before promotion.

## Primary follow-up / course load

The next PRIMARY that resumes this project should treat the following as required integration work rather than optional polish:

- reconcile the 702-commit `main` divergence before any production runtime merge;
- implement artifact ownership/override semantics on a current-main branch;
- bind delivery registration to authenticated persisted ingress;
- decide whether self-enhancement candidate persistence is governed working state or an explicitly separate scratch plane;
- make enhancement-cycle persistence atomic;
- bind `PRIMARY_ACCEPTED` evolution state to a durable Primary acceptance receipt;
- integrate the epistemic promotion gate with the future durable accepted-state adapter;
- add causal/audit events for grant issuance, denial, consumption, revocation and expiry;
- run correlated-hallucination and poisoned-evidence swarm campaigns at increasing agent counts;
- measure false promotion, missed promotion, cost, latency and convergence rather than accuracy alone.

## Conclusion

The architecture is already designed around a sound premise: model text is not authority. The remaining work is to make that premise complete at the epistemic boundary.

The safe scaling target is not "agents do not hallucinate." It is:

> **Hallucinations remain bounded candidate information unless independent evidence and explicit local governance convert them into a narrowly authorized effect.**

That property is what makes high-count swarms tolerable.
