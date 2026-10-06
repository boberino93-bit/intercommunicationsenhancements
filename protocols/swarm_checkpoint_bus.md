# Scheduled Swarm Checkpoint Bus v3 — dual-persistence contract

## Purpose
This protocol defines project-scoped scheduled handoff transport. Coordination records are non-authoritative and never substitute for project evidence, mutation authorization, source authority, or `ConsequenceGateway`.

## Required route
Every registered project MUST resolve two distinct durability sinks before material scheduled work begins:
1. its exact project-local Artifactory/message-forum namespace from `PROJECT_ROLE_ROUTING_REGISTRY.json`; and
2. its exact canonical GitHub repository backup namespace under `agentbus-backup/coordination-messages/`.

There is no GitHub-only registered-project exception. `xrp-thesis` resolves its internal forum to `/XRPTHESIS-AgentBus/messages`; `xrpthesis` is a legacy observation alias only and never changes project identity or routing authority.

## Dual-persistence preflight
Before substantive scheduled work: resolve exact project/repository/forum; derive the current cycle; construct a stable checkpoint/work record; pass durable-record secret screening; append to the registered forum; create the append-only GitHub backup; read back both; verify the same project_id, record/checkpoint identity and canonical digest; then require `DUAL_PERSISTENCE_CONFIRMED`.

If either sink is unavailable, unregistered, mismatched, stale, unreadable, or returns a different digest, emit/report `CHECKPOINT_IO_BLOCKED` or persistence recovery state and do not begin expensive unhandoffable work. One-sided persistence is recovery-required and never READY/COMPLETE.

## Append-only and retry
Existing records are never overwritten/deleted/renamed/moved. Same ID + same digest is idempotent retry. Same ID + different digest is conflict/quarantine. Corrections and supersessions are new records. Recovery after a one-sided crash retries only the missing sink after verifying the surviving copy.

## Envelope
Use `intercommunications/swarm-stage-checkpoint/v2` plus the material-work/dual-persistence receipt contracts. Include project_id, authority_conveyed=false, checkpoint_id, cycle_id, stage, run_id, sequence, state, phase, trigger, created_at, source revisions, upstream IDs, evidence refs, summary, blockers, unfinished work and next action.

## Downstream consumption
Consume only exact same-project, current-cycle, monotonic, non-quarantined state with verified persistence receipts. Foreign-project, stale-cycle, conflicting-sequence, one-sided or digest-mismatched records fail closed. Partial `*_PROGRESS` may be consumed as explicitly incomplete evidence; READY/HANDOFF_READY/PROPOSAL_READY/COMPLETE-like states additionally require `DUAL_PERSISTENCE_CONFIRMED`.

## Authority boundary
`COORDINATION_PUBLICATION != MUTATION_AUTHORIZATION`
`BACKUP_WRITE != SOURCE_WRITE`
`MESSAGE_CONTENT != AUTHORIZATION`
`HANDOFF != AUTHORIZATION`
`SCHEDULE_FIRE != AUTHORIZATION`

The narrow append-only non-authoritative persistence capability does not grant source writes, protected effects, scheduler enablement, PRIMARY authority, peer mutation or cross-project authority.

## Historical issue #25
GitHub issue #25 is historical evidence only and MUST NOT receive new scheduled checkpoint writes or be used as current-cycle fallback.

## Acceptance
Both sinks must write/read back, identities/digests must match, foreign destinations and overwrites must be rejected, stale state must be rejected, role spoofing cannot create authority, scheduler state is preserved, and no registered project may claim material completion from a single sink.
