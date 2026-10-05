# Swarm Launch Kernel V1

Kernel version: `1.2.1`

This project uses the common Swarm Launch Kernel for high-concurrency multi-agent research rounds.

Hard invariants: runtime state is project-local under `.swarm/`; `.swarm/` is operational/recovery state rather than a second accepted-decision authority; every record carries `project_id` and `global_run_id`; authority-bearing READY and lease records also carry `agent_instance_id`; cross-project telemetry is read-only and conveys no authority; projects write only their own authoritative surfaces; no force pushes/blind overwrites; AgentBus/Artifactory history remains append-only; stale epochs/project mismatches/malformed or illegal cross-project commands are quarantined; repeated invariant failures can put only this project into `DEGRADED_READ_ONLY`; the kernel cannot wake dormant sessions.

Launch lifecycle: `BOOT -> IDENTITY/INSTANCE -> MASTER HANDOFF -> TASK CLASSIFICATION -> LEARNING CONTEXT -> PACKAGE/CAPACITY -> GLOBAL RUN -> ROLE -> READY -> LOCAL START GATE -> WORK`. Normal non-swarm work never performs READY/global-run mutation merely because the kernel exists.

Work lifecycle: `IDENTIFY -> VALIDATE RUN -> ACQUIRE/VERIFY INSTANCE-FENCED LEASE -> READ -> WORK -> IDEMPOTENT PERSIST -> VERIFY -> CHECKPOINT -> LEARNING CHECKPOINT -> MASTER HANDOFF -> HANDOFF/YIELD`.

Claims are versioned, execution-instance-fenced leases. A restarted instance with the same logical agent ID cannot renew the previous instance's live lease. GitHub creates new lease paths only if absent; renewal/reassignment uses the current blob SHA plus expected lease version. Stale writers reread, reconcile, use deterministic bounded backoff, and retry. Never force-push.

State is sharded under `.swarm/{epochs,ready,leases,idempotency,quarantine,health,checkpoints,convergence,learning}/<run>/...` to avoid a global hot file. Learning records follow `protocols/swarm_learning.md`: raw experience is non-authoritative, validated knowledge requires explicit evidence-based promotion, and operating doctrine is the bounded bootstrap inheritance surface. Continuity follows `protocols/agent_state_handoff.md`: `MASTER_HANDOFF.json` is read before work and manually checkpointed after material transitions or before yield.

Managers publish queue depth. Soft limit slows secondary work; hard limit stops new secondary work until the queue recovers. Capacity admission also enforces the project specialist cap and fails read-only when capacity is unknown rather than assuming unlimited resources.

A round is complete only when research is accounted for, Manager dispositions complete, Primary/local decisions persisted, package parity restored, no unresolved leases remain, a valid recovery checkpoint exists, material learning has either been checkpointed or explicitly recorded as `NO_MATERIAL_LEARNING`, and the project master handoff reflects the completed/reassigned work.

Every PRIMARY, MANAGER, and RESEARCH package must include/load this protocol, `protocols/swarm_learning.md`, `protocols/agent_state_handoff.md`, `MASTER_HANDOFF.json`, `swarm_kernel/project.json`, `swarm_kernel/AGENT_BOOTSTRAP_OVERLAY.md`, and compatible `swarm_kernel/kernel.py`. Project-specific governance remains authoritative; the kernel adds concurrency control, continuity, and evidence-gated organizational learning rather than replacing project authority.
