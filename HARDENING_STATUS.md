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
- **DOCUMENTED + PACKAGED:** Primary owns holistic project/package release consistency; Manager and Research remain distinct deployment roles with lower default authority tiers and dedicated bootstrap contracts.
- **ENFORCED + CI VERIFIED:** exact-SHA GitHub Actions build pipeline for PRIMARY/MANAGER/RESEARCH ZIP packages.

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

## Verified deployment package evidence

GitHub Actions run `37157511450` completed successfully for source revision `104b3e3632ec9eb0f9c5097f4655cb8d4158277a` and produced artifact `11285423995`.

The downloaded outer deployment artifact verified at SHA-256:

`84101d06322c0d456354cdd105e364dd8485489cfdbf14214a210ca0e066bb20`

It contained exactly three role ZIPs, each with 21 entries, no missing declared components, and the correct role bootstrap:

- PRIMARY: `bdf272d3ce5bb746d178fc5cd32cff3db5f5ecd8f95ba54d786e6f03160de8a8`
- MANAGER: `e860e010cafa6d756052e26e8646e5dd1e0b76afb53a63cc5dcc51e31830901a`
- RESEARCH: `f67e216969708b31e0461e2121943083cbc69c3636eb69285d5ccf859e810c79`

All three manifests declared project `intercommunicationsenhancements`, framework `1.1.0-alpha.1`, protocol `2.0.0-alpha.1`, and exact source revision `104b3e3632ec9eb0f9c5097f4655cb8d4158277a`.

## Remaining Alpha 2/3 work

Atomic leases, compare-and-set state mutation, dead-letter/quarantine routing, delivery acknowledgements, bounded retries, global project registry, project pause/drain, and the full cross-project bridge service remain open hardening work.
