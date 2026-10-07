# IEP-SYNC-001 v0.1 Deployment Receipt

Status: **ROLLOUT COMMITTED; VALIDATION REQUIRED BEFORE CLAIMING RUNTIME EFFECT**

Date: 2026-10-07
Repository: `boberino93-bit/intercommunicationsenhancements`
Target branch: `main`

## Authorization chain

- `AUTH-7CE9AAD9` / GitHub issue #139 authorized the initial bounded rollout. It produced the canonical protocol and recurring-swarm integration before its 15-minute window expired.
- `AUTH-1873ECFD` / GitHub issue #145 was abandoned after an out-of-scope connector-validation write created issue #146. No further rollout mutation was performed under that case after the fault was recognized.
- `AUTH-18F87771` / GitHub issue #147 authorized completion on the reconciled current head, regression tests, validation, and corrective closure of accidental issues #143 and #146.

## Canonical rollout commits

1. `d3693e28c0d48a7e91e05cfc5eddabc7ab12faa5` — create `protocols/swarm_synchronization.md`.
2. `29b87ea06c1b33067c7be238e6da40a973642f27` — integrate synchronization into `protocols/primary_recurring_swarm_protocol.md`.
3. `a81587005956faf6f7d65adecbaf6e7bd8ec7313` — require IEP-SYNC-001 from `AGENT_BOOTSTRAP.json` while preserving concurrent governed-proposal and forensic-orchestration controls.
4. `748472dd0f311a19a09b40e1ac28e651a102fd49` — load IEP-SYNC-001 from `GLOBAL_AGENT_ENTRYPOINT.json` and add synchronization to the global sequence.
5. `82e323c67e3c4b7b9ca07b861aeb93d789fda0c9` — add regression tests for synchronization integration and stronger-control preservation.

## Architectural invariants preserved

- Heartbeat remains a sensor, not ownership authority.
- Claims / leases / fencing remain current mutation-ownership authority.
- Synchronization does not create a new persistent role, scheduler, authority store, claim system, or control plane.
- Existing mutation authorization and authority authentication remain stronger gates.
- Schedule enable/re-enable state is unchanged.
- Project isolation and project work-control gates remain in force.
- Existing governed-proposal and forensic-orchestration controls are preserved.

## Synchronization behavior activated in canonical source

Agents are required to maintain enough current shared situation state to align on mission, priorities, critical path, ownership, dependencies, contradictions, blockers, decisions, risks, and recent material changes. Agents resynchronize at startup and before claim/re-task/protected mutation boundaries, with event-driven re-synchronization for material state changes. The default focus rule limits primary-task WIP to one unless the canonical policy justifies tightly coupled support work.

## Corrective cleanup

Accidental assistant-created GitHub issues #143 (`test`) and #146 (`noop`) are authorized for closure under `AUTH-18F87771` only. They are not evidence, authority, or part of the swarm design.

## Validation truth

A repository commit proves canonical source state only. It does **not** by itself prove that every external runtime, scheduler host, adapter, active agent process, or deployment ring has loaded the new policy. Validation must therefore distinguish:

- repository readback;
- regression/CI result;
- runtime adoption evidence.

Runtime adoption remains `UNPROVEN` unless separately observed from the actual runtime substrate.
