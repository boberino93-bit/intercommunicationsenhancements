# Scheduled Agent Launch — Repair, Receipt, and Health-Gate Amendment (2026-10-07)

This amendment is authoritative where it conflicts with `protocols/scheduled_agent_launch.md` activation, receipt, scheduler-health, or scheduler-runtime-evidence language. All unrelated launch, project-binding, supervisory, admission, mutation, continuation, and safety rules in the base protocol remain in force.

## Canonical policy vs runtime evidence branches

Canonical code, policy, mappings, grants, protocols, and scheduler intent are read from `main`. Runtime scheduler evidence uses the dedicated `scheduler-evidence` branch when the GitHub degraded persistence path is required.

Write authority on `scheduler-evidence` never grants write, merge, force-push, status-check-bypass, policy-mutation, or other authority on `main`. After the cutover through mutation-journal sequence 6, new runtime scheduler mutation claims/events and degraded GitHub frontend execution receipts MUST NOT be written to `main`.

The `scheduler-evidence` branch is evidence only, not scheduler policy authority. Missing, unavailable, forked, force-rewritten, or invalid evidence fails closed for automatic scheduler mutation and cannot be used as proof of healthy execution.

## Scoped liveness-repair exception

The base protocol's blanket statement that no autonomous component may ever restore a disabled mapped swarm task is superseded only by a current scoped repair contract in `governance/SCHEDULER_ACTIVATION_GRANT_2026-10-07.json`, `governance/SCHEDULER_SYNCHRONIZATION_DIRECTIVE.json`, `org_agent_mesh.scheduler_repair_guard`, and `org_agent_mesh.schedule_activation`.

A disabled-to-enabled repair is permitted only when all of the following are true:

- the actor is the exact declared primary frontend reconciler or exact declared secondary liveness sentinel;
- a current `ACTIVE` human repair authorization is loaded and its `issued_at <= now < expires_at` time bound passes;
- the repair authorization has not exhausted its per-target or global rolling repair budget;
- the target frontend automation ID is explicitly in that authorization;
- the binding is exact and already declared;
- the canonical backend job remains enabled;
- the binding policy is `MIRROR` or `MIRROR_WHEN_ACCOUNT_CAPACITY_AVAILABLE`;
- account capacity is available;
- frontend identity is available;
- HOLD/PAUSE/STOP is clear;
- the executable repair guard passes before the activation gate is invoked;
- the current runtime mutation journal on `scheduler-evidence` validates completely before any automatic mutation.

Repair-budget exhaustion is not normal liveness recovery. It produces repair quarantine and requires renewed explicit human authorization or another authorized recovery path. An expired grant fails closed and may not extend itself.

This exception authorizes only restoration of existing mapped enablement. It does not authorize task creation, deletion, replacement, rebinding, renaming, rescheduling, project mutation, PRIMARY/MASTER creation, or full-swarm creation. `MIRROR_DISABLED_STANDBY`, personal/frontend-only, unmapped, missing, unavailable, and canonically paused/disabled targets remain prohibited.

An intentional durable pause must be represented in canonical control state. Canonical pause/backend disabled/HOLD/STOP always overrides liveness repair.

## Execution receipt requirement

Every successful mapped ChatGPT Scheduled Task invocation must publish an append-only execution receipt as early as practical after startup identity/binding verification and before substantial project work.

The receipt publisher may be either:

1. the declared Bootstrap Spawn Bridge reconciler reporting an exact observed mapped execution; or
2. the exact mapped frontend task attesting its own invocation.

For exact-self publication, `publisher_frontend_automation_id` MUST equal the receipt's `frontend_automation_id`, and that identity MUST match the declared binding. A worker may never publish a receipt for another worker.

Receipts use `governance/SCHEDULER_FRONTEND_RECEIPT_POLICY.json`, the receipt schemas, and `org_agent_mesh.frontend_execution_receipts`. Preferred transport is registered same-project AgentBus/Artifactory. When that surface is unavailable and the canonical GitHub degraded fallback is permitted, receipt files use immutable CREATE_NEW_FILE_ONLY semantics in `agentbus-backup/coordination-messages/` on branch `scheduler-evidence`. Degraded receipt writes to `main` are prohibited after cutover.

