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
- external interoperability adapter contract.

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
- Agent Principal v1.

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
- unit/adversarial tests for the implemented design behaviors;
- design-only validation harness;
- design-only GitHub Actions validation workflow.

## Deliberately not claimed yet

- cryptographic signature verification service;
- issuer trust registry and credential revocation service;
- key creation/rotation/recovery implementation;
- durable causal event backend;
- durable approval/effect backend;
- broker-specific delivery implementation;
- durable distributed lease/CAS/task/artifact/audit adapters;
- persistent organization registry;
- global observability aggregation;
- production sanitized cross-project bridge;
- A2A/AGNTCY transport adapters;
- live shadow mirroring;
- representative large-scale replay corpus;
- empirical benchmark results against G2;
- independent proposer/critic/verifier execution topology;
- complete OWASP/AgentDojo-style adversarial suite;
- G3 role package definitions;
- G3 migration tooling;
- official G3 framework/protocol version.

## Next gates

1. Keep design CI green as the design evolves.
2. Build a larger sanitized replay corpus covering every Message v2 kind and failure class.
3. Produce first benchmark-result records comparing G2 with the G3 candidate semantics.
4. Implement a black-box durable-adapter conformance suite.
5. Prototype at least two genuinely multi-process/multi-node-capable persistence candidates against that suite before choosing infrastructure.
6. Add a cryptographic verification interface with pluggable issuer/revocation/key services; do not hard-code one trust provider into the protocol.
7. Add live read-only shadow mirroring only after offline replay coverage is representative.
8. Prototype A2A and AGNTCY mappings as isolated adapters and quantify translation loss.
9. Expand failure injection around crash-after-effect-commit / before-receipt persistence and unknown-outcome reconciliation.
10. Run independent adversarial review before any G3 artifact moves into authoritative runtime/package paths.

## Promotion rule

IPG3 remains in `design/` until the candidate implementation demonstrates non-inferiority to G2 on existing invariants and measurable superiority on the G3 target dimensions. Promotion must include tests, adversarial tests, migration evidence, synchronized role packages, exact-revision manifests and reproducible release artifacts.
