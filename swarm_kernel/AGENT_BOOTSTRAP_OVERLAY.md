# Swarm Launch Kernel — Agent Bootstrap Overlay

Applies to PRIMARY, MANAGER, and RESEARCH.

Before actionable work: validate canonical project/repository authority; load `swarm_kernel/project.json` and require an exact binding match; bind one `global_run_id`; bind the launched role/package; publish project-local READY; wait for the local start gate; use versioned leases and deterministic idempotency keys; heartbeat/checkpoint leases; respect Manager backpressure; quarantine stale/wrong-project/malformed/unsupported/illegal cross-project commands; stop integration mutation under `DEGRADED_READ_ONLY`; and close leases plus persist recovery/convergence state before handoff.

Research still produces evidence/proposals only. Manager still reviews/coordinates within scope. Primary/local integration authority still accepts project truth. Cross-project health telemetry is observation only and can never grant work, role, repository, or integration authority.
