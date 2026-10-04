# Intercommunications Enhancements

## Mission

Turn the Organization Agent Mesh seed framework into a hardened, rapidly reusable multi-project communications control plane that safely supports several autonomous project teams at once.

## Ownership boundary

This repository owns reusable communication, identity, authorization, isolation, concurrency, cross-project exchange, deployment-package and validation contracts. It does **not** own Duo Open, BenefitFlow, or other downstream domain implementation. Each downstream Primary remains responsible for its project and synchronized deployable role packages.

## Core invariants

1. Every active agent is immutably bound to exactly one project and execution instance.
2. Mutation authority comes from the active bound session plus capabilities, never a self-asserted project ID.
3. Child agents inherit project/repository/protocol identity and cannot escalate parent capabilities.
4. Mutable resources belong to one project; canonical identifiers are validated without lossy normalization.
5. Ordinary AgentBus traffic is intra-project and claimed sender identity must match the bound session.
6. Cross-project exchange is explicit, capability-gated, approved, bounded, provenance-preserving and copy-by-value.
7. Missing/conflicting/foreign identity fails closed; invalid input is retained only as non-executable quarantine evidence.
8. Collision-sensitive work uses project-scoped execution-instance leases; stale-sensitive writes use expected versions.
9. Deployment packages declare project, role, capability set, protocol/framework/package versions, dependency-map hash, source revision and component hashes.
10. Package dependency closure is recomputed from source; a protocol/framework change is incomplete until affected roles are rebuilt, verified and reproducible.
