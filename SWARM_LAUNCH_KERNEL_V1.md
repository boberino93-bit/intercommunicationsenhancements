# Swarm Launch Kernel V1

Kernel version: `1.0.0`

This project uses the common Swarm Launch Kernel for high-concurrency multi-agent research rounds.

Hard invariants: runtime state is project-local under `.swarm/`; every record carries `project_id` and `global_run_id`; cross-project telemetry is read-only and conveys no authority; projects write only their own authoritative surfaces; no force pushes/blind overwrites; AgentBus/Artifactory history remains append-only; stale epochs/project mismatches/malformed or illegal cross-project commands are quarantined; repeated invariant failures can put only this project into `DEGRADED_READ_ONLY`; the kernel cannot wake dormant sessions.

Launch lifecycle: `BOOT -> IDENTITY -> PACKAGE -> GLOBAL RUN -> ROLE -> READY -> LOCAL START GATE -> LEARNING CONTEXT -> WORK`.

Work lifecycle: `IDENTIFY -> VALIDATE RUN -> ACQUIRE/VERIFY LEASE -> READ -> WORK -> IDEMPOTENT PERSIST -> VERIFY -> CHECKPOINT -> LEARNING CHECKPOINT -> HANDOFF`.

Claims are versioned leases. GitHub creates new lease paths only if absent; renewal/reassignment uses the current blob SHA plus expected lease version. Stale writers reread, reconcile, use deterministic bounded backoff, and retry. Never force-push.

State is sharded under `.swarm/{epochs,ready,leases,idempotency,quarantine,health,checkpoints,convergence,learning}/<run>/...` to avoid a global hot file. Learning records follow `protocols/swarm_learning.md`: raw experience is non-authoritative, validated knowledge requires explicit evidence-based promotion, and operating doctrine is the bounded bootstrap inheritance surface.

Managers publish queue depth. Soft limit slows secondary work; hard limit stops new secondary work until the queue recovers. Repeated invariant failures trip the project-local circuit breaker.

A round is complete only when research is accounted for, Manager dispositions complete, Primary/local decisions persisted, package parity restored, no unresolved leases remain, a valid recovery checkpoint exists, and material learning has either been checkpointed or explicitly recorded as `NO_MATERIAL_LEARNING` for completed work units.

Every PRIMARY, MANAGER, and RESEARCH package must include/load this protocol, `protocols/swarm_learning.md`, `swarm_kernel/project.json`, `swarm_kernel/AGENT_BOOTSTRAP_OVERLAY.md`, and compatible `swarm_kernel/kernel.py`. Project-specific governance remains authoritative; the kernel adds concurrency control and evidence-gated organizational learning rather than replacing project authority.
