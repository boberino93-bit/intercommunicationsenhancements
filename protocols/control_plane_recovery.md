# Control Plane Recovery and Concurrency

Lifecycle is `UNBOUND -> BOUND -> INITIALIZED -> ACTIVE -> DRAINING -> TERMINATED`. Mutation APIs accept an active bound session, not self-asserted project/instance strings.

Leases are canonical project/resource keyed, execution-instance owned, expiring, idempotent for the same holder and exclusive against competitors. Restarted instances cannot renew/release a prior instance's lease.

Stale-sensitive mutation uses expected-version compare-and-set. Task claims/transitions are session/capability bound and versioned. Artifact publication/replacement records creator, task/provenance and SHA-256.

Message acceptance uses atomic exclusive creation keyed by project plus idempotency identity. Acknowledgements distinguish receipt from accepted, started and terminal execution. Retries are bounded. Unsafe/expired payloads are quarantined and never promoted.

`ACTIVE` accepts authorized work; `DRAINING` denies new mutation but can allow explicitly marked completion; `PAUSED` denies mutation. Lifecycle state is per project.

The in-process registries are reference semantics. Distributed adapters must preserve atomic claim, instance ownership, expiry, CAS and append-only evidence semantics or fail closed.
