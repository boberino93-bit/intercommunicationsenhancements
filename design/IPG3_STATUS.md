# IPG3 Design Status

Status: **EXPERIMENTAL / NON-AUTHORITATIVE**

Branch: `design/next-gen-intercommunication-protocols`

Stable baseline remains framework `1.6.0-alpha.1` / protocol `2.4.0-alpha.1` on `main`. No IPG3 design artifact is included in the current deployment dependency closure.

## Implemented in design branch

### Architecture

- full generational breakdown from empirical coordination through G3;
- IPG3 protocol architecture draft;
- compatibility and shadow-mode migration model;
- adversarial validation plan.

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
- Cross-Project Exchange v2.

### Executable design behavior

- deterministic Message v2 -> Message v3 shadow projection;
- semantic-equivalence assertion for protected v2 fields;
- cross-project exchange relational validator;
- human approval replay/expiry/use validator;
- effect receipt replay/order validator;
- unit/adversarial tests for the initial behavior set;
- design-only validation harness;
- design-only GitHub Actions validation workflow.

## Not yet authoritative or production-complete

- authenticated principal implementation;
- key management, signing, rotation and revocation;
- durable causal event store;
- durable approval consumption store;
- exactly-once-effect coordinator;
- broker adapter;
- durable distributed lease/CAS/task/artifact/audit adapters;
- persistent organization registry;
- global observability service;
- production sanitized cross-project bridge;
- A2A/AGNTCY adapters;
- live shadow mirroring;
- benchmark corpus and threshold policy;
- independent proposer/critic/verifier execution topology;
- complete OWASP/AgentDojo-style adversarial suite;
- G3 role package definitions;
- G3 migration tooling;
- official G3 framework/protocol version.

## Immediate next gates

1. Design CI must pass all current draft/schema/test checks.
2. Add runtime-safe validation for delegation contracts and trust promotions.
3. Add causal-chain verification including hash predecessor and cycle checks.
4. Add approval-consumption atomicity model and crash/retry tests.
5. Add effect coordinator state machine with unknown-commit recovery semantics.
6. Define benchmark suites for security, reliability, interoperability, recovery, cost and duplicate-work rate.
7. Add offline replay fixtures from sanitized Message v2 examples.
8. Run shadow projection across a representative message corpus and quantify missing G3 information.
9. Prototype at least two durable-state backends against the same semantic contract before selecting infrastructure.
10. Prototype external interoperability as adapters, not as internal authority replacements.

## Promotion rule

IPG3 remains in `design/` until the candidate implementation demonstrates non-inferiority to G2 on existing invariants and measurable superiority on the G3 target dimensions. Promotion must include tests, adversarial tests, migration evidence, synchronized role packages, exact-revision manifests and reproducible release artifacts.
