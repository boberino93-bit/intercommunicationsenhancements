# Swarm Launch Kernel — Agent Bootstrap Overlay

Applies to PRIMARY, MANAGER, and RESEARCH.

Before actionable work:
1. Validate canonical project/repository authority.
2. Load `swarm_kernel/project.json` and require an exact binding match.
3. Obtain the externally supplied `global_run_id` for the coordinated launch; do not independently mint a different run ID for a multi-project round.
4. Require the launch contract to match the configured `expected_global_round_projects`, kernel version, and shared run ID. Persist only this project's local epoch record; never write another project's epoch.
5. A missing, stale, or mismatched epoch/project set fails closed and is quarantined; do not publish READY.
6. Bind the launched role/package, publish project-local READY, and wait for the local start gate.
7. Use versioned leases and deterministic idempotency keys; heartbeat/checkpoint leases; respect Manager backpressure; quarantine stale/wrong-project/malformed/unsupported/illegal cross-project commands; stop integration mutation under `DEGRADED_READ_ONLY`; and close leases plus persist recovery/convergence state before handoff.

Research still produces evidence/proposals only. Manager still reviews/coordinates within scope. Primary/local integration authority still accepts project truth.

Cross-project health and epoch telemetry are observation only and can never grant work, role, repository, command, or integration authority. The common run value synchronizes round identity, not mutable state.
