# Intercommunications Enhancements

## Mission

Turn the Organization Agent Mesh seed framework into a hardened multi-project communications control plane that can safely support several autonomous project teams at the same time.

## Ownership boundary

This repository owns the reusable communication, identity, isolation, concurrency, cross-project exchange, deployment-package, and validation contracts. It does **not** own Duo Open or BenefitFlow domain implementation. Each downstream Primary remains responsible for its own project and its own synchronized Primary/Manager/Research deployment packages.

## Core invariants

1. Every active agent is bound to exactly one project.
2. Every mutable resource is owned by exactly one project.
3. Ordinary AgentBus traffic is intra-project only.
4. Cross-project exchange is explicit, capability-gated, approved, bounded, audited, and copy-by-value.
5. Missing or conflicting project identity fails closed.
6. Child agents inherit project identity.
7. Human-readable IDs are aliases; canonical identity is project-scoped.
8. Deployment packages declare project, role, protocol, framework, package version, and source revision.
9. Stale or foreign packages are rejected.
10. A protocol change is incomplete until affected role packages are rebuilt and validated.
