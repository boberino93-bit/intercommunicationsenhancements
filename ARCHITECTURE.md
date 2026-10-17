# Intercommunications Architecture

## Purpose and active generation

Intercommunication Enhancements is the reference hardening project for the Organization Agent Mesh. It provides the shared coordination protocol/interface while preserving each project's independent state, authority, evidence, authorization boundary, and VMBUS namespace.

**Canonical bootstrap generation: V26.** Framework/package semver remains **1.6.0-alpha.1** and protocol semver remains **2.4.0-alpha.1**; those are separate version axes.

V25 R11 and earlier artifacts remain preserved lineage/evidence only and are not current bootstrap authority.

## V26 readiness-first bootstrap

Execution begins with `PROJECT_MANIFEST_V26.json`, `bootstrap/V26_BOOTSTRAP_ADAPTER.json`, and `BOOTSTRAP_ORDER.json`.

The active ordering is:

`UNBOUND_READ_ONLY → initialize/validate VMBUS → VMBUS_READY → load R10 corrected principal context + R11 revisable model synthesis + V26 direct chronology → build epistemic/privacy/chronology/synthesis indexes → PRINCIPAL_CONTEXT_READY → PROJECT_BIND → project-scoped VMBUS/policy → project/task recovery → capability discovery → optional external persistence reconciliation → task interpretation/execution under normal authority gates`

This order corrects the former project-binding-first topology. Project identity remains a critical authorization boundary, but project binding is now a **post-readiness** operation. `VMBUS_READY` and `PRINCIPAL_CONTEXT_READY` must exist first.

Principal context, synthesis, chronology, continuity, ownership, confidence, or conversational familiarity do not create identity proof, authentication, authority, consent, or mutation permission.

## Project separation

Intercommunication Enhancements is the **only shared coordination project**. Shared interface compatibility is not shared mutable state.

- `SHARED_INTERCOMMUNICATION_PROTOCOL != SHARED_PROJECT_STATE`
- `COMMON_BOOTSTRAP_INTERFACE != COMMON_PROJECT_AUTHORITY`
- `PROJECT_A_VMBUS != PROJECT_B_VMBUS`
- `CROSS_PROJECT_DISCOVERY != CROSS_PROJECT_DATA_ACCESS`
- `CV_SUPPORT != FEDERATED_PROJECT`
- `INTERCOMMUNICATION_ENHANCEMENTS = ONLY_SHARED_COORDINATION_PROJECT`

CV Support remains fully non-federated. Other projects may adopt compatible intercommunication interfaces while retaining their own bootstrap, policy, state, evidence and authorization boundaries.

## Project binding and execution identity

After V26 readiness, canonical operations resolve `project_id -> repository/workspace -> agent_id -> agent_instance_id -> task/resource -> capability`.

`ProjectBinding` is immutable for the bound execution instance. Lifecycle remains `UNBOUND -> BOUND -> INITIALIZED -> ACTIVE -> DRAINING -> TERMINATED`. Protected mutation requires the applicable project/session controls plus the current case-bound authorization required by governance. Caller-supplied project strings, context similarity, role, or possession of a connector do not authorize mutation.

Scheduled project context is routing evidence, not mutation authority. Missing, malformed, or conflicting scheduled context fails closed for the affected branch and may not silently switch projects.

## VMBUS and persistence surfaces

The V26 embedded/virtual memory bus is initialized before project binding. Once the project is known, state is projected into a project-scoped namespace and policy boundary.

Standalone readiness does not require GitHub, ChatGPT Library AgentBus, Slack, JFrog, or another external service. After readiness, persistence surfaces are independent:

- GitHub is the canonical versioned source/governance and durable backup surface represented by this repository.
- The ChatGPT Library AgentBus, when actually exposed to a runtime, is the live coordination stream at `/Intercommunication enhancements/AgentBus/messages`.
- Legacy repository labels containing `ARTIFACTORY` or `INTERNAL_ARTIFACTORY` are historical/internal labels and must not be silently interpreted as JFrog Artifactory.
- Record equivalence requires the same logical record identity and verified payload SHA-256.
- Conflicts are preserved and surfaced; they are not silently resolved by last-writer-wins.
- `GITHUB_WRITE != AGENTBUS_WRITE`.
- Unavailable transport must be disclosed; an unperformed external write may not be claimed as performed.

## Authority and authentication

