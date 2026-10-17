# Intercommunications Enhancements

Reference protocol-engineering project for hardening the Organization Agent Mesh into a fail-closed, multi-project intercommunication and deployment control plane.

**Canonical bootstrap generation: V26.**  
Framework/package semver remains **1.6.0-alpha.1** and protocol semver remains **2.4.0-alpha.1**; those are separate version axes from the V26 BIOS/bootstrap generation.

## V26 active contract

V26 is the current active generation. V25 R11 and earlier records remain preserved as historical lineage and evidence; they are not active bootstrap authority.

Startup is readiness-first:

`UNBOUND_READ_ONLY → VMBUS_READY → PRINCIPAL_CONTEXT_READY → PROJECT_BIND → project-scoped VMBUS/policy → task interpretation → normal authority gates`

`PROJECT_MANIFEST_V26.json` and `bootstrap/V26_BOOTSTRAP_ADAPTER.json` define the machine-readable V26 generation. `BOOTSTRAP_ORDER.json` is the active execution order.

The principal-context layers improve interpretation but never create identity proof, authentication, authority, consent, or mutation permission. External persistence is optional after standalone readiness; a GitHub write does not prove a ChatGPT Library AgentBus write and vice versa.

## Project separation

Intercommunication Enhancements is the **only shared coordination project**. Common protocols, schemas, interfaces and compatibility rules do not create common project state or common project authority.

- `SHARED_INTERCOMMUNICATION_PROTOCOL != SHARED_PROJECT_STATE`
- `COMMON_BOOTSTRAP_INTERFACE != COMMON_PROJECT_AUTHORITY`
- `PROJECT_A_VMBUS != PROJECT_B_VMBUS`
- `CROSS_PROJECT_DISCOVERY != CROSS_PROJECT_DATA_ACCESS`
- `CV_SUPPORT != FEDERATED_PROJECT`
- `INTERCOMMUNICATION_ENHANCEMENTS = ONLY_SHARED_COORDINATION_PROJECT`

CV Support remains fully non-federated and outside shared coordination state.

## Current hardening alpha

- `project_id` is an authorization boundary, not descriptive metadata.
- Mutations require a bound execution context plus the current case-bound authorization required by governance; self-asserted project IDs do not authorize anything.
- Canonical project/resource IDs are validated without lossy sanitization.
- Child agents inherit project/repository/protocol identity, receive a fresh execution instance, and cannot escalate parent capabilities.
- Ordinary AgentBus traffic is project-scoped; compatibility or discovery does not grant peer data access.
- Project-scoped leases, expected-version state mutation, task ownership, artifact provenance and audit attribution provide reference concurrency/recovery semantics.
- PRIMARY, MANAGER and RESEARCH packages must include the V26 manifest and V26 bootstrap adapter, are generated from the dependency map, and ship as one coordinated release set.
- CI/tests and package verification reject a stale pre-V26 bootstrap prefix or missing V26 package components.
- Protocol or architecture changes are incomplete while any dependent active surface or role package is stale.

Start with `START_HERE.md`, `PROJECT_MANIFEST_V26.json`, `bootstrap/V26_BOOTSTRAP_ADAPTER.json`, `BOOTSTRAP_ORDER.json`, `PROJECT_CHARTER.md`, and `ARCHITECTURE.md`.
