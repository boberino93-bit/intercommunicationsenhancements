# Hardening Status

Canonical bootstrap generation: **V26**.  
Framework/package target: **1.6.0-alpha.1**. Protocol target: **2.4.0-alpha.1**.

This file reports implementation truth. V25 R11 and earlier records are preserved historical lineage, not current bootstrap authority. A revision is release-complete only when the exact revision's applicable release gates succeed; known pre-existing red conditions must remain visible rather than being described as green.

## Enforced in the reference runtime / canonical bootstrap

- **V26 CANONICAL CONTRACT:** startup begins `UNBOUND_READ_ONLY`; `VMBUS_READY` and `PRINCIPAL_CONTEXT_READY` are required before project binding, and principal-context readiness is required before task interpretation.
- **V26 CANONICAL CONTRACT:** `PROJECT_MANIFEST_V26.json`, `bootstrap/V26_BOOTSTRAP_ADAPTER.json`, and `BOOTSTRAP_ORDER.json` define the active generation. Pre-V26 artifacts are lineage/evidence only.
- **V26 CANONICAL CONTRACT:** principal context/model synthesis/chronology do not create identity proof, authentication, authority, consent, or mutation permission.
- **V26 CANONICAL CONTRACT:** Intercommunication Enhancements is the only shared coordination project; shared interface/protocol does not share project state, authority, evidence, authorization, or VMBUS namespaces. CV Support is explicitly non-federated.
- **ENFORCED + TESTED:** after V26 standalone readiness, project binding and fail-closed identity controls scope project-local work.
- **ENFORCED + TESTED:** mutation authority derives from an `ACTIVE` immutable bound session plus the required current case-bound authorization; raw caller project strings cannot authorize mutation.
- **ENFORCED + TESTED:** canonical mutation-authorization governance separates human intent from write authority (`INTENT != AUTHORIZATION`) and preserves stronger exact-action gates for high-consequence operations.
- **ENFORCED + TESTED:** ambiguous interactive mutation authorization fails closed for the affected write while safe read-only analysis/validation may continue.
- **ENFORCED + TESTED:** generic human-launched project agents without an explicit role enter demand-driven roleless admission rather than defaulting to PRIMARY; PRIMARY self-promotion and MASTER self-selection are denied, and role/claim never substitute for mutation authorization.
- **ENFORCED + TESTED:** explicit role capabilities and child non-escalation.
- **ENFORCED + TESTED:** canonical identifiers are validated without lossy sanitization.
- **ENFORCED + TESTED:** internal message publication requires bound sender identity and `PUBLISH_MESSAGE`; no implicit cross-project internal override exists.
- **ENFORCED + TESTED:** atomic project-scoped message idempotency, acknowledgement lifecycle, bounded retries, expiry and quarantine.
- **ENFORCED + TESTED:** base cross-project exchange requires source binding, `CROSS_PROJECT_EXCHANGE`, explicit approval, requesting-agent agreement and unexpired scope; discovery alone is not data access.
- **ENFORCED + TESTED:** cross-project operational-intelligence semantics separate passive knowledge, discovery, expertise/capability/managerial awareness, routing requests and verified active execution; active-participation claims require matching canonical assignment evidence.
- **ENFORCED + TESTED:** project-local sanitized peer discovery registry preserves explicit freshness/availability and rejects unsanitized extra fields, stale entries and authority-bearing metadata.
- **ENFORCED + TESTED:** cross-project routing lineage rejects cycles; target-project acceptance/decline and later update/supersession states use explicit non-authoritative receipts, and acceptance is not represented as active execution.
- **ENFORCED + TESTED:** sanitized snapshot bridge provides immutable two-phase source export/destination import under explicit approved exchange; imported state remains `accepted_state=false` / `authority_conveyed=false`.
- **ENFORCED + TESTED:** execution-instance-owned expiring leases, stale-instance rejection and compare-and-set stale-write prevention.
- **ENFORCED + TESTED:** crash-durable SQLite reference persistence for accepted state and leases, including transactional CAS, project-qualified keys, restart recovery, concurrent-writer exclusion, checksum validation and fail-closed schema-version fencing.
- **ENFORCED + TESTED:** independent project lifecycle; project-scoped task ownership/versioning, artifact provenance/content hashing, and attributable append-only reference audit records.
- **ENFORCED + TESTED:** dynamic scheduled-task routes capture project identity, authorized role, coordination/artifact namespaces and repository identity from the local project contract; generated launch context is verified against that contract before mutation.
- **ENFORCED + TESTED:** scheduled launch reference admission state machine, bounded concurrent starts, deterministic staggering, minimum start spacing, bounded exponential backoff/jitter, attempt caps and the rule that project task state cannot advance before `BOOTSTRAP_READY`.
- **ENFORCED + TESTED:** layered-context bootstrap treats observable authorized inputs as potentially context-bearing while preserving provenance, temporal state, contradictions, and the separation between context presence, evidence quality, and authority.
- **ENFORCED:** path guards, capacity reserve, read-only recursive self-enhancement and explicit-destination Slack controls remain packaged.

