# IPG3 Design Status

Status: **EXPERIMENTAL / NON-AUTHORITATIVE**

Branch: `design/next-gen-intercommunication-protocols`

Stable baseline remains framework `1.6.0-alpha.1` / protocol `2.4.0-alpha.1` on `main`. No IPG3 design artifact is included in the current deployment dependency closure.

## Implemented in design branch

### Architecture

- full generational breakdown from empirical coordination through G3;
- IPG3 protocol architecture draft;
- compatibility and shadow-mode migration model;
- adversarial validation plan;
- benchmark suite and hard promotion thresholds;
- durable-state adapter semantic contract;
- external interoperability adapter contract;
- Adaptive Research & Swarm Regulation protocol for assistance detection, Primary sizing, manager/research topology, live resize and termination.

### Draft protocol objects

- Message v3;
- Delegation Contract v1;
- Effect Receipt v1;
- Human Approval v1;
- Trust and Provenance Record v1;
- Causal Event v1;
- Evolution Candidate v2;
- Benchmark Result v1;
- Progress Ledger / Stall Signal v1;
- Cross-Project Exchange v2;
- Agent Principal v1;
- Research Assistance Request v1;
- Swarm Allocation Decision v1;
- Swarm State v1.

### Executable design behavior

- deterministic Message v2 -> Message v3 shadow projection;
- semantic-equivalence assertion for protected v2 fields;
- sanitized offline Message v2 replay fixtures and replay metrics;
- cross-project exchange relational validation;
- human approval replay/expiry/use validation;
- atomic single-use approval consumption reference ledger;
- concurrent approval-consumer contention tests;
- effect prepare/commit/replay/unknown-state reference ledger;
- idempotency-digest collision rejection;
- delegation capability ceiling and scope validation;
- trust-promotion path validation;
- hash-linked causal-chain verification and tamper detection;
- authenticated-principal relational validation;
- backend-independent durable adapter API;
- black-box durable-adapter conformance suite;
- SQLite durability candidate with local/multi-process semantics;
- PostgreSQL durability candidate with server-backed multi-process/multi-node-capable semantics;
- CI-backed conformance validation of both SQLite and PostgreSQL candidates for exclusive create, CAS, consumable authorization, execution-instance leases, project isolation and append-only event collisions;
- benchmark-gated evolution candidate lifecycle with forbidden stage-skipping;
- unsafe, inferior, high-regression or non-reproducible candidate promotion rejection;
- progress/stall/convergence analyzer that returns repeated non-progress to the strategic evolution ledger;
- A2A 1.0 Agent Card/Task/Message/Artifact normalization prototype that preserves remote capability declarations only as discovery claims;
- AGNTCY/SLIM identity and directory normalization prototype with verified-identity evidence, local capability intersection and mandatory local principal issuance;
- adaptive assistance detector using confidence, attempts, stall, parallelism, dependency density, domain count, conflict, verification need, consequence, tool gaps, context pressure and novelty;
- three retained swarm-sizing generations for empirical comparison;
- v1 naive baseline field penalty `44`;
- v2 dependency/structural-trigger optimization field penalty `4`;
- v3 verification-cell/diminishing-return optimization field penalty `0` on the retained synthetic campaign;
- dynamic resize campaign covering under-allocation, duplicate work, new-domain coordination, verification gaps and anti-flapping, with target penalty `0` and four justified topology changes out of five cases;
- fail-closed assistance/allocation/swarm-state validators;
- explicit rule that only an ACTIVE bound Primary execution instance may authorize allocation or topology changes;
- forged Primary, budget-overrun, stale-revision, invalid-topology and draining-scale-up adversarial tests;
- unit/adversarial tests for the implemented design behaviors;
- design-only validation harness;
- design-only GitHub Actions validation workflow.

## Deliberately not claimed yet

- cryptographic signature verification service;
- issuer trust registry and credential revocation service;
- key creation/rotation/recovery implementation;
- a selected production durability backend;
- full durable integration of causal events, approvals, effects, tasks, artifacts and audit state into the active runtime;
- broker-specific delivery implementation;
- persistent organization registry;
- global observability aggregation;
- production sanitized cross-project bridge;
- production A2A/AGNTCY transport clients/servers (current work is normalization/mapping only);
- live shadow mirroring;
- representative large-scale replay corpus;
- real-world evidence that v3 is the optimal swarm-sizing policy for arbitrary tasks;
- production telemetry-derived false-positive/false-negative escalation rates;
- empirical benchmark results against G2 beyond regression/conformance gates and synthetic swarm policy campaigns;
- independent proposer/critic/verifier execution topology;
- complete OWASP/AgentDojo-style adversarial suite;
- G3 role package definitions;
- G3 migration tooling;
- official G3 framework/protocol version.

## Next gates

1. Keep both IPG3 design CI and the existing G2 package/reproducibility gate green.
2. Build a larger sanitized replay corpus covering every Message v2 kind and major failure class.
3. Add read-only adaptive-swarm telemetry to measure real assistance requests before any automatic allocation authority exists.
4. Measure unnecessary-escalation, missed-escalation, duplicate-work, manager-overhead, cost and convergence outcomes from real campaigns; use those results to challenge the retained synthetic expectations.
5. Produce formal Benchmark Result records comparing G2 with G3 candidate semantics and overhead.
6. Expand durable-adapter conformance with process-death, timeout-after-commit, restart persistence and partition/failover scenarios.
7. Compare PostgreSQL with at least one additional genuinely distributed persistence design before selecting a production substrate; SQLite remains a valuable local/reference candidate, not a multi-node choice.
8. Add a cryptographic verification interface with pluggable issuer/revocation/key services; do not hard-code one trust provider into the protocol.
9. Exercise A2A/AGNTCY mappings against real SDK/protocol fixtures and quantify translation loss before building production transport adapters.
10. Run independent adversarial review before any G3 artifact moves into authoritative runtime/package paths.

## Promotion rule

IPG3 remains in `design/` until the candidate implementation demonstrates non-inferiority to G2 on existing invariants and measurable superiority on the G3 target dimensions. Adaptive swarm sizing additionally requires real telemetry before its synthetic policy is treated as production-optimal. Promotion must include tests, adversarial tests, migration evidence, synchronized role packages, exact-revision manifests and reproducible release artifacts.
