# Intercommunications Enhancements

Dedicated protocol-engineering project for hardening the Organization Agent Mesh into a fail-closed, multi-project intercommunications and deployment control plane.

This repository is seeded conceptually and technically from the uploaded `org-agent-mesh-framework-v1.0.0` package. Its purpose is to develop project isolation, deterministic message routing, concurrency safety, explicit cross-project exchange, synchronized agent deployment packages, and adversarial validation for several autonomous project teams operating simultaneously.

## Current hardening alpha

- `project_id` is treated as an authorization boundary, not descriptive metadata.
- Ordinary AgentBus traffic is intra-project only.
- Cross-project exchange is separate, explicit, deny-by-default, approval/capability-gated, and provenance-preserving.
- Agent execution identity is separated from human-readable role names.
- Lane/presence coordination is project-scoped.
- PRIMARY, MANAGER, and RESEARCH deployment packages are versioned and must match the running project protocol.
- Stale or foreign deployment packages are rejected.
- Protocol changes are incomplete until dependent agent packages are rebuilt and validated.
- GitHub Actions builds and verifies the three role deployment ZIPs from the exact commit SHA on every push to `main`.

Start with `PROJECT_CHARTER.md`, `ROADMAP.md`, and `START_HERE.md`.