Authority tier and capability set are separate. Child agents inherit project/repository/protocol identity, receive fresh execution-instance IDs, and may not escalate beyond parent capability.

The authority chain preserves these separations:

`CLAIMED_IDENTITY != AUTHENTICATED_IDENTITY != AUTHORIZATION`

Human intent, ownership, role, connector access, project context, principal-context readiness, or a prior consumed authorization are not reusable write authority. High-consequence mutations use the repository's current case-bound authorization and independent-proof controls.

## Messaging and coordination

Ordinary coordination is project-scoped. Messages carry explicit project and sender identity, correlation/causation, idempotency and expiry. Cross-project discovery or metadata awareness does not grant cross-project data access.

Explicit cross-project exchange, where permitted, is bounded, copy-by-value, provenance-preserving, and non-authoritative at import unless the destination project separately accepts/promotes it. Imported intelligence does not inherit source-project authority.

CV Support is excluded from federation and is not a target for shared discovery or exchange under V26.

## Tasks, artifacts, leases and state

Project-scoped task ownership, artifact provenance/content hashes, expected-version state transitions, execution-instance-owned leases, stale-instance rejection and compare-and-set provide the reference concurrency model.

The SQLite reference backend remains a single-node durability implementation for selected accepted state/lease paths. A distributed adapter is conformant only if it preserves equivalent atomicity, isolation, ownership, expiry/recovery and CAS semantics; otherwise it must fail closed.

Projects retain independent lifecycle state. Pausing or draining one project does not imply pausing unrelated projects.

## Layered context and evidence

V26 separates three principal-context classes:

1. R10 corrected direct-user context.
2. R11 model synthesis, explicitly revisable and non-authoritative.
3. V26 direct-user chronology.

Those classes must not silently collapse into one another or into established fact. Provenance, chronology, contradiction, uncertainty and privacy/relevance boundaries remain visible. Retrieval failure is not absence of evidence, parser/runtime failure is not source corruption, and preserved/materialized data is not automatically verified/inspected.

## Swarm learning

Learning remains cumulative operational intelligence, not model-weight training. Raw experience is non-authoritative; validated knowledge requires appropriate validation; operating doctrine requires explicit promotion. Repetition or multi-agent agreement does not by itself create truth or authority.

Learning state is project-local. Shared coordination does not allow one project's raw experience, doctrine or accepted state to become another project's state by default.

## Scheduler and sequencing

V26 canonical promotion/alignment does not mutate scheduler enable/disable state.

Research → Manager → Primary sequencing is checkpoint/readiness/fencing-gated, not trusted merely because wall-clock schedules are staggered. A downstream stage that fires before required upstream state exists must wait or continue only independent safe work; it must not manufacture readiness from clock order.

## Packaging and dependency closure

`packaging/agent_package_dependencies.json` is authoritative package dependency closure. Every PRIMARY, MANAGER and RESEARCH package must include:

- `PROJECT_MANIFEST_V26.json`
- `bootstrap/V26_BOOTSTRAP_ADAPTER.json`
- `BOOTSTRAP_ORDER.json`
- project identity/routing controls
- required governance/protocol/runtime/schema dependencies
- its own role-specific bootstrap/instructions and no foreign role instructions

Build and verification require the V26 readiness-first prefix. Generated package/release metadata identifies `canonical_bootstrap_generation = V26` while framework/package semver stays `1.6.0-alpha.1`.

## Release gate and implementation truth

A revision is not globally green merely because V26 metadata exists. The release process separates focused V26 canonical-alignment validation from unrelated pre-existing suite failures and reports both accurately.

The intended release sequence is:

`tests → exact-SHA package build → V26/package verification → independent rebuild → reproducibility comparison → authorized promotion → main readback`

Known pre-alignment repository-suite red conditions involving the pytest runner dependency and a bootstrap-continuity `native_memory` identifier remain visible until separately repaired and validated. V26 alignment does not silently relabel them as fixed.

## Remaining production layers

The alpha still needs complete distributed/multi-node durable adapters, host-independent enforcement for some pre-tool consequences, persistent organization-wide lifecycle/observability, broker-specific durable acknowledgement transport, concrete durable learning-registry/promotion infrastructure, and host/scheduler integration capable of enforcing provider admission before model invocation. These limitations do not change the V26 bootstrap precedence or project-isolation contract.
