# Swarm Scale 100 Bootstrap Overlay

Applies to PRIMARY, MANAGER, and RESEARCH when a swarm run is being sized, launched, expanded, or evaluated for scale.

1. Load `SWARM_SCALE_ENTRYPOINT.json`, `protocols/swarm_scale_100.md`, `protocols/stage15_preflight.md`, `governance/SWARM_SCALE_100_POLICY.json`, and `governance/STAGE15_PREFLIGHT_POLICY.json`.
2. Treat 100 as a population target, not permission for a flat provider burst or unrestricted concurrent mutation.
3. Preserve the current project specialist cap and manager backpressure rules unless a separately authorized, evidence-backed change explicitly modifies them.
4. Use the staged ladder `15 -> 30 -> 60 -> 100`; the next stage is blocked until the current stage gate passes.
5. Before any Stage-15 launch, require one provenance-bound preflight envelope from `org_agent_mesh.stage15_preflight` covering exactly the registered seven-project set for the intended global run.
6. Contract alignment alone is not preflight readiness. Preflight readiness alone is not a stage pass or launch authorization.
7. Derive capacity admission from fresh project/repository-bound `org-agent-mesh/capacity-signal/v1` evidence. Missing, stale, future, UNKNOWN, or non-GREEN evidence fails closed.
8. Canonicalize the explicit XRP operations alias `xrpthesis -> xrp-thesis` only for central accounting. Preserve the observed alias and `normalized:false` until the source project completes normalization.
9. Standby participants remain `STANDBY_READ_ONLY` and may not acquire mutating work solely because they are part of the target population.
10. Every exclusive or mutating work item still requires the normal project binding, role/capability, claim/lease/fence, idempotency, authorization, and completion-integrity controls.
11. All expected agents must be READY and accounted for before a stage can pass. Lost agents, stale handoffs, duplicate commits, cross-project write violations, unauthorized mutations, unresolved leases, or unaccounted work block scale progression.
12. Feed scale/preflight incidents into the regression-learning subsystem as non-authoritative evidence. Do not normalize recurring capacity, identity, collision, provider-admission, queue, stale-state, or handoff failures as expected noise.
13. A provider/scheduler test profile is not an automatic production configuration change. Security, authority, recovery, schedule activation, destructive operations, and cross-project source writes remain human-gated where existing policy requires it.
14. Report scale state precisely: distinguish `CONTRACT_READY`, `PREFLIGHT_READY`, `STAGE_PASSED`, `POPULATION_TARGET`, `ACTIVE_SLOT`, `STANDBY_READ_ONLY`, provider launch state, manager backpressure, and mutation eligibility.
