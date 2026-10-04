# IPG3 Adaptive Research & Swarm Regulation

Status: **DESIGN DRAFT — NON-AUTHORITATIVE — NOT PACKAGED**

This subsystem defines how an IPG3 agent recognizes that a task exceeds its local research capacity, communicates that need to the Primary agent, and receives an explicitly authorized research/manager topology. It also defines how an active swarm may be resized or terminated as evidence changes.

It does **not** give Research or Manager agents authority to spawn agents.

---

## 1. Core invariant

> An agent may detect, explain, and recommend a need for additional intelligence capacity. Only the bound ACTIVE Primary execution instance may authorize a swarm allocation or topology change.

Research/Manager requests are evidence. They are not authority.

---

## 2. Control loop

```text
LOCAL ATTEMPT
  -> ASSISTANCE NEED ASSESSMENT
  -> ResearchAssistanceRequest
  -> PRIMARY REVIEW
  -> SwarmAllocationDecision
  -> DELEGATION CONTRACTS / CELL ASSIGNMENTS
  -> SwarmState ACTIVE
  -> OBSERVE PROGRESS / DUPLICATION / STALL / DISAGREEMENT
  -> PRIMARY RESIZE / RESTRUCTURE / DRAIN / TERMINATE
  -> RESULTS CONVERGE TO PRIMARY
```

If an agent that is not currently part of an authorized swarm discovers a new need, it MUST return to `ResearchAssistanceRequest`; it MUST NOT call resize semantics to bypass admission control.

---

## 3. Assistance detection

The detector evaluates multiple signals rather than treating low confidence as sufficient by itself.

Signals currently modeled:

- confidence;
- local attempt count;
- repeated stall count;
- independently parallelizable workstreams;
- dependency density between workstreams;
- number of domains;
- conflicting evidence;
- explicit independent-verification requirement;
- consequence of a wrong answer;
- unavailable tool/capability;
- context pressure;
- novelty.

### Hard triggers

The current candidate treats these as direct escalation evidence:

- a tool/capability gap that another authorized worker may satisfy;
- conflicting evidence combined with a need for independent verification.

### Structural triggers

Field testing added structural escalation because a weighted score alone missed important cases:

- sustained local stall after repeated attempts and low confidence;
- broad genuinely parallel work after multiple attempts.

A single weak attempt MUST NOT, by itself, cause swarm creation.

---

## 4. ResearchAssistanceRequest v1

Any ACTIVE Primary, Manager, or Research session may submit a request from its own immutable project/execution identity.

The request carries:

- project/task/requester identity;
- unresolved problem;
- confidence and complexity signals;
- recorded local attempts;
- evidence gaps;
- proposed workstreams;
- source references;
- policy version that triggered the request.

Relational validation requires the requester identity to match the bound ACTIVE session and `attempt_count` to match the recorded attempts.

A request MUST NOT contain spawn authority.

Recommended Message v3 mapping:

- `class = CONTROL`
- `kind = RESEARCH_ASSISTANCE_REQUEST`
- recipient = project Primary
- acknowledgement policy = `EXECUTION`

---

## 5. Primary sizing responsibility

The Primary decides whether to reject, partially accept, or accept the request and determines:

- number of Research agents;
- number of Manager agents;
- workstream decomposition;
- cell topology;
- budget ceilings;
- maximum evaluation cycles;
- reasons for the allocation.

The sizing algorithm is advisory to Primary policy and MUST remain replaceable/evolvable.

### Research sizing principle

Research capacity should follow **executable parallel fronts**, not raw question count.

High dependency density reduces useful parallelism.

Independent verification is added only when evidence conflict, consequence, verification requirements, or novelty justify it.

The current v3 candidate applies a diminishing-return cap of approximately two researchers per effective front, with an overall design cap of 12 in the reference policy.

### Manager sizing principle

Management capacity follows integration load, not researcher count alone.

Inputs include:

- number of domains;
- cross-workstream dependency;
- number of effective parallel fronts;
- disagreement/integration burden discovered at runtime.

Small coherent or verification-focused teams remain Primary-direct even when the subject is high consequence.

---

## 6. SwarmAllocationDecision v1

Only an ACTIVE Primary session may authorize this object.

The decision binds:

- the original assistance request;
- exact research/manager counts;
- topology;
- cells/workstreams;
- budget ceilings;
- decision rationale;
- status.

Validators reject:

- non-Primary authorization;
- forged/stale Primary execution identity;
- project mismatch;
- wrong assistance-request linkage;
- researcher or manager budget overrun;
- topology/count mismatch;
- cell totals that differ from the aggregate allocation;
- rejected decisions that still allocate capacity.

Recommended Message v3 mapping:

- `class = DECISION`
- `kind = SWARM_ALLOCATION_DECISION`
- acknowledgement policy = `EXECUTION`

---

## 7. Cell topology

Reference topologies:

### PRIMARY_DIRECT

