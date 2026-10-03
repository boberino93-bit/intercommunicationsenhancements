# Hardening Status

Current target: **framework 1.5.0-alpha.1 / protocol 2.4.0-alpha.1**

This file records implementation state, not aspirational architecture. Historical package hashes from older releases are intentionally not presented as evidence for the current target.

## Implemented in repository

- **ENFORCED:** immutable project-binding primitive and same-project authorization guard.
- **ENFORCED + TESTED:** fail-closed agent lifecycle; non-`ACTIVE`/unbound sessions cannot authorize mutation.
- **ENFORCED + TESTED:** child binding inherits project/repository/workspace/protocol identity and receives a fresh execution-instance ID.
- **ENFORCED:** internal message bus rejects source/destination project mismatch and incompatible protocol versions.
- **ENFORCED:** message expiry, agent-instance identity, correlation/causation, and project-scoped idempotency protection.
- **ENFORCED + TESTED:** delivery acknowledgement lifecycle separates receipt, acceptance, execution, completion/failure/rejection.
- **ENFORCED + TESTED:** retries are bounded and preserve project/idempotency identity.
- **ENFORCED + TESTED:** malformed/unauthorized/cross-project/incompatible/expired input is kept out of normal execution and can be retained as quarantine evidence.
- **ENFORCED:** cross-project exchange remains a separate explicit validator and is denied without capability + approval.
- **ENFORCED + TESTED:** project-scoped expiring leases use execution-instance ownership and collision-resistant lease IDs; same-holder retries are idempotent; competing active holders are denied.
- **ENFORCED + TESTED:** expired leases are recoverable; a restarted execution instance cannot renew/release an earlier instance's lease.
- **ENFORCED + TESTED:** compare-and-set state mutation rejects stale expected versions.
- **ENFORCED + TESTED:** project lifecycle is independently versioned as `ACTIVE`, `DRAINING`, or `PAUSED`; one project's pause/drain does not stop peers.
- **ENFORCED:** repository/project path guards and project-qualified resource identifiers prevent ordinary cross-project/path-escape mutation.
- **ENFORCED:** capacity coordination preserves the configured 20% verified reserve and treats unknown hard limits as unknown rather than unlimited.
- **ENFORCED:** recursive self-enhancement peer observation remains read-only and local promotion remains review/Primary-gated.
- **ENFORCED:** scheduled Slack delivery remains explicit-destination external communication and does not replace canonical project state.
- **ENFORCED:** deployment package manifests reject foreign project identity and stale protocol/framework versions.
- **ENFORCED:** package verification rejects undeclared/foreign archive contents, role-instruction leakage, wrong filenames, incomplete/duplicate role sets, and source-revision disagreement.
- **DOCUMENTED + PACKAGED INPUTS:** Primary owns holistic project/package release consistency; Manager and Research retain lower default authority tiers and distinct control-plane responsibilities.
- **ENFORCED CI PIPELINE:** exact-SHA GitHub Actions pipeline runs tests, builds PRIMARY/MANAGER/RESEARCH ZIPs, verifies the coordinated release set, and publishes it as one workflow artifact.

## Current test coverage

The repository test suite now covers the earlier isolation/cross-project/package/self-enhancement/scheduled-task/capacity cases plus control-plane recovery cases including:

- same human-readable resource names in different project namespaces;
- foreign lease claim denial;
- idempotent same-instance lease retry;
- competing lease rejection;
- concurrent lease contention with one effective holder;
- lease expiry/recovery;
- stale execution-instance lease renewal rejection;
- compare-and-set stale-write rejection;
- independent project pause behavior;
- drain-completion behavior;
- unbound-agent mutation denial;
- child binding inheritance;
- foreign active-agent mutation denial;
- unsafe-message quarantine;
- duplicate delivery no-op behavior;
- acknowledgement lifecycle;
- bounded retry exhaustion;
- foreign acknowledgement denial;
- stale framework/protocol deployment package rejection.

## Deployment package release gate

The 1.5.0-alpha.1 package dependency map includes:

- `protocols/control_plane_recovery.md`;
- `org_agent_mesh/control_plane.py`;
- `org_agent_mesh/delivery.py`;
- lease, delivery, lifecycle-registry, and quarantine schemas;
- updated Primary/Manager/Research bootstrap contracts;
- all prior shared protocol layers (isolation, cross-project exchange, recursive self-enhancement, Slack scheduled tasks, capacity coordination).

The current branch is **NOT release-complete until exact-source CI has rebuilt and verified all three 1.5.0-alpha.1 ZIPs**. The final release evidence must identify the exact source revision, workflow result, package filenames, and archive hashes. Do not substitute the hashes of an older package generation.

## Partially enforced / remaining risks

- **PARTIALLY ENFORCED:** lease, compare-and-set, project-registry, and delivery ledgers are thread-safe reference-runtime implementations. A durable multi-process/distributed Artifactory or database adapter must provide equivalent atomic operations, expiry/recovery, and persistence semantics before those controls are considered distributed-runtime enforcement.
- **PARTIALLY ENFORCED:** the project registry contract and independent pause/drain behavior are implemented in the reference runtime; a persistent organizational registry/control service remains future work.
- **PARTIALLY ENFORCED:** cross-project exchange has a fail-closed capability/approval validator; a full sanitized export/import bridge service remains future work.
- **NOT IMPLEMENTED AS A GLOBAL SERVICE:** organization-wide observability/telemetry aggregation. Project-scoped evidence and identifiers exist, but a durable global query service is still a next layer.

## Release status

`HARDENING STATUS = INCOMPLETE` until the branch test/build/package workflow succeeds for the final source revision and the coordinated PRIMARY/MANAGER/RESEARCH artifacts are verified. After that evidence exists, the source-level hardening in this release may be marked complete for the current alpha scope while the distributed-backend risks above remain explicitly open.
