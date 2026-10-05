# System Scaler Protocol

Status: STAGED / NOT ACTIVE

The System Scaler is a bounded control-plane advisor for the staged 15 -> 30 -> 60 -> 100 swarm path. It does not create agents, terminate agents, change authority, or override project-local controls.

## Invariants

- Only RESEARCH capacity may be dynamically moved between active admission and standby.
- PRIMARY and MANAGER capacity remains fixed unless separately authorized.
- A scaler decision is a request, never execution authority.
- Scale-up is bounded by the current stage, project specialist caps, provider admission controls, manager backpressure, capacity state, leases, completion integrity, audit state, handoff freshness, and explicit eligible-work demand.
- Unknown, stale, run-mismatched, future-dated, exhausted, integrity-failed, or degraded telemetry fails closed.
- Scale-down is graceful drain only. A candidate must be idle and lease-free, then checkpoint, hand off, satisfy audit obligations, and return to standby.
- No scaler path may directly terminate a live agent or revoke a live lease.
- Cross-project telemetry is observation only.
- Decisions are deterministic and carry both a full-input snapshot digest and a decision digest.

## Telemetry binding

Each project signal MUST identify the current run and include a timezone-aware measurement timestamp. A decision cycle MUST receive the exact registered project set. Stale, future-dated, missing-project, duplicate-project, or run-mismatched telemetry cannot advance hysteresis memory and cannot admit work.

The reference freshness window is 120 seconds with five seconds of tolerated clock skew. This is a staged default, not authority to weaken project-local freshness requirements.

## Scale-up hysteresis and demand

A project becomes eligible for one additional RESEARCH admission only after the configured number of consecutive healthy observation windows, after cooldown, and when eligible queued work actually exists. Healthy capacity without work demand does not justify adding active agents.

Healthy means: capacity GREEN, manager backpressure NORMAL, collisions zero, unresolved leases zero, completion integrity true, ledger chain valid, handoff fresh, current run binding valid, and telemetry fresh.

Global and per-project admission rate limits apply. Fairness rotates among eligible projects rather than repeatedly selecting the same project.

## Hold, pressure, and graceful drain

Soft manager pressure, AMBER/PRESERVE capacity, transient collisions, or cooldown conditions produce HOLD.

RESERVE_ONLY capacity or manager hard pressure globally blocks new admissions. A graceful drain may be requested only for explicitly idle and lease-free RESEARCH agents.

EXHAUSTED capacity produces GLOBAL HOLD rather than a checkpoint-dependent drain request because the capacity layer explicitly blocks essential writes at exhaustion; the scaler must not assume checkpoint/handoff persistence is available.

If hard pressure exists and no safe drain candidate is known, the result is HOLD. The scaler never converts pressure into an excuse to admit work elsewhere in the same cycle.

## Stage contraction

When the requested stage ceiling is below the currently active RESEARCH population, contraction takes precedence over every admission path. The scaler may request bounded graceful drains from idle, lease-free candidates until the ceiling is reached.

If one cycle cannot safely drain enough agents, the decision reports remaining excess and the next cycle continues contraction. It MUST NOT claim the stage transition is complete or admit replacement work while excess active capacity remains.

## Authority boundary

`Scaler Decision != Authorization != Mutation`.

The scaler emits only `HOLD`, `REQUEST_ADMIT`, or `REQUEST_DRAIN_TO_STANDBY`. Existing launch, role, lease, package, authorization, security, recovery, and project-work controls decide whether any request may actually execute.

## Activation boundary

This protocol may be implemented and tested while inactive. Production activation, schedule enablement, live capacity increases, or changes to security/authorization/recovery require separate human authorization.
