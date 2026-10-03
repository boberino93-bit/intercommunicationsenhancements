# Hardening Status

Current target: **1.1.0-alpha.1 / protocol 2.0.0-alpha.1**

## Implemented in repository

- **ENFORCED:** immutable project-binding primitive and same-project authorization guard.
- **ENFORCED:** internal message bus rejects source/destination project mismatch.
- **ENFORCED:** message protocol version check, expiry check, agent-instance requirement, and project-scoped idempotency protection.
- **ENFORCED:** cross-project exchange is a separate explicit validator and is denied without capability + approval.
- **ENFORCED:** work-lane collisions are scoped to project and agent execution instance.
- **ENFORCED:** presence records require project and agent-instance identity.
- **ENFORCED:** deployment package manifests reject foreign project identity and stale protocol/framework versions.
- **DOCUMENTED:** Primary owns holistic project/package release consistency; Manager and Research remain distinct deployment roles with lower default authority tiers.
- **COMMITTED:** exact-SHA GitHub Actions build pipeline for PRIMARY/MANAGER/RESEARCH ZIP packages.

## Test evidence

Before repository distillation, the modified full seed package passed **30/30 tests** locally, combining the original 18 seed tests with new isolation/package hardening tests.

The committed repository contains the first focused adversarial suite covering:

- internal cross-project routing rejection;
- missing project identity;
- foreign target binding;
- path escape;
- duplicate idempotency keys;
- cross-project deny-by-default and approval requirements;
- foreign/stale deployment package rejection;
- same-named lanes across different project namespaces.

## Not yet claimed complete

- **CI RUN NOT YET VERIFIED:** the workflow is committed, but no Actions run is currently visible through the connector for the API-originated pushes.
- **DEPLOYMENT ZIPS NOT YET CLAIMED VERIFIED:** do not report PRIMARY/MANAGER/RESEARCH ZIPs as current until an exact-source build run is observed and its artifacts validate.
- Atomic leases, compare-and-set state mutation, dead-letter/quarantine routing, delivery acknowledgements, bounded retries, global project registry, project pause/drain, and full cross-project bridge service remain Alpha 2/3 work.
