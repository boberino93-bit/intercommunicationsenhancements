# Reliability Kernel v1.8 — implementation candidate

Status: **IMPLEMENTATION_CANDIDATE / VALIDATION_PENDING**  
Base: `72e87ce7cddca17fd78c8ece3ecb5f523c7021e2`  
Normalized runtime source: `fb592418f700fc5e540e76bfa42b043e03fe6ed9`

## Scope

This candidate adds a narrow executable reliability layer without creating a second control plane. Existing `ProjectBinding`, capability, lifecycle, lease, state-version, launch-admission, and package-release mechanisms remain authoritative.

The candidate implements:

- projection of existing authority into an `EffectivePolicySlice`;
- tamper-evident HMAC reference `PolicyCertificate` with project/repository/work-instance/ownership binding, expiry and optional single-use consumption;
- machine-enforced non-escalation, project identity and repository identity invariants;
- a bounded `ResourceGovernor` for concurrency and aggregate work weight;
- `SAFE_MINIMAL` fail-closed effect filtering;
- proof-carrying handoffs that reject receiver capability expansion and stale ownership epochs;
- schema/protocol compatibility fencing;
- a hysteresis/cooldown primitive for adaptive control-loop stability;
- stable operator-visible reliability reason codes.

## Authority boundary

The policy compiler can only select a subset of capabilities already present in the active `ProjectBinding`. It does not mint capabilities. `PRODUCTION_DEPLOYMENT` and `BREAK_GLASS` are deliberately non-compilable by this reference candidate because the current baseline does not expose a canonical deployment capability or authenticated human break-glass verifier.

`POLICY_CHANGE` and `FINANCIAL_ACTION` still require their pre-existing baseline capabilities and remain protected transition classes. A production implementation must bind them to the trusted human-authorization mechanism before treating the reference path as deployment-conformant.

## Cryptographic scope

The HMAC signing path is a reference tamper-evidence implementation for tests and controlled runtime integration. It is not a claim that secret-key distribution, hardware-backed keys, PKI, or break-glass authentication is complete. Ordinary agents must not receive a human root secret.

## Integration order

1. Keep this candidate isolated from `main` until exact-revision CI succeeds.
2. Reconcile the new module with existing `launch_admission`, control-plane leases, durable state and package-verifier code; do not fork those responsibilities.
3. Add executor/preflight invocation points for certificate verification only after the call path is proven non-bypassable.
4. Move replay ledgers and resource reservations to the canonical durable backend before production conformance.
5. Add public-key or infrastructure-backed authorization verification for protected human transitions.
6. Run adversarial/property tests, catastrophe reconstruction, then ringed canary.
7. Promotion requires existing governance; this document does not authorize deployment.

## Explicit non-claims

This candidate does **not** claim: production deployment authorization, complete break-glass, multi-node fairness, durable global SLO budgets, disaster-recovery completion, supply-chain attestation completion, or that all 19,201 directive lines have been mechanically compiled.
