# System Scaler Protocol

Status: STAGED / NOT ACTIVE

The System Scaler is a bounded control-plane advisor for the staged 15 -> 30 -> 60 -> 100 swarm path. It does not create agents, terminate agents, change authority, or override project-local controls.

## Invariants

- Only RESEARCH capacity may be dynamically moved between active admission and standby.
- PRIMARY and MANAGER capacity remains fixed unless separately authorized.
- A scaler decision is a request, never execution authority.
- Scale-up is bounded by the current stage, project specialist caps, provider admission controls, manager backpressure, capacity state, leases, completion integrity, audit state, and handoff freshness.
- Unknown or degraded state fails closed.
- Scale-down is graceful drain only. A candidate must be idle and lease-free, then checkpoint, hand off, satisfy audit obligations, and return to standby.
- No scaler path may directly terminate a live agent or revoke a live lease.
- Cross-project telemetry is observation only.
- Decisions are deterministic and carry an idempotency digest.

## Scale-up hysteresis

A project becomes eligible for one additional RESEARCH admission only after the configured number of consecutive healthy observation windows and after any cooldown. Healthy means: capacity GREEN, manager backpressure NORMAL, collisions zero, unresolved leases zero, completion integrity true, ledger chain valid, and handoff fresh.

Global and per-project admission rate limits apply. Fairness rotates among eligible projects rather than repeatedly selecting the same project.

## Hold and drain

Soft manager pressure, transient collisions, or cooldown conditions produce HOLD. Hard manager backpressure, reserve/exhausted capacity, or deliberate stage contraction may request graceful drain of idle lease-free RESEARCH agents. Integrity/security/unknown-state failures freeze new admissions and preserve existing state for recovery.

## Authority boundary

`Scaler Decision != Authorization != Mutation`.

The scaler emits only `HOLD`, `REQUEST_ADMIT`, or `REQUEST_DRAIN_TO_STANDBY`. Existing launch, role, lease, package, authorization, security, recovery, and project-work controls decide whether any request may actually execute.

## Activation boundary

This protocol may be implemented and tested while inactive. Production activation, schedule enablement, live capacity increases, or changes to security/authorization/recovery require separate human authorization.