## V26 persistence boundary

Standalone VMBUS readiness does not depend on an external persistence service. After readiness:

- GitHub is the canonical versioned source/governance and durable backup surface represented by this repository.
- The ChatGPT Library AgentBus, when exposed by the runtime, is the live project coordination stream at `/Intercommunication enhancements/AgentBus/messages`.
- Legacy fields named `ARTIFACTORY` or `INTERNAL_ARTIFACTORY` are historical/internal labels and must not be silently interpreted as JFrog Artifactory.
- `GITHUB_WRITE != AGENTBUS_WRITE`; neither is evidence that the other occurred.
- No ChatGPT Library AgentBus write/readback is claimed from a runtime that does not expose a write-capable transport.

## Deployment package enforcement

- **ENFORCED:** deterministic dependency map for shared and role-specific package inputs.
- **V26 ENFORCED:** every role package dependency closure explicitly includes `PROJECT_MANIFEST_V26.json` and `bootstrap/V26_BOOTSTRAP_ADAPTER.json`.
- **V26 ENFORCED:** package build rejects a bootstrap order that does not place V26 VMBUS/principal-context readiness before project binding.
- **V26 ENFORCED:** package verifier rejects missing V26 components, stale generation metadata, or a packaged pre-V26 bootstrap prefix.
- **ENFORCED:** manifest v3 records exact source revision, role/tier/capabilities, dependency-map hash and component hashes; V26 build metadata additionally identifies the canonical generation and V26 component paths.
- **ENFORCED:** verifier recomputes source dependency closure and rejects omissions/extras, source/hash drift, foreign role files, wrong project/repository, stale framework/protocol or mixed revisions.
- **ENFORCED:** `release-set.json` binds PRIMARY/MANAGER/RESEARCH archive hashes to one revision and identifies V26 as the canonical bootstrap generation.
- **RELEASE GATE:** tests, exact-SHA build, verification, independent rebuild and reproducibility comparison precede claiming a synchronized role-package release.

## Remaining risks / visible limitations

- **PARTIALLY ENFORCED:** repository/bootstrap governance cannot guarantee that a host or external integration which entirely bypasses the canonical bootstrap will honor repository-defined pre-tool gates. Least-privilege connector scopes, protected branches/review gates, and host/tool consequence controls remain important defense layers.
- **PARTIALLY ENFORCED AT THE HOST BOUNDARY:** repository policy cannot disable or inspect the host product's internal memory subsystem. Host-supplied current conversation/project context may be observable as ephemeral context, but it is not swarm authority or mutation permission.
- **PARTIALLY ENFORCED:** roleless admission is policy/bootstrap-enforced; safe high-concurrency self-assignment still depends on sufficiently fresh demand state and reliable claim/lease/fence mechanisms.
- **PARTIALLY ENFORCED:** provider admission prevents overload only when the actual scheduler/dispatcher can execute it before model invocation. Where the host does not expose a pre-invocation hook, deterministic staggering plus retry/reconciliation is the available mitigation.
- **PARTIALLY ENFORCED:** accepted state and leases have a crash-durable single-node reference backend. Other registries remain thread-safe/in-process or protocol-level references; a multi-node backend must demonstrate equivalent atomicity, ownership, expiry/recovery and CAS semantics before being treated as production-conformant.
- **PARTIALLY ENFORCED:** persistent organization-wide lifecycle/observability and a concrete durable learning-registry/promotion service remain future production layers.
- **KNOWN BASELINE TEST LIMITATIONS:** the pre-alignment main lineage already recorded repository-suite red conditions involving the pytest runner dependency and a bootstrap-continuity `native_memory` identifier. V26 canonical alignment does not silently relabel those as fixed; focused V26/package checks and full-suite results must be reported separately.

## Release status rule

`HARDENING STATUS = COMPLETE FOR CURRENT ALPHA SCOPE` only for an exact commit whose required release gates succeed and whose synchronized PRIMARY/MANAGER/RESEARCH package evidence is available. Until that evidence exists for the aligned V26 revision, status is **V26 CANONICAL ALIGNMENT IN VALIDATION**, not globally green.
