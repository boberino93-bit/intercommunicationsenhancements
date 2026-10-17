# V26 AgentBus Recovery Migration

Status: **GOVERNED RECOVERY PLAN**  
Scope: **Intercommunication Enhancements only**

## Purpose

Recover the internal ChatGPT Library AgentBus message board without destroying uninspected evidence, and reconcile it cleanly with canonical GitHub V26 source state.

The registered live board is:

`/Intercommunication enhancements/AgentBus/messages`

The board is a ChatGPT Library AgentBus surface. Historical repository labels such as `INTERNAL_ARTIFACTORY` and `ARTIFACTORY` are retained only as compatibility aliases; they do not mean JFrog.

## Authority split

- GitHub `main`: canonical versioned source, governance, schemas and durable backup.
- Internal ChatGPT Library AgentBus: canonical live project coordination/event stream.
- VMBUS: standalone runtime/context/readiness layer.

These are different authorities. A write to one does not prove a write to another.

## Record reconciliation

Reconcile corresponding records by:

1. `logical_record_id`
2. `payload_sha256`

Same ID + same digest means equivalent. Same ID + different digest means conflict. Merely having different sets of records in two stores is not by itself a record conflict.

## Required destructive recovery order

1. Inspect the live AgentBus.
2. Export the complete current board.
3. Hash the export and record message count/manifest.
4. Independently read the export back.
5. Only after steps 1-4 pass, retire/delete the live board under a fresh destructive high-consequence authorization case.
6. Recreate the registered board namespace.
7. Seed a V26 genesis record containing the canonical GitHub source revision and V26 artifact digest.
8. Read the genesis record back from AgentBus.
9. Create the matching GitHub reconciliation record.
10. Read the GitHub record back.
11. Verify `logical_record_id` and `payload_sha256` equality.
12. Mark synchronization complete.

## Fail-closed rules

`RETRIEVAL_FAILURE != ABSENCE_OF_EVIDENCE`

`MATERIALIZED != INSPECTED`

`PRESERVED != VERIFIED`

`GITHUB_WRITE != AGENTBUS_WRITE`

`STORE_DIFFERENCE != RECORD_CONFLICT`

No board deletion is permitted when the current board remains uninspected or the fresh archive has not been independently verified.

## Runtime limitation recorded during this migration

The runtime preparing this migration did not expose ChatGPT Library create/update/delete operations. Therefore this repository work prepares and validates the migration but does not claim that the Library board was reset or reseeded.

## Project isolation

CV Support remains non-federated and is outside this migration. No scheduler state or peer project repository is changed by this migration.
