# Intercommunications Architecture

## Purpose

This project hardens the Organization Agent Mesh control plane for simultaneous unrelated projects. It separates global infrastructure from project-owned execution state and makes project identity an enforceable authorization boundary.

## Topology

```text
GLOBAL CONTROL PLANE
├── protocol definitions
├── project registry (planned Alpha 3)
├── global agent registry (planned Alpha 3)
├── observability (planned Alpha 3)
└── explicit cross-project bridge (planned Alpha 3)

PROJECT A                         PROJECT B
├── agents                       ├── agents
├── tasks / lanes                ├── tasks / lanes
├── messages                     ├── messages
├── artifacts / evidence         ├── artifacts / evidence
├── presence / leases            ├── presence / leases
├── repository binding           ├── repository binding
└── deployment packages          └── deployment packages
```

Global infrastructure may know that projects exist; ordinary project execution may not silently merge their state.

## Identity hierarchy

Canonical operations carry enough identity to resolve:

`organization → project_id → repository/workspace → agent_id → agent_instance_id → task/lane → resource`

Human-readable aliases such as `researcher-01`, `task-001`, or `latest-analysis` may repeat in multiple projects. They are not global identifiers.

## Internal messaging

Protocol `2.0.0-alpha.1` adds explicit source/destination project identity, sender execution-instance identity, correlation/causation, idempotency, and expiry fields. Ordinary AgentBus traffic requires matching source and destination project IDs. A mismatch is rejected as a policy violation rather than auto-routed.

## Cross-project exchange

Cross-project communication is not a special case of the internal bus. It uses a separate exchange contract with explicit source/destination projects, purpose, classification, artifact scope, allowed use, expiry, correlation, and approval. Default policy is DENY. Data should cross by value as a bounded sanitized snapshot with provenance.

## Deployment roles and authority

Deployment role and authority tier are separate concepts:

- PRIMARY → ORCHESTRATOR by default
- MANAGER → REVIEWER by default
- RESEARCH → SPECIALIST by default

Role naming never elevates authority. Each role ZIP carries the shared protocol plus its role-specific bootstrap contract.

## Release consistency

The Primary owns project-level release coherence. Changes to identity, routing, schemas, bootstrap, capabilities, artifact ownership, repository/workspace resolution, or role responsibility trigger package dependency analysis. Affected role packages must be rebuilt from an exact source revision and validated before the change is considered complete.

## Current vs planned

Alpha 1 implements project binding, fail-closed internal routing, explicit exchange validation, project-scoped lanes/presence, deployment package compatibility checks, and adversarial tests. Alpha 2 adds atomic leases, compare-and-set mutation, acknowledgements, bounded retries, quarantine/dead-letter handling, and crash recovery. Alpha 3 introduces the global registry/control-plane services and independent project pause/drain behavior.
