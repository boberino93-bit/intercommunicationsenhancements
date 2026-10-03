# Intercommunications Architecture

## Purpose

This project hardens the Organization Agent Mesh control plane for simultaneous unrelated projects. It separates global infrastructure from project-owned execution state and makes project identity an enforceable authorization boundary.

## Topology

```text
GLOBAL / ORGANIZATIONAL CONTROL PLANE
├── protocol definitions
├── read-visible project registry contract
├── capacity/advisory signals
├── observability (future distributed service)
└── explicit cross-project bridge (validator implemented; service remains future work)

PROJECT A                         PROJECT B
├── bound agent sessions          ├── bound agent sessions
├── tasks / lanes / leases        ├── tasks / lanes / leases
├── messages / delivery ledger    ├── messages / delivery ledger
├── quarantine evidence           ├── quarantine evidence
├── versioned state / artifacts   ├── versioned state / artifacts
├── presence / lifecycle          ├── presence / lifecycle
├── repository binding            ├── repository binding
└── deployment packages           └── deployment packages
```

Global infrastructure may know that projects exist; ordinary project execution may not silently merge their state.

## Identity hierarchy

Canonical operations carry enough identity to resolve:

`organization → project_id → repository/workspace → agent_id → agent_instance_id → task/lane → resource`

Human-readable aliases such as `researcher-01`, `task-001`, or `latest-analysis` may repeat in multiple projects. They are not global identifiers.

An agent begins `UNBOUND`. Mutation is denied until it is immutably bound, initialized, and `ACTIVE`. Child agents inherit the parent's project/repository/workspace/protocol binding and receive a fresh execution-instance identity. Task semantics do not select or override project identity.

## Internal messaging

Protocol `2.4.0-alpha.1` requires explicit source/destination project identity, sender execution-instance identity, correlation/causation, idempotency, and expiry fields. Ordinary AgentBus traffic requires matching source and destination project IDs. A mismatch is rejected rather than auto-routed.

Delivery state is separate from transport receipt. Acknowledgement-required work distinguishes `RECEIVED`, `ACCEPTED`, `STARTED`, `COMPLETED`, `FAILED`, and `REJECTED`. Retries are bounded and preserve project/idempotency identity. Unsafe or expired messages do not enter normal execution; they are retained as quarantine/dead-letter evidence.

## Concurrency and recovery

Collision-sensitive work uses project-scoped expiring leases keyed by resource and owned by a specific agent execution instance. The same holder may retry a claim idempotently; competing instances are denied until release/expiry. Renew/release requires the holder instance and lease token. Expired leases are recoverable, and a restarted execution instance cannot silently inherit an old lock.

Stale-sensitive state mutation uses expected-version compare-and-set. A stale writer fails rather than overwriting a newer state version.

The reference runtime implements these primitives with thread-safe in-process registries. Durable multi-process or distributed persistence adapters must provide equivalent atomic semantics at their own storage boundary or fail closed.

## Project lifecycle isolation

Each project has an independently versioned lifecycle state:

- `ACTIVE`: authorized mutation may proceed.
- `DRAINING`: no new mutable work; explicitly marked completion of already accepted work may finish.
- `PAUSED`: project mutation is denied.

Pausing or draining one project does not suspend unrelated projects.

## Cross-project exchange

Cross-project communication is not a special case of the internal bus. It uses a separate exchange contract with explicit source/destination projects, purpose, classification, artifact scope, allowed use, expiry, correlation, capability, and approval. Default policy is DENY. Data should cross by value as a bounded sanitized snapshot with provenance.

The current implementation contains the fail-closed exchange validator. A full durable cross-project bridge service remains future work.

## Deployment roles and authority

Deployment role and authority tier are separate concepts:

- PRIMARY → ORCHESTRATOR by default
- MANAGER → REVIEWER by default
- RESEARCH → SPECIALIST by default

Role naming never elevates authority. Each role ZIP carries the shared protocol/runtime plus its role-specific bootstrap contract. Shared control-plane code therefore does not give Research or Manager Primary authority.

## Release consistency

The Primary owns project-level release coherence. Changes to identity, routing, schemas, bootstrap, capabilities, artifact ownership, repository/workspace resolution, capacity, lifecycle, lease/CAS behavior, delivery recovery, or role responsibility trigger package dependency analysis. Affected role packages must be rebuilt from an exact source revision and validated before the change is considered complete.

The CI release path checks out an exact source SHA, runs the repository test suite, builds all three role ZIPs from that SHA, verifies their manifests/components, and publishes them as one coordinated artifact set.

## Current enforcement status

Implemented in the reference runtime:

- immutable project binding and same-project authorization;
- child project-identity inheritance with fresh execution-instance IDs;
- fail-closed internal message routing and explicit cross-project exchange validation;
- project-scoped idempotency, expiry, delivery acknowledgements, bounded retries, and quarantine;
- project-scoped expiring leases with expiry/recovery and execution-instance ownership;
- compare-and-set stale-write rejection;
- independent `ACTIVE` / `DRAINING` / `PAUSED` project lifecycle controls;
- package compatibility checks and synchronized PRIMARY/MANAGER/RESEARCH build inputs;
- capacity reserve, recursive self-enhancement, and scheduled-task transport controls from prior protocol layers.

Still requiring a stronger production layer:

- durable multi-process/distributed lease and CAS storage adapter with equivalent atomicity;
- persistent global registry/observability service rather than only the reference registry contract;
- full cross-project bridge service beyond the existing validator;
- destination-specific durable acknowledgement transport where a concrete message broker is introduced.