A receipt conveys no scheduler, repository-main, project, role, mutation, or continuation authority. If receipt persistence is blocked, the evidence branch is unavailable, or exact branch/write/readback conditions cannot be proven, report `FRONTEND_RECEIPT_PERSISTENCE_BLOCKED` or `SCHEDULER_EVIDENCE_BRANCH_UNAVAILABLE`; do not claim the occurrence is backend-verified.

## Health qualification and evidence deadline

`is_enabled=true`, successful update acknowledgement, accepted immediate-run request, `FRONTEND_EXECUTION_EXPECTED`, or one isolated execution is insufficient to declare sustained scheduler health.

The independent health gate in `governance/SCHEDULER_HEALTH_POLICY.json` is authoritative. The default qualification is three consecutive verified health-mature occurrences. An occurrence becomes health-mature only after the configured health evidence deadline, which MUST cover receipt acceptance plus persistence grace and any job-specific scheduler grace. Absence before that deadline is pending evidence; absence after it is degraded.

When the GitHub degraded receipt path is in use, the independent backend health audit MUST read the receipt set from `scheduler-evidence`, not from the historical receipt snapshot on `main`.

Common-mode ChatGPT provider failure is not automatically recoverable by another ChatGPT Scheduled Task and must remain visibly degraded when no out-of-band actuator exists.

## Scheduler-health work admission

Scheduler health is an additional restriction and never a source of authority. Before reversible or protected project mutation, the exact lane must be `HEALTHY`. `HEALTHY` only permits progression to the normal project, role, claim, consequence, mutation, and validation gates. `RECOVERING`, `DEGRADED_MISSING_EXECUTION_EVIDENCE`, `UNQUALIFIED`, stale, or unknown health permits only useful safe read-only work and append-only observability/checkpoint evidence. The executable reference gate is `org_agent_mesh.scheduler_work_gate`.

## Scheduler mutation evidence and multi-writer exclusion

All new scheduler-state mutation evidence MUST use `governance/SCHEDULER_MUTATION_JOURNAL_POLICY.json` and `org_agent_mesh.scheduler_mutation_journal`. Historical v1/v2 ledger files and the `main` v3 snapshot through sequence 6 remain evidence but are not writable/live authority for new mutations.

The live journal is stored on branch `scheduler-evidence`. Before any automatic scheduler mutation, an actor MUST:

1. load canonical policy from `main`;
2. fetch and validate the complete v3 journal from `scheduler-evidence`;
3. derive the exact next sequence and terminal event hash;
4. atomically acquire the deterministic next sequence by creating `governance/scheduler-mutation-journal-v3/claims/{sequence:06d}.json` on `scheduler-evidence` with CREATE_NEW_FILE_ONLY semantics;
5. read back that exact claim from `scheduler-evidence` and verify its event ID, actor, previous-event hash and claim hash;
6. create the immutable planned event at the matching deterministic event path on `scheduler-evidence`;
7. revalidate the complete evidence-branch journal;
8. only then perform the separately authorized scheduler mutation.

After provider mutation, live provider readback must be obtained and a separately claimed immutable applied/readback event must be added through the same evidence-branch sequence protocol.

If the deterministic claim path already exists, the actor lost the race and MUST NOT mutate. A claim without a matching valid event, a sequence fork, hash mismatch, evidence-branch mismatch, readback mismatch, or inability to create/read back immutable evidence blocks automatic mutation. Claims may not be stolen, overwritten, deleted, or automatically expired. Planned and applied evidence remain distinct. This storage protocol prevents two repair actors from both assuming ownership of one scheduler mutation sequence and prevents runtime evidence needs from becoming a reason to bypass protected `main`; it does not grant scheduler mutation or repository-main authority by itself.
