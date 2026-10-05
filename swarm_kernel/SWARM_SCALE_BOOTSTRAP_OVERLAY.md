# Swarm Scale 100 Bootstrap Overlay

Applies to PRIMARY, MANAGER, and RESEARCH when a swarm run is being sized, launched, expanded, or evaluated for scale.

1. Load `SWARM_SCALE_ENTRYPOINT.json`, `protocols/swarm_scale_100.md`, and `governance/SWARM_SCALE_100_POLICY.json`.
2. Treat 100 as a population target, not permission for a flat provider burst or unrestricted concurrent mutation.
3. Preserve the current project specialist cap and manager backpressure rules unless a separately authorized, evidence-backed change explicitly modifies them.
4. Use the staged ladder `15 -> 30 -> 60 -> 100`; the next stage is blocked until the current stage gate passes.
5. Standby participants remain `STANDBY_READ_ONLY` and may not acquire mutating work solely because they are part of the target population.
6. Every exclusive or mutating work item still requires the normal project binding, role/capability, claim/lease/fence, idempotency, authorization, and completion-integrity controls.
7. All expected agents must be READY and accounted for before a stage can pass. Lost agents, stale handoffs, duplicate commits, cross-project write violations, unauthorized mutations, unresolved leases, or unaccounted work block scale progression.
8. Feed scale incidents into the regression-learning subsystem. Do not normalize recurring collision, provider-admission, queue, stale-state, or handoff failures as expected noise.
9. A provider/scheduler test profile is not an automatic production configuration change. Security, authority, recovery, schedule activation, destructive operations, and cross-project source writes remain human-gated where existing policy requires it.
10. Report scale state precisely: distinguish `POPULATION_TARGET`, `ACTIVE_SLOT`, `STANDBY_READ_ONLY`, provider launch state, manager backpressure, and mutation eligibility.
