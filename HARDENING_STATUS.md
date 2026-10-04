# Hardening Status

Current target: **framework 1.6.0-alpha.1 / protocol 2.4.0-alpha.1**.

This file reports implementation truth. A revision is release-complete only when the exact revision's CI release gate succeeds.

## Enforced in the reference runtime

- **ENFORCED + TESTED:** identity-first bootstrap and fail-closed identity lock.
- **ENFORCED + TESTED:** mutation authority derives from an `ACTIVE` immutable bound session; raw caller project strings cannot authorize mutation.
- **ENFORCED + TESTED:** explicit role capabilities and child non-escalation.
- **ENFORCED + TESTED:** canonical identifiers are validated without lossy sanitization.
- **ENFORCED + TESTED:** internal message publication requires bound sender identity and `PUBLISH_MESSAGE`; no cross-project internal override exists.
- **ENFORCED + TESTED:** atomic project-scoped message idempotency, acknowledgement lifecycle, bounded retries, expiry and quarantine.
- **ENFORCED + TESTED:** cross-project exchange requires source binding, capability, approval, requesting-agent agreement and unexpired scope.
- **ENFORCED + TESTED:** execution-instance-owned expiring leases, stale-instance rejection and compare-and-set stale-write prevention.
- **ENFORCED + TESTED:** crash-durable SQLite reference persistence for accepted state and leases, including transactional CAS, project-qualified keys, restart recovery, concurrent-writer exclusion, checksum validation and fail-closed schema-version fencing.
- **ENFORCED + TESTED:** independent project lifecycle; project-scoped task ownership/versioning, artifact provenance/content hashing, and attributable append-only reference audit records.
- **ENFORCED:** path guards, capacity reserve, read-only recursive self-enhancement and explicit-destination Slack controls remain packaged.

## Deployment package enforcement

- **ENFORCED:** deterministic dependency map for shared and role-specific package inputs.
- **ENFORCED:** shared patterns include every runtime module, schema and protocol document.
- **ENFORCED:** manifest v3 records exact source revision, role/tier/capabilities, dependency-map hash and component hashes.
- **ENFORCED:** verifier recomputes source dependency closure and rejects omissions/extras, source/hash drift, foreign role files, wrong project/repository, stale framework/protocol or mixed revisions.
- **ENFORCED:** `release-set.json` binds PRIMARY/MANAGER/RESEARCH archive hashes to one revision.
- **ENFORCED CI GATE:** tests, exact-SHA build, verification, independent rebuild and byte-for-byte reproducibility comparison precede publication.

## Remaining risks

- **PARTIALLY ENFORCED:** accepted state and leases now have a crash-durable single-node reference backend. Task, artifact, audit, project-registry and delivery ledgers remain thread-safe in-process references, and a multi-node/distributed backend must still demonstrate equivalent atomicity, ownership, expiry/recovery and CAS semantics before being treated as production-conformant.
- **PARTIALLY ENFORCED:** pause/drain exists in reference runtime; persistent organization-wide lifecycle service remains future work.
- **PARTIALLY ENFORCED:** cross-project exchange has a fail-closed validator; durable sanitized bridge remains future work.
- **NOT IMPLEMENTED AS A GLOBAL SERVICE:** organization-wide observability aggregation.

## Release status rule

`HARDENING STATUS = COMPLETE FOR CURRENT ALPHA SCOPE` only for an exact commit whose CI release gate succeeds and publishes the synchronized PRIMARY/MANAGER/RESEARCH release set. Before that exact evidence exists, status is **INCOMPLETE**.
