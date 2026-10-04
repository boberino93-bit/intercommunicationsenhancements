# IPG3 Durable State Adapter Contract

Status: **NON-AUTHORITATIVE DESIGN**

The infrastructure product is not the protocol. Any backend may be used only if it preserves these semantics. A backend that cannot provide them must fail closed or be limited to data classes that do not require them.

## Required logical stores

A conformant production control plane will require durable stores for at least:

- project registry and lifecycle;
- bound agent/execution-instance registry;
- leases;
- compare-and-set state;
- task ownership and transitions;
- artifact provenance/version records;
- message acceptance/idempotency;
- delivery/acknowledgement state;
- approval consumption;
- effect preparation/commit/reconciliation;
- causal/audit events;
- trust/provenance records;
- evolution candidates and benchmark results.

These may share physical infrastructure but remain logically separated and project-scoped.

## Atomicity classes

### A1 — exclusive create

Used for message/effect/idempotency identities.

Requirement: concurrent creates for the same qualified identity result in exactly one effective new record. Losing attempts observe the existing identity; they do not create parallel effective state.

### A2 — compare-and-set

Used for stale-sensitive mutable state.

Requirement: update applies only when the durable current version equals the caller's expected version. Version comparison and write are one atomic operation.

### A3 — lease claim/renew/release

Requirement: lease identity is project-qualified and holder identity includes execution instance. Claim is exclusive until expiry; renewal/release requires the current holder; a restarted instance cannot inherit another instance's lease.

### A4 — consumable authorization

Used for human approval.

Requirement: verifying remaining uses and incrementing/consuming the approval are one atomic operation. Two concurrent consumers cannot both spend the same final use.

### A5 — effect commit record

Requirement: idempotency identity and request digest are atomically associated. A repeated key with another request digest is a conflict. Commit/reconciliation state must survive worker loss.

### A6 — append-only causal evidence

Requirement: accepted causal/audit records cannot be silently rewritten. Correction occurs by additional events/supersession. Hash-chain or equivalent integrity evidence must detect historical mutation.

## Transactional boundaries

Do not demand one global transaction for all project work. Define the smallest correctness boundary needed for each invariant.

Examples:

- approval consume + local effect authorization should be atomic enough that a crash cannot make one approval appear unspent after an authorized effect begins;
- external side effects cannot generally share a database transaction with local state, so use prepare/effect/reconcile semantics rather than claiming impossible distributed exactly-once transactions;
- task state and artifact publication may use a transaction when artifact metadata and task version are stored together, or causal evidence must make partial completion recoverable.

## Consistency

Strong consistency is required for ownership/authorization decisions that cannot tolerate two simultaneous winners.

Eventual consistency may be used for derived observability/read models only when those models are never used as authority for mutation.

Examples suitable for eventually consistent read models:

- dashboards;
- aggregate metrics;
- historical search indexes;
- cost summaries;
- non-authoritative capacity visualization.

Examples not suitable without additional protocol:

- lease ownership;
- approval remaining uses;
- active project lifecycle gate;
- effect idempotency identity;
- CAS mutation version.

## Failure behavior

Adapters must define outcomes for:

- process death before commit;
- process death after commit before response;
- duplicate request;
- timeout with unknown commit status;
- network partition;
- replica lag;
- primary failover;
- clock skew where TTL/lease expiry is used;
- storage exhaustion;
- schema/version skew.

Unknown commit outcome must not be converted to success or blind retry. It enters a recoverable `UNKNOWN`/reconciliation state when safety requires it.

## Time semantics

Lease/expiry correctness must not depend on arbitrary worker-local wall clocks when a backend can provide authoritative transaction/server time. Clock source must be explicit and testable.

## Project isolation

Every durable key must be project-qualified or stored in a project-isolated namespace whose mapping is injective and validated.

An adapter API must not accept a raw caller project string as authorization. The calling control plane supplies an already validated bound-session context; the adapter verifies or receives the qualified identity produced from it.

## Adapter capabilities

Each adapter declares supported guarantees, for example:

- `EXCLUSIVE_CREATE`;
- `COMPARE_AND_SET`;
- `LEASE_TTL`;
- `ATOMIC_COUNTER_CONSUME`;
- `TRANSACTIONAL_BATCH`;
- `APPEND_ONLY_LOG`;
- `SERVER_TIME`;
- `WATCH_STREAM`;
- `MULTI_PROCESS`;
- `MULTI_NODE`.

The framework maps logical stores only onto adapters whose declared and tested guarantees meet the store requirements.

## Conformance suite

Every candidate backend must pass the same black-box suite:

1. 100+ concurrent exclusive-create contenders -> one winner;
2. stale CAS under concurrent writers -> stale writers rejected;
3. lease contention/expiry/restart -> no stale-instance inheritance;
4. concurrent final approval-use consumers -> one winner;
5. effect idempotency collision -> digest mismatch rejected;
6. timeout-after-commit simulation -> recover existing committed identity;
7. process death during prepare/commit -> safe reconciliation;
8. project-A/project-B identical resource names -> no collision;
9. pause/drain one project -> unrelated project proceeds;
10. history tamper attempt -> detected or prohibited;
11. storage restart -> durable state preserved;
12. multi-process execution -> semantics unchanged;
13. multi-node mode, when claimed -> semantics unchanged under node loss/partition tests.

## Infrastructure selection rule

Do not select a backend because it is popular or already available. Score candidate infrastructures against this contract, operational requirements, deployment environment, cost, observability, backup/restore and failure characteristics.

A backend may be excellent for one store and unsuitable for another. IPG3 permits composable adapters rather than requiring one database/broker to solve every control-plane problem.
