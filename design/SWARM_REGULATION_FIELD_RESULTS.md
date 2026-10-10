# Adaptive Swarm Regulation — Field Test Results

Status: **DESIGN EVIDENCE — SYNTHETIC / NON-PRODUCTION**

The purpose of these campaigns is to test the semantics of escalation, sizing, manager allocation, resizing and authority boundaries before the subsystem has live agent-spawn authority.

## 1. Static sizing campaign

The retained campaign contains 11 operational scenarios:

1. routine local task;
2. first weak attempt;
3. single tool/capability gap;
4. conflicting evidence requiring verification;
5. small repeatedly stalled problem;
6. dependency-dense/sequential problem;
7. large parallel cross-domain problem;
8. critical three-front problem;
9. critical small novel problem;
10. broad but routine parallel work;
11. context-pressure-only case.

Penalty model:

- wrong escalate/no-escalate decision: `5` points;
- each researcher outside the expected range: `2` points;
- each manager outside the expected range: `2` points.

Lower is better. Zero means every retained scenario falls inside its expected operational range.

| Policy generation | Penalty | Main behavior |
|---|---:|---|
| v1 baseline | 44 | score-only admission; breadth-driven researchers; count-driven managers |
| v2 optimization | 4 | structural stall/parallel triggers; dependency-aware parallelism; lower manager overhead |
| v3 optimization | 0 | targeted verification capacity; novelty/risk interaction; diminishing returns; integration-based management |

The CI field script pins the exact `44 -> 4 -> 0` progression. A future policy change that alters these values fails the gate unless the expectations are explicitly re-baselined with justification.

### Material fixes learned from the campaign

- Raw workstream count badly over-allocates a dependency-dense problem; dependency density must reduce parallel capacity.
- Low confidence alone is not enough to justify a swarm.
- A weighted score alone can miss a repeatedly stalled task; sustained-stall structure matters.
- Broad genuinely parallel work can justify assistance even when no single signal is extreme.
- High consequence may require an independent verifier without requiring a Manager.
- Management should follow integration/coordination burden rather than researcher count alone.

## 2. Dynamic resize campaign

Five runtime scenarios test whether an already-authorized swarm adapts without topology flapping:

| Scenario | Start | Result | Expected behavior |
|---|---|---|---|
| sustained unresolved fronts | 2R / 0M | 4R / 0M | scale up |
| duplicate work / oversupply | 6R / 0M | 4R / 0M | scale down |
| newly discovered domains + disagreement | 6R / 0M | 6R / 1M | add coordination capacity |
| moderate duplicate/idle noise | 5R / 1M | 5R / 1M | no topology flap |
| newly discovered verification gap | 2R / 0M | 3R / 0M | add verifier |

Results:

- resize penalty: `0`;
- justified topology changes: `4 / 5`;
- no-flap scenario remained unchanged.

The test also asserts that resize cannot be used on a task that never passed swarm admission. New assistance demand outside an authorized swarm must go back through `ResearchAssistanceRequest` and Primary allocation.

## 3. Authority/adversarial campaign

Validated failure cases include:

- forged requester execution identity;
- attempt-count/evidence mismatch;
- Research agent posing as Primary allocator;
- allocation beyond Primary-approved researcher budget;
- manager budget/topology mismatch;
- stale swarm revision replay;
- Research agent attempting a topology change;
- DRAINING swarm attempting to scale up;
- termination that leaves active research/manager capacity.

The positive path also verifies:

- ACTIVE Research/Manager sessions may request assistance from their own identity;
- ACTIVE Primary may authorize an in-budget swarm;
- Primary may revision a swarm through allowed lifecycle transitions;
- termination reaches zero active capacity.

## 4. Optimization history

The subsystem intentionally retains v1, v2 and v3 policy functions instead of destructively replacing earlier logic. This allows the improvement mechanism to compare an incumbent and candidate under the same scenario corpus.

### Optimization 1

Problem observed:

- sequential work was treated as parallel;
- some stalled/broad problems were under-escalated;
- managers were allocated too mechanically.

Changes:

- dependency-density scaling;
- structural stall/parallel triggers;
- lower manager overhead.

Measured result: `44 -> 4` penalty.

### Optimization 2

Remaining problem:

- small novel/high-consequence work could receive excess researcher/manager capacity even when the real need was independent verification rather than coordination.

Changes:

- verification-pressure model;
- novelty/risk interaction;
- diminishing-return cap;
- integration-load-based manager allocation;
- runtime resize hysteresis.

Measured result: `4 -> 0` static penalty plus `0` dynamic penalty on the retained campaigns.

## 5. What these results do not prove

These are deterministic synthetic operational scenarios. They demonstrate that the protocol behaves according to the specified expectations and that the two candidate optimizations improve this retained corpus.

They do **not** prove that v3 is the globally optimal number of agents for real research tasks.

Production confidence requires read-only/live telemetry measuring:

- missed assistance requests;
- unnecessary assistance requests;
- success/quality by topology;
- duplicate-work rate;
- manager overhead;
- cost/token/time consumption;
- convergence speed;
- verification benefit;
- resize frequency and oscillation.

Real evidence may invalidate the current heuristic. If it does, the sizing policy should evolve through the same candidate/benchmark/promotion system rather than being treated as permanent truth.
