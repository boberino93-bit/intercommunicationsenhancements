# Deployment Package Synchronization

A hardening change is incomplete while any affected deployable role is stale.

Authoritative dependency closure is `packaging/agent_package_dependencies.json`. Shared globs cover all runtime modules, schemas and protocol documents; role files are added per PRIMARY, MANAGER and RESEARCH.

Manifest v3 records exact source SHA, role, capabilities, framework/protocol/package versions, deterministic commit-derived build time, dependency-map SHA-256, exact component inventory and hashes.

Verification recomputes dependency closure from repository source, rejects missing/extra archive members, compares every component to manifest and source, rejects foreign role instructions, enforces the complete role set and one source revision, and validates `release-set.json` archive hashes.

CI independently rebuilds and compares output hashes. The CI artifact is authoritative only for its exact source revision.
