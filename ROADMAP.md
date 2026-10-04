# Roadmap

## Alpha 1 — Project identity boundary — implemented reference layer
- Immutable project binding and identity-first bootstrap
- Intra-project message enforcement
- Project-scoped lanes/presence
- Explicit cross-project exchange contract
- Adversarial isolation tests

## Alpha 2 — Concurrency/recovery/authorization — implemented reference layer
- Active bound-session mutation authorization
- Role capability sets and child non-escalation
- Expiring execution-instance leases
- Compare-and-set state mutation
- Delivery acknowledgement, bounded retry and quarantine
- Project-scoped task/artifact/audit reference registries
- Canonical identifier collision protection

## Alpha 2.5 — Deployment integrity — implemented release gate
- Glob-based package dependency closure
- Manifest v3 role capabilities and component/source hashes
- Coordinated PRIMARY/MANAGER/RESEARCH release set
- Deterministic archives and independent reproducibility check

## Alpha 3 — Durable organizational control plane — next hardening layer
- Durable multi-process/distributed lease/CAS/task/artifact/audit adapters
- Persistent project and global agent registries
- Project-scoped/global observability service
- Durable sanitized cross-project bridge
- Broker-specific acknowledgement transport

## Beta gate
- Instantiate a third unrelated project without core code changes
- Run multiple unrelated projects simultaneously
- Intentionally attempt identity spoofing and cross-project contamination
- Demonstrate deterministic rejection and attributable audit evidence
- Prove per-project role package sets are synchronized and reproducible
- Exercise pause/drain/failure of one project while peers continue
