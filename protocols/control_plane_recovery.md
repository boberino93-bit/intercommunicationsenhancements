# Control Plane, Lease, Recovery, and Delivery Protocol

## Scope

This protocol defines the reference safety controls for project binding, mutation authorization, expiring work leases, stale-write prevention, project lifecycle isolation, delivery acknowledgements, bounded retries, and quarantine/dead-letter handling.

It is intentionally project-aware. Human-readable agent, task, artifact, lane, and message names are not globally authoritative identifiers.

## Agent lifecycle and binding

Reference lifecycle:

`UNBOUND -> BOUND -> INITIALIZED -> ACTIVE -> DRAINING -> TERMINATED`

An `UNBOUND`, `BOUND`, or merely `INITIALIZED` agent may inspect only what is required to establish and validate its project context. It may not authorize mutation. Mutable work requires an `ACTIVE` session with an immutable `ProjectBinding` containing project, repository/workspace, logical agent, execution-instance, and protocol identity.

Child agents inherit the parent's project, repository, workspace, and protocol binding. A child receives a fresh execution-instance ID. Task text never overrides inherited project identity.

## Project lifecycle

Each registered project has an independent lifecycle record:

- `ACTIVE`: ordinary authorized mutations are permitted.
- `DRAINING`: new mutations are denied; an operation explicitly marked as completion of already accepted work may finish.
- `PAUSED`: project mutations are denied until the project is explicitly returned to `ACTIVE`.

Lifecycle mutations use expected-version checks. One project's pause or drain state does not pause unrelated projects.

## Project-scoped leases

Exclusive or collision-sensitive work uses a project-qualified lease key. A lease records:

- `project_id`
- `resource_id`
- `holder_agent_instance_id`
- collision-resistant `lease_id`
- acquisition and expiry timestamps
- monotonically increasing lease version

Claim is atomic inside the reference registry. A retry from the same execution instance returns its existing active lease. A competing execution instance is denied while the lease is active. Expired leases are recoverable and may be reclaimed.

Renewal and release require both the original execution-instance identity and lease token. A restarted agent therefore cannot silently inherit an earlier process instance's lock.

## Compare-and-set mutation

Mutable state that can be concurrently updated uses an expected-version contract. A write succeeds only when `expected_version == current_version`. Stale updates fail rather than silently overwriting newer state.

The reference `VersionedStateStore` provides this behavior in-process. Production persistence adapters must preserve equivalent atomic compare-and-set semantics at their own storage boundary.

## Delivery acknowledgements

Delivery state is distinct from transport arrival. The supported reference lifecycle is:

`RECEIVED -> ACCEPTED -> STARTED -> COMPLETED`

Failure/rejection paths are explicit:

- `RECEIVED -> REJECTED`
- `ACCEPTED -> FAILED | REJECTED`
- `STARTED -> FAILED | REJECTED`
- `FAILED -> ACCEPTED` only through an authorized retry

`COMPLETED` and `REJECTED` are terminal.

Delivery records are keyed by project-qualified idempotency identity. Re-registering the same delivery is a safe no-op and does not increment execution count.

## Bounded retries

Retries are bounded by the delivery record's `max_attempts`. Retry preserves the same project and idempotency identity. Once the attempt budget is exhausted, the delivery remains failed until explicit higher-level disposition; it is not retried indefinitely.

Permanent identity/authorization failures are not normal retry candidates.

## Quarantine and expiry

Unsafe messages do not enter normal execution. Malformed, unauthorized, cross-project, protocol-incompatible, or otherwise invalid messages are persisted as diagnostic quarantine evidence when possible.

Expired messages receive an `EXPIRED` outcome and are also retained as diagnostic evidence. Quarantine preserves:

- local project context
- claimed project/message identity when available
- rejection reason
- payload digest
- timestamp
- original payload

Quarantine is evidence, not an execution queue. A quarantined payload must never become executable merely because it was persisted.

## Duplicate handling

An idempotency duplicate is a safe no-op or returns the previously known delivery state. Duplicate transport must not imply duplicate execution.

## Cross-project boundary

Ordinary internal delivery, lease, state mutation, acknowledgement, and project lifecycle operations require requester and target project identity to match. Cross-project exchange remains a separate capability- and approval-gated protocol. This control-plane protocol does not add a cross-project authority bypass.

## Persistence and atomicity status

The reference implementation uses thread-safe in-process registries to prove lifecycle, lease, CAS, acknowledgement, retry, and recovery semantics. These controls are **ENFORCED + TESTED in the reference runtime**.

Durable multi-process or distributed Artifactory/state adapters are **PARTIALLY ENFORCED** until their concrete storage implementation provides equivalent atomic claim, CAS, expiry/recovery, and append/quarantine guarantees. Any adapter that cannot provide those semantics must fail closed rather than weakening this contract.
