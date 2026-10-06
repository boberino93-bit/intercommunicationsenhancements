# Hardened Hybrid Admission Shadow v2

Status: **STAGED / DISABLED / NON-ACTIVATING**

This protocol stages a safety-first hybrid capacity allocator without changing production scheduling or authority.

## Core invariant

`CAPACITY != PLACEMENT != ROLE != AUTHORITY`

The Priority Frontier is discovery-only. A placement proposal is not ownership. A role grant is organizational only. A claim or lease is not mutation authority. Protected effects remain subject to the existing mutation-authorization policy, reliability ownership/fencing, and `ConsequenceGateway`.

## Reused controls

The shadow design deliberately reuses existing controls instead of introducing parallel security systems:

- scheduled/provider admission remains upstream;
- roleless admission remains the organizational placement model;
- `project_work_control` remains authoritative for HOLD/resume decisions;
- project-local `self_admissible_roles` is re-resolved for the exact target project;
- existing claims/leases/versioning and reliability ownership epochs remain the ownership boundary;
- `ConsequenceGateway` remains the sole protected-effect commit boundary;
- current human mutation authorization remains independently required.

Hybrid admission produces only a non-authoritative `precondition_digest` that may be included among the evidence supplied to the existing protected-effect path.

## Launch modes

`ROLE_BOUND`: project and role are explicitly supplied. This compatibility mode does not permit generic role inference.

`PROJECT_CAPACITY`: project is bound; role is absent at launch and may be requested after local admission checks.

`PORTFOLIO_CAPACITY`: project and role are absent; discovery is read-only until a target project independently admits the agent.

Unknown or ambiguous modes fail closed. Replay and fingerprint mismatch fail closed.

## Priority Frontier

Frontier snapshots are compact indexes derived from bounded project demand digests. They are revision/run bound, expiring, and explicitly non-authoritative. Priority uses hard constraints and tiers before multidimensional ordering. Human priority requires authenticated provenance; privileged tier-0 priority requires separate verification. Saturated downstream review is negative pressure, not a reason to create more upstream work.

## Project-local admission

Generic self-admission is limited to the exact target project's current `self_admissible_roles`. The shadow runtime refuses roles outside the bounded generic family (`research`, `manager`) and refuses peer self-admission where the target list is empty.

Project HOLD or any control state that denies new work blocks admission. Source-revision mismatch blocks admission. The target is a useful decision within 30 seconds; beyond approximately 45 seconds the safe result is `ADMISSION_BLOCKED`, not indefinite crawling or invented work.

## Hybrid schedule definition

The staged schedule is disabled. It defines three `PROJECT_CAPACITY` slots, one project-capacity slot reserved for integration/validation when demanded, and one experimental `PORTFOLIO_CAPACITY` slot. No scheduled slot may create Primary authority. Existing fixed scheduling remains production state until a separate migration/activation authorization explicitly supersedes it.

## Historical contradiction

Current historical material contains inconsistent generic-start semantics, including older text that can be read as defaulting a generic actionable launch to Primary while newer roleless-admission contracts deny generic Primary self-promotion. This shadow package does not silently rewrite history. It proposes a future explicit supersession: generic capacity contributes capacity only; Primary is not self-selected by generic admission. Production documentation is unchanged by this staging package.

## Failure families

The shadow model uses explicit blocked states including launch invalid/replay, stale or mismatched Frontier inputs, invalid provenance, project identity/control conflict, role-admission denial, claim conflict, authorization required, cross-project scope violation, no material work, and admission-SLA exceeded.

Unrelated safe read-only work may continue where existing governance permits it; these states never manufacture authority.

## Rollout

1. Shadow evaluation only.
2. Compare recommendations with current/human decisions and measure admission latency/collisions/backpressure.
3. Separate authorization for any live canary.
4. Separate authorization for scheduler migration, peer-project adoption, Stage-15 launch, or scaler interaction.

This PR does **not** activate, merge, propagate, increase capacity, or launch a swarm stage.
