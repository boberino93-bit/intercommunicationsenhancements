# Scheduled Agent Launch — Repair and Execution-Receipt Amendment (2026-10-07)

This amendment is authoritative where it conflicts with `protocols/scheduled_agent_launch.md` activation or receipt language. All unrelated launch, project-binding, supervisory, admission, mutation, continuation, and safety rules in the base protocol remain in force.

## Scoped liveness-repair exception

The base protocol's blanket statement that no autonomous component may ever restore a disabled mapped swarm task is superseded only by the active scoped repair contract in `governance/SCHEDULER_ACTIVATION_GRANT_2026-10-07.json`, `governance/SCHEDULER_SYNCHRONIZATION_DIRECTIVE.json`, and `org_agent_mesh.schedule_activation`.

A disabled-to-enabled repair is permitted only when all of the following are true:

- the actor is the exact declared primary frontend reconciler or exact declared secondary liveness sentinel;
- a current ACTIVE human repair authorization is loaded;
- the target frontend automation ID is explicitly in that authorization;
- the binding is exact and already declared;
- the canonical backend job remains enabled;
- the binding policy is `MIRROR` or `MIRROR_WHEN_ACCOUNT_CAPACITY_AVAILABLE`;
- account capacity is available;
- frontend identity is available;
- HOLD/PAUSE/STOP is clear.

This exception authorizes only restoration of existing mapped enablement. It does not authorize task creation, deletion, replacement, rebinding, renaming, rescheduling, project mutation, PRIMARY/MASTER creation, or full-swarm creation. `MIRROR_DISABLED_STANDBY`, personal/frontend-only, unmapped, missing, unavailable, and canonically paused/disabled targets remain prohibited.

An intentional durable pause must be represented in canonical control state. Canonical pause/backend disabled/HOLD/STOP always overrides liveness repair.

## Execution receipt requirement

Every successful mapped ChatGPT Scheduled Task invocation must publish an append-only execution receipt as early as practical after startup identity/binding verification and before substantial project work.

The receipt publisher may be either:

1. the declared Bootstrap Spawn Bridge reconciler reporting an exact observed mapped execution; or
2. the exact mapped frontend task attesting its own invocation.

For exact-self publication, `publisher_frontend_automation_id` MUST equal the receipt's `frontend_automation_id`, and that identity MUST match the declared binding. A worker may never publish a receipt for another worker.

Receipts use:

- `governance/SCHEDULER_FRONTEND_RECEIPT_POLICY.json`;
- `schemas/frontend_execution_receipt.schema.json`;
- `schemas/scheduler_frontend_receipt_message.schema.json`;
- `org_agent_mesh.frontend_execution_receipts`.

Preferred transport is the registered same-project AgentBus/Artifactory channel. When unavailable and the canonical degraded fallback is permitted, create a new immutable file under `agentbus-backup/coordination-messages/` named with prefix `scheduler-frontend-receipt__`. Never overwrite, update, delete, or reuse a conflicting receipt file.

A receipt conveys no scheduler, project, role, mutation, or continuation authority. It proves only the exact observed frontend occurrence when its identity and timing validate.

If receipt persistence is blocked, report `FRONTEND_RECEIPT_PERSISTENCE_BLOCKED`; do not claim the occurrence is backend-verified.

## Health qualification

`is_enabled=true`, successful update acknowledgement, accepted immediate-run request, `FRONTEND_EXECUTION_EXPECTED`, or one isolated execution is insufficient to declare sustained scheduler health.

The independent health gate in `governance/SCHEDULER_HEALTH_POLICY.json` is authoritative. The default qualification is three consecutive verified mature occurrences. Missing latest mature execution evidence is degraded. Common-mode ChatGPT provider failure is not automatically recoverable by another ChatGPT Scheduled Task and must remain visibly degraded when no out-of-band actuator exists.
