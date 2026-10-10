# System Scaler Bootstrap Overlay

Status: STAGED / NOT ACTIVE

This overlay is intentionally dormant until separately authorized for production activation.

When activated, it may only request bounded RESEARCH admission or graceful drain-to-standby operations through existing launch/lease/handoff controls. It may not directly create authority, terminate agents, revoke leases, raise capacity limits, enable schedules, or alter authentication/security/recovery policy.

Before honoring a scaler request, require:

- current stage contract;
- exact registered-project signal set;
- current run binding;
- fresh timezone-aware telemetry;
- project binding;
- package parity;
- explicit eligible-work demand for admission;
- GREEN resource-capacity evidence for admission;
- manager backpressure state;
- lease safety;
- completion integrity;
- audit/ledger validity;
- handoff freshness;
- all existing authorization/preflight checks.

`UNKNOWN`, `EXHAUSTED`, stale, future-dated, run-mismatched, integrity-failed, or degraded telemetry fails closed.

Stage contraction takes precedence over admission. Contraction may request only graceful drains of explicitly idle and lease-free RESEARCH agents. Partial contraction must report remaining excess rather than pretending the lower stage has converged.

A scaler decision must carry an input-snapshot digest and decision digest. Replaying a decision against different telemetry is invalid.

`Scaler Decision != Authorization != Mutation`.
