# V25 R11 Draft PR Summary

This candidate introduces the V25 R11 standalone bootstrap ordering and external-mirror semantics without changing `main` or canonically promoting R11.

Key points:

- VMBUS initializes before project binding.
- Principal context becomes ready before project binding and task interpretation.
- R10 user-context remains distinct from R11 revisable model synthesis.
- External GitHub and Artifactory/message-board surfaces are optional after standalone readiness.
- No Artifactory write is claimed because the current runtime exposes no Artifactory/JFrog connector.
- Scheduled pipeline sequencing is checkpoint-gated rather than clock-trusted.
- Scheduler posture is disabled by default during migration, with `VMBUS Defrag` retained as the explicit enabled exception.

Promotion to main is intentionally outside this change set.
