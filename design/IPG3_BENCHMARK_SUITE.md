# IPG3 Benchmark Suite v1

Status: **DESIGN GATE**

IPG3 may not be promoted merely because its new tests pass. It must demonstrate non-inferiority on G2 invariants and measurable improvement on the G3 target dimensions.

## Baseline

Baseline candidate: validated framework `1.6.0-alpha.1` / protocol `2.4.0-alpha.1` exact release revision.

Every benchmark run must identify the exact baseline revision, candidate revision, suite revision and environment.

## Hard security gates

These are binary. Any regression is disqualifying regardless of performance improvement.

- cross-project ordinary-message rejection: 100%;
- forged caller project identity rejection: 100%;
- child capability escalation rejection: 100%;
- stale execution-instance lease rejection: 100%;
- stale CAS mutation rejection: 100%;
- expired message rejection/quarantine: 100%;
- package source/component hash mismatch rejection: 100%;
- mixed role/revision package rejection: 100%;
- approval replay beyond authorized use count: 100%;
- effect idempotency digest collision rejection: 100%;
- duplicate committed effect produces no second commit: 100%;
- untrusted/reflection content direct-to-authoritative promotion rejection: 100%;
- causal history tamper detection: 100% for covered mutations.

## Reliability metrics

Measure at minimum:

- message delivery convergence under duplicate/reordered delivery;
- effect recovery after crash at each prepare/commit/receipt boundary;
- approval-consumption correctness under concurrent consumers;
- lease recovery time after process death;
- stale-write rejection rate;
- duplicate work rate across delegated agents;
- successful task recovery after agent-instance replacement;
- false completion rate;
- quarantine false-positive/false-negative rates for defined fixtures.

Promotion target: no degradation in existing G2 reliability gates; new G3 protected effects and approvals must converge safely in all modeled retry/crash scenarios.

## Communication metrics

- envelope serialization size;
- processing latency per validation stage;
- projection success rate from Message v2;
- percentage of projected messages missing principal identity;
- percentage missing delegation contracts;
- percentage missing approval identity when approval is relevant;
- percentage lacking event sequence;
- semantic-class ambiguity rate;
- causal reconstruction completeness.

Initial shadow target before live dual validation: >= 99% successful deterministic projection of the representative non-malformed v2 corpus, with every failure classified rather than silently repaired.

## Delegation quality metrics

For research/manager swarms measure:

- duplicate research rate;
- scope-overlap rate;
- out-of-scope tool/write attempts;
- incomplete evidence contracts;
- manager rejection rate due to ambiguous assignment;
- task completion per delegated token/tool cost;
- handoff recovery success.

Candidate improvement target: materially lower duplicate/scope-conflict rate without reducing evidence coverage.

## Evolution metrics

- novel evidence gained per cycle;
- repeated-action rate;
- equivalent-proposal rate;
- candidates rejected before implementation due to threat modeling;
- regressions caught pre-promotion;
- failed-idea rediscovery rate;
- benchmark reproducibility rate;
- rollback success rate;
- complexity change versus measurable benefit.

The optimizer is considered improved only when it raises useful discovery/validation yield without weakening promotion discipline.

## Interoperability metrics

For each adapter candidate:

- lossless mapping of required IPG3 identity fields;
- lossless task/correlation mapping;
- preservation of idempotency and expiry;
- explicit representation of unsupported semantics;
- local re-authorization before mutation;
- adapter failure isolation;
- version negotiation behavior;
- untrusted remote capability descriptor rejection rate.

No adapter may obtain authority merely because a remote protocol considers a request valid.

## Cost/performance metrics

Track but never trade away hard security gates for:

- validation CPU time;
- persistent writes per completed task;
- bytes persisted per event;
- message amplification;
- telemetry overhead;
- package size;
- agent/tool/token cost per successful task.

## Benchmark outcome

A candidate receives one of:

- `SUPERIOR`: all hard gates pass and at least one target dimension improves materially with no material regression;
- `NON_INFERIOR`: all hard gates pass and no material regression, but gains are insufficient to justify promotion alone;
- `INFERIOR`: measurable regression without compensating required value;
- `UNSAFE`: any hard security invariant fails;
- `INCONCLUSIVE`: evidence/reproducibility is insufficient.

Only `SUPERIOR` or explicitly justified `NON_INFERIOR` components may proceed to architectural review. Neither outcome bypasses Primary/release gates.
