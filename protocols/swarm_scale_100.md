# Swarm Scale 100 Protocol

Status: ACTIVE TARGET — ALIGNMENT VERIFIED / STAGE 15 NOT YET PASSED
Scope: Global Swarm scaling and staged validation

## Objective

Scale the architecture toward a 100-agent population without weakening authority, project isolation, lease/fence semantics, completion integrity, or provider/API capacity safeguards.

A target population of 100 does **not** mean 100 simultaneous provider starts or 100 simultaneous mutating workers.

## Core scaling model

The swarm separates five quantities:

1. **Population** — total registered participants in the run.
2. **Provider launch concurrency** — model/provider starts allowed in flight.
3. **Active work slots** — agents currently eligible to perform bounded project work.
4. **Project specialist capacity** — active RESEARCH slots per project.
5. **Mutation/write capacity** — independently governed by authority, leases/fences, idempotency, capacity state, and write budgets.

Population may increase without increasing the other four quantities.

## Current 100-agent plan

The seven registered projects are now contract-aligned on kernel `1.2.1` and the seven-project global round. The append-only verification record is `governance/SWARM_SCALE_100_ALIGNMENT_VERIFICATION_20261005.json`.

The earlier `governance/SWARM_SCALE_100_COMPATIBILITY_AUDIT_20261005.json` is preserved as historical pre-remediation evidence. It is not current readiness state.

Under the existing per-project cap of eight active RESEARCH specialists, the current topology yields:

- 7 PRIMARY active slots
- 7 MANAGER active slots
- 56 RESEARCH active slots
- 30 RESEARCH standby/read-only participants
- 100 total participants
- 70 active work slots

Standby participants may reconstruct context, observe allowed telemetry, prepare non-mutating analysis, and wait for admission. They may not acquire mutating work merely because they are part of the population.

## Contract alignment state

Contract alignment is VERIFIED. All seven registered projects expose a compatible local swarm contract and agree on the global fields required for one coordinated round while preserving project-local identity and coordination bindings.

Alignment verification makes Stage 15 **eligible to test**. It does not mean Stage 15 has passed, does not authorize launching it, and does not authorize higher stages.

A future mismatch in `expected_global_round_projects`, `global_run_contract_version`, kernel compatibility, repository/project binding, or another designated identical field fails closed and re-blocks the affected stage.

Do not resolve future mismatch by silently taking an intersection, dropping projects, widening foreign-write authority, weakening fail-closed checks, or treating semantic similarity as contract compatibility.

## Staged validation ladder

The required progression is:

`15 -> 30 -> 60 -> 100`

Each stage must converge and pass its gate before the next stage is attempted. A failed stage produces regression evidence and remediation work; it does not authorize raising limits.

Stage 15 has **not yet passed** and requires a separately authorized live validation run.

## Provider admission

A flat burst is prohibited. The reference launch controller retains conservative defaults. Test profiles may use staged launch parameters from `governance/SWARM_SCALE_100_POLICY.json`, but those values are test targets only and do not automatically reconfigure a provider or scheduler.

If provider admission is unavailable before model invocation, deterministic staggering and persisted retry state remain required.

## Work admission

Per-project active-specialist caps remain authoritative until separately changed after evidence demonstrates headroom. Manager queue backpressure remains mandatory. At hard-stop backpressure, secondary work stops admitting until the manager queue recovers.

Exclusive or mutating work continues to require the normal claim/lease/fence and authorization controls. Scale membership never conveys authority.

## Stage gate

A stage cannot pass unless all expected agents are READY and accounted for, and all of the following are zero at convergence:

- unauthorized mutations
- cross-project write violations
- duplicate commits
- unresolved leases
- stale handoffs
- lost agents
- unaccounted work items

The completion-integrity sweep, audit-ledger integrity, and manager-backpressure recovery checks must also pass.

## Capacity changes

Do not increase active-specialist caps, live provider concurrency, scheduler activation, or mutation/write budgets merely to hit the population target. Those changes require evidence from lower stages and whatever authorization class applies to the specific control.

Security, authentication, authorization, recovery, destructive operations, root governance, schedule activation, and cross-project source writes remain outside the bounded scaling-maintenance lane.

## Regression learning

Every scale-stage incident should be normalized into the regression-learning system. Recurring collision, stale-state, capacity, duplicate-work, handoff, contract-alignment, or provider-admission failures should generate tests or service-pack candidates rather than being treated as one-off launch noise.

## Success definition

The 100-agent objective is met when a 100-participant run reaches convergence with every participant accounted for, all stage-gate invariants satisfied, no unresolved work ownership, and no authority/security regression. Raising simultaneous active capacity beyond the current safe ceiling is a separate evidence-driven optimization.
