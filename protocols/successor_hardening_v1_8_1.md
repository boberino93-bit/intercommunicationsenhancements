# Successor hardening v1.8.1 — diagnostics, learning, visibility, and consequence boundary

Status: `IMPLEMENTATION_CANDIDATE`  
Canonical: `NO`  
Production deployment: `NOT_AUTHORIZED`

## Purpose

This tranche strengthens the existing v1.8 candidate without creating a second control plane.

It implements four bounded surfaces:

1. **Diagnostic learning** — evidence-weighted online strategy diagnostics with holdout isolation, contamination quarantine, drift detection, and advisory-only recommendations.
2. **Intercommunication diagnostics** — nominal 45-second liveness, 60-second maximum normal staleness, heartbeat coalescing, durable material deltas, peer discovery, and read-only fleet aggregation.
3. **Consequence gateway** — frozen exact-action preparation, independently signed commit grants, pre-commit revalidation, revocation/replay protection, consequence receipts, provenance labels, egress policy, and `UNKNOWN_EFFECT -> VERIFY_OR_RECOVERY`.
4. **Operational readiness diagnostics** — explicit evidence probes for scheduler admission, distributed backend guarantees, and repository governance so the system cannot silently upgrade partial integration into a proven claim.

## Learning contract

The learning algorithm is `bounded-evidence-weighted-online-mean-v1`.

Training inputs require:

- verified evidence;
- confidence at or above configured threshold;
- `TRAIN` partition;
- non-contaminated evidence.

`HOLDOUT` observations are evaluated separately and never update strategy weights.

A recommendation remains:

`CANDIDATE + ADVISORY + authority=false`

It cannot become `VALIDATED` or `DOCTRINE` without the existing swarm-learning validation/promotion path.

## Intercommunication contract

Default policy:

- nominal heartbeat: 45 seconds;
- maximum normal staleness: 60 seconds;
- unchanged intermediate status may be coalesced;
- material delta or meaningful degraded/recovery/terminal transition is durable;
- heartbeat fields are observations and never ownership authority;
- same-epoch/different-fence observations are surfaced as conflicts but do not transfer work;
- peer discovery is task-semantic and project-scoped;
- aggregate observability is derived/read-only.

## Consequence contract

For gated effects:

`PREPARE -> EXACT ACTION DIGEST -> INDEPENDENT GRANT -> REVALIDATE CURRENT STATE -> COMMIT ONCE -> VERIFY EFFECT -> RECEIPT`

The grant is bound to project, agent instance, exact action digest, operation/effect class, target, ownership epoch, fence, policy digest, capability digest, precondition digest, expiry, and use count.

The preparer cannot authorize itself.

Immediately before commit the verifier also checks session active, task still authorized, capability still present, lease still valid, project not quarantined, cross-project exchange validated when applicable, and health still allows effect.

An executor exception after the effect boundary produces `UNKNOWN_EFFECT`, disables blind retry, and requires verification/recovery.

## Environment truth

The operational diagnostic layer does not pretend that runtime integrations exist. It distinguishes provider admission `PREVENTIVE` vs `MITIGATION_ONLY`, distributed backend `PROVEN`/`PARTIAL`/`UNPROVEN`, and repository governance `PROVEN`/`PARTIAL`/`UNPROVEN`.

These diagnostics are evidence, never deployment authority.

## Promotion boundary

This tranche remains non-canonical until exact-head repository CI and independent review pass. Even after that, it may at most become a verified release candidate. Production promotion still requires the separately authorized path.