Normally 1–3 research agents or a small coherent expert/verification cell.

Primary directly integrates results.

### SINGLE_MANAGER_CELL

One Manager coordinates one research cell where coordination/integration burden warrants separation from Primary.

### MULTI_MANAGER_CELLS

Multiple non-overlapping workstream cells, each coordinated by a Manager, converge through Primary.

Managers coordinate work and enforce delegated scope. They MUST NOT expand the total allocation, issue new authority, or expand child capability ceilings without Primary authorization.

---

## 8. Runtime observation

An active swarm should emit measurable coordination signals rather than relying only on agent intuition.

Current reference observations:

- unresolved parallel fronts;
- stalled cycles;
- duplicate-work rate;
- idle rate;
- newly discovered domains;
- cross-agent disagreement rate;
- verification gaps.

Future observational metrics should include cost per useful finding, evidence quality, handoff latency, delegation accuracy, convergence time, and manager coordination overhead.

---

## 9. Resize policy

Resize produces a recommendation/next state; Primary authorization is still mandatory.

### Scale up

Scale-up is justified by sustained unmet parallel demand or a newly identified verification gap.

### Scale down

Scale-down is justified by clear duplicate work or idle capacity.

### Add management

Manager capacity may increase if new domains, disagreement, or integration burden appears while the campaign is active.

### Hysteresis

Moderate one-cycle noise MUST NOT continuously grow/shrink the swarm. The reference policy requires stronger oversupply or sustained unresolved-demand signals before resizing.

This reduces topology flapping.

---

## 10. SwarmState v1

Swarm state is revisioned. Reference lifecycle:

```text
AUTHORIZED -> ACTIVE -> SCALING -> ACTIVE
                    \-> DRAINING -> TERMINATED
                    \-> TERMINATED
```

Only an ACTIVE bound Primary may authorize transitions.

Invariants:

- project/swarm/task identities are immutable;
- every accepted state change increments revision exactly once;
- stale revision replay fails closed;
- DRAINING cannot scale up;
- TERMINATED has zero active research/manager capacity;
- non-terminated states require research capacity;
- topology must match current counts.

Recommended Message v3 kinds:

- `SWARM_SCALE_UP`
- `SWARM_SCALE_DOWN`
- `SWARM_RESTRUCTURE`
- `SWARM_DRAIN`
- `SWARM_TERMINATE`

All are `CONTROL` or `DECISION` messages and require Primary authority.

---

## 11. Research recursion

A Research agent may discover that one of its assigned questions requires additional investigation.

It does **not** recursively spawn descendants.

It emits a new assistance request linked to its task/delegation contract. Primary may:

- reject it;
- assign another existing researcher;
- expand the current cell;
- create a new cell;
- add a Manager;
- restructure the whole swarm.

This preserves global capacity awareness and prevents uncontrolled agent-tree growth.

---

## 12. Field-testing method

The reference design retains policy generations instead of overwriting the baseline so improvements can be compared.

### v1 — naive baseline

- score-only admission;
- researcher count roughly follows workstream count;
- managers mostly follow researcher-count ratios.

Known pathologies:

- misses some sustained-stall/broad-parallel cases;
- over-allocates sequential work;
- creates managers where risk requires verification rather than coordination.

### v2 — first optimization

Adds:

- structural stall/parallel triggers;
- dependency-density adjustment;
- lower manager overhead.

### v3 — second optimization

Adds:

- targeted independent-verification capacity;
- novelty/risk interaction;
- diminishing-return caps;
- management based on integration load;
- live resize hysteresis.

The CI field campaign MUST show v2 outperforming v1 and v3 outperforming v2 on the retained synthetic scenario corpus. If a new policy does not improve the test, it is not called an optimization.

A separate dynamic campaign tests scale-up, scale-down, manager addition, verification expansion, and no-flap behavior.

---

## 13. Limits of current evidence

The current field campaigns are deterministic synthetic operational tests. They validate policy semantics and failure modes; they do **not** yet establish the optimal swarm size for real-world model tasks.

Before production promotion, the framework should collect sanitized real campaign outcomes and compare:

- quality/success against agent counts;
- duplicate work;
- manager overhead;
- cost/token/time consumption;
- convergence speed;
- missed-escalation rate;
- unnecessary-escalation rate;
- resize frequency;
- independent-verification benefit.

Those empirical records should eventually train/tune an evolvable sizing policy, but the learned policy MUST remain behind the same Primary authorization and benchmark gates.

---

## 14. Promotion requirement

Adaptive swarm regulation remains under `design/` until:

1. static and dynamic field tests pass;
2. authority/lifecycle adversarial tests pass;
3. the complete IPG3 design gate passes;
4. existing Generation 2 package/reproducibility gates remain green;
5. live read-only telemetry has enough evidence to evaluate false/true escalation rates;
6. independent adversarial review finds no authority bypass;
7. a separate promotion decision moves the objects/runtime into authoritative paths.
