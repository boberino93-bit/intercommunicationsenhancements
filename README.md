# Intercommunications Enhancements

Reference protocol-engineering project for hardening the Organization Agent Mesh into a fail-closed, multi-project intercommunications and deployment control plane.

Current target: **framework 1.6.0-alpha.1 / protocol 2.4.0-alpha.1**.

## Current hardening alpha

- `project_id` is an authorization boundary, not descriptive metadata.
- Mutations require an `ACTIVE` immutable bound execution session plus the required capability; self-asserted project IDs do not authorize anything.
- Canonical project/resource IDs are validated without lossy sanitization.
- Child agents inherit project/repository/protocol identity, receive a fresh execution instance, and cannot escalate parent capabilities.
- Ordinary AgentBus traffic is intra-project only; cross-project exchange is a separate deny-by-default approved capability boundary.
- Project-scoped leases, expected-version state mutation, task ownership, artifact provenance and audit attribution provide reference concurrency/recovery semantics.
- PRIMARY, MANAGER and RESEARCH packages are generated from a dependency map, contain manifest v3 capability/source/component hashes, and ship as one coordinated release set.
- CI runs tests, builds exact-SHA packages, verifies dependency closure and source hashes, rebuilds independently, and rejects non-reproducible archives.
- Protocol or architecture changes are incomplete while any dependent role package is stale.

Start with `PROJECT_CHARTER.md`, `ROADMAP.md`, `START_HERE.md`, and `ARCHITECTURE.md`.
