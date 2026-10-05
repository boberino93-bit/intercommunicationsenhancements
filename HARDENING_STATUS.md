# Hardening Status

Current target: **framework 1.6.0-alpha.1 / protocol 2.4.0-alpha.1**.

This file reports implementation truth. A revision is release-complete only when the exact revision's CI release gate succeeds.

## Enforced in the reference runtime / canonical bootstrap

- **ENFORCED + TESTED:** identity-first bootstrap and fail-closed identity lock.
- **ENFORCED + TESTED:** mutation authority derives from an `ACTIVE` immutable bound session; raw caller project strings cannot authorize mutation.
- **ENFORCED + TESTED:** canonical mutation-authorization governance now separates human intent from write authority (`INTENT != AUTHORIZATION`), rejects capability questions/design discussion/enthusiasm/role/claim/repository permission as standalone authorization sources, requires a bounded authorization envelope before external side effects, and preserves stronger exact-action gates for high-consequence operations.
- **ENFORCED + TESTED:** ambiguous interactive mutation authorization fails closed for the affected write while safe read-only analysis/validation may continue.
- **ENFORCED + TESTED:** generic human-launched project agents without an explicit role enter demand-driven roleless admission rather than defaulting to PRIMARY; PRIMARY self-promotion and MASTER self-selection are denied, and role/claim never substitute for mutation authorization.
- **ENFORCED + TESTED:** explicit role capabilities and child non-escalation.
- **ENFORCED + TESTED:** canonical identifiers are validated without lossy sanitization.
- **ENFORCED + TESTED:** internal message publication requires bound sender identity and `PUBLISH_MESSAGE`; no cross-project internal override exists.
- **ENFORCED + TESTED:** atomic project-scoped message idempotency, acknowledgement lifecycle, bounded retries, expiry and quarantine.
- **ENFORCED + TESTED:** cross-project exchange requires source binding, capability, approval, requesting-agent agreement and unexpired scope.
- **ENFORCED + TESTED:** execution-instance-owned expiring leases, stale-instance rejection and compare-and-set stale-write prevention.
- **ENFORCED + TESTED:** crash-durable SQLite reference persistence for accepted state and leases, including transactional CAS, project-qualified keys, restart recovery, concurrent-writer exclusion, checksum validation and fail-closed schema-version fencing.
- **ENFORCED + TESTED:** independent project lifecycle; project-scoped task ownership/versioning, artifact provenance/content hashing, and attributable append-only reference audit records.
- **ENFORCED + TESTED:** dynamic scheduled-task routes capture project identity, authorized role, forum/artifact namespaces and repository identity from the local project contract; generated launch context is verified against that contract before mutation.
- **ENFORCED + TESTED:** scheduled launch reference admission state machine, bounded concurrent starts, deterministic staggering, minimum start spacing, bounded exponential backoff/jitter, attempt caps and the rule that project task state cannot advance before `BOOTSTRAP_READY`.
- **ENFORCED:** path guards, capacity reserve, read-only recursive self-enhancement and explicit-destination Slack controls remain packaged.

## Deployment package enforcement

- **ENFORCED:** deterministic dependency map for shared and role-specific package inputs.
- **ENFORCED:** shared patterns include every runtime module, schema and protocol document, including scheduled-launch/admission code and schemas.
- **ENFORCED:** manifest v3 records exact source revision, role/tier/capabilities, dependency-map hash and component hashes.
- **ENFORCED:** verifier recomputes source dependency closure and rejects omissions/extras, source/hash drift, foreign role files, wrong project/repository, stale framework/protocol or mixed revisions.
- **ENFORCED:** `release-set.json` binds PRIMARY/MANAGER/RESEARCH archive hashes to one revision.
- **ENFORCED CI GATE:** tests, exact-SHA build, verification, independent rebuild and byte-for-byte reproducibility comparison precede publication.

## Remaining risks

- **PARTIALLY ENFORCED:** the mutation-authorization hard gate is canonical in bootstrap/governance and covered by deterministic regression tests, but the ChatGPT/provider host does not expose a universal repository-independent pre-tool interceptor controlled by this repository. A model or external integration that bypasses the canonical bootstrap could still attempt a write. Projects should therefore combine this policy with least-privilege connector scopes, protected branches/review gates, and tool-level consequence controls where available.
- **PARTIALLY ENFORCED:** roleless admission is policy/bootstrap-enforced; safe high-concurrency self-assignment still depends on each project exposing sufficiently fresh demand state and a reliable claim/lease/fence mechanism. If that coordination surface is unavailable, generic agents are required to remain read-only for conflicting work rather than guessing ownership.
- **PARTIALLY ENFORCED:** the provider-admission controller is a tested reference component, but it prevents provider overload only when the actual scheduler/dispatcher can execute it before model invocation. Where ChatGPT's scheduler does not expose a pre-invocation hook, deterministic schedule staggering plus retry/reconciliation is the available mitigation; a model run cannot self-retry a request rejected before it starts.
- **PARTIALLY ENFORCED:** accepted state and leases now have a crash-durable single-node reference backend. Task, artifact, audit, project-registry, scheduled-occurrence and delivery ledgers remain thread-safe/in-process or protocol-level references, and a multi-node/distributed backend must still demonstrate equivalent atomicity, ownership, expiry/recovery and CAS semantics before being treated as production-conformant.
- **PARTIALLY ENFORCED:** pause/drain exists in reference runtime; persistent organization-wide lifecycle service remains future work.
- **PARTIALLY ENFORCED:** cross-project exchange has a fail-closed validator; durable sanitized bridge remains future work.
- **PARTIALLY ENFORCED:** swarm-learning policy and bootstrap inheritance are defined, but a concrete durable learning-registry/promotion service remains future work.
- **NOT IMPLEMENTED AS A GLOBAL SERVICE:** organization-wide observability aggregation.

## Release status rule

`HARDENING STATUS = COMPLETE FOR CURRENT ALPHA SCOPE` only for an exact commit whose CI release gate succeeds and publishes the synchronized PRIMARY/MANAGER/RESEARCH release set. Before that exact evidence exists, status is **INCOMPLETE**.
