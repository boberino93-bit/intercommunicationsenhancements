# Deployment Package Synchronization

Each project Primary owns release coherence for its deployable PRIMARY, MANAGER, and RESEARCH packages. Any change to project identity, AgentBus semantics, schemas, bootstrap, capabilities, role responsibilities, artifact routing, or repository/workspace resolution triggers dependency analysis.

Affected packages must be rebuilt, manifest-validated, archive-validated, and smoke-tested before hardening is declared complete.

Deployment role is separate from authority tier:

- `PRIMARY` maps to `ORCHESTRATOR` by default.
- `MANAGER` maps to `REVIEWER` by default.
- `RESEARCH` maps to `SPECIALIST` by default.

Custom grants remain explicit and least-privilege.

## Release gate

A protocol/framework change is incomplete while a dependent deployment package remains stale. Package manifests must declare project ID, deployment role, authority tier, framework version, protocol version, package version, source revision, and included components. Foreign-project or incompatible-protocol packages fail closed.
