# Roleless Project-Agent Admission Protocol

Status: **CANONICAL ADMISSION OVERLAY**

## Purpose

Allow a human to launch a generic project agent with minimal instructions such as "you are an agent working on this project; start your work" while preventing role pileups, duplicate work, stale-state execution, and authority escalation.

The admission problem is separated into four questions:

1. Which project am I in?
2. What work is currently needed?
3. Which role may I safely occupy?
4. What mutation authority, if any, do I actually possess?

Role selection never answers question 4.

## 1. Admission state machine

`UNBOUND -> PROJECT_VERIFIED -> DEMAND_ASSESSED -> ROLE_CANDIDATE -> CLAIMED -> ACTIVE`

- `UNBOUND`: read-only global/project discovery only.
- `PROJECT_VERIFIED`: exact project identity and local contract verified.
- `DEMAND_ASSESSED`: current frontier, queues, claims, leases, blockers, accepted state, liveness, intentional-stop state, and role pressure inspected.
- `ROLE_CANDIDATE`: one authorized non-escalating role selected from current project need.
- `CLAIMED`: one bounded work unit is successfully claimed/fenced when mutation or exclusive ownership is required.
- `ACTIVE`: the agent executes only inside the verified role, claim, project, capability, and mutation-authorization envelopes.

Any unresolved conflict returns to a read-only state for the affected scope.

## 2. Generic agent means capacity, not authority

A generic project agent contributes available capacity. It does not arrive as PRIMARY, Manager, Researcher, builder, or validator by assumption.

The admission layer must determine the highest-value safe role from current project demand rather than personal preference or a fixed global ratio.

Generic admission must not create authority that the human did not grant.

## 3. Required demand assessment

Before selecting a role, inspect the best available current project evidence for:

- unresolved workstreams/frontier;
- active claims, leases, fences, and ownership;
- research backlog;
- validation/contradiction backlog;
- review/integration backlog;
- implementation/prototype backlog;
- blocked work and missing capabilities;
- current Managers/Primaries and their liveness;
- intentional STOP/PAUSE/quarantine state;
- duplicate-work risk;
- capacity/backpressure state;
- latest accepted project state and source revision.

Do not infer demand from topic excitement or from the number of idle agents alone.

## 4. Role-selection rules

Role selection is demand-driven and project-local.

A generic agent may self-select only roles that the local contract explicitly marks as self-admissible. Typical self-admissible roles are Research/Specialist, Validator/Reviewer, bounded Builder/Experimenter, or Manager/Reviewer when local demand and capability gates permit.

PRIMARY is scarce authority. A roleless agent must not self-promote to PRIMARY merely because no explicit role was supplied. PRIMARY requires one of:

- explicit current human assignment;
- a valid project-local delegation/lease from an already authorized PRIMARY/MASTER within a human-approved scope; or
- another explicit local policy path that preserves equivalent authority controls.

MASTER is never self-selected through project admission.

If no self-admissible role has meaningful work, the correct result is `NO_MATERIAL_WORK`, not invented activity.

## 5. Demand-driven balancing

Do not hard-code permanent role percentages.

Prefer the role that relieves the highest verified project bottleneck while minimizing duplication and coordination overhead. Examples:

- many unresolved independent fronts + little review backlog -> favor Research/Specialist;
- large evidence backlog awaiting validation -> favor Validator/Reviewer;
- reviewed findings waiting for integration -> favor Manager/Reviewer if locally authorized;
- known bounded implementation experiment with unmet capability -> favor Builder/Experimenter;
- contradictory high-impact findings -> favor independent validation;
- high duplicate-work rate or saturated write capacity -> favor read-only synthesis/dedupe or stop admission.

Scale down or stop when useful parallel work is exhausted.

## 6. Claim-before-mutate

Before exclusive or mutating work, the agent must acquire the project-defined claim/lease/fence for one bounded semantic work unit.

The claim must identify at minimum:

- project;
- agent instance;
- role;
- work identity/objective;
- scope;
- expected output;
- lease/fence identity or equivalent ownership token;
- expiry/release semantics when applicable.

If a compatible active claim already exists, do not duplicate it unless explicitly entering an independent-validation lane.

If reliable claim coordination is unavailable, the agent may continue read-only independent work that cannot corrupt or duplicate canonical state, but must not perform conflicting mutation.

## 7. Independent validation exception

Duplicate investigation is allowed only when explicitly labeled independent validation and when the duplicated effort has expected information value, such as checking a high-risk assumption, resolving disagreement, reproducing a result, or testing a failure mode.

Independent validators must not overwrite or silently merge the original finding. They publish separate evidence and let the authorized review/integration path reconcile it.

## 8. Role switching

An active generic agent may change roles only between bounded work units.

Before switching:

1. persist useful handoff state when required;
2. release or expire the current claim/lease safely;
3. reassess current project demand;
4. select a newly authorized role;
5. acquire a new claim/lease when needed;
6. re-evaluate mutation authorization.

Role switching must never carry old write authority into the new role or task.

## 9. Mutation authorization remains separate

After role and claim resolution, every external write remains subject to `protocols/mutation_authorization.md` and any stronger consequence-specific gate.

A valid claim proves work ownership, not permission to mutate. A valid role proves organizational placement, not permission to mutate.

`ROLE + CLAIM != MUTATION_AUTHORIZATION`

## 10. Provider and capacity limits

The architecture may admit large numbers of generic agents, but it must never assume unlimited concurrency.

Admission should honor verified provider/session limits, rate limits, repository contention, artifact/storage capacity, manager/review backpressure, and project-local maximums. Unknown limits are not infinite limits.

When capacity is saturated, excess agents should remain read-only, take low-contention work, or stop cleanly rather than thrash.

## 11. Stale-state and race protection

Immediately before claim acquisition and immediately before first mutation, refresh the relevant current state when practical.

If another agent has claimed the work, the source revision materially changed, the role bottleneck disappeared, or an intentional stop appeared, abandon/reselect rather than continuing from stale admission state.

## 12. Admission audit

For material admissions, retain compact evidence sufficient to reconstruct:

- project resolved;
- demand snapshot/reference;
- selected role and reason;
- rejected duplicate role/work candidates when material;
- claim/lease identity;
- mutation-authorization state;
- stop/no-work disposition when applicable.

Do not create noisy heartbeat-only writes merely to prove admission.

## 13. Minimal human launch contract

A human may intentionally provide only project identity plus a generic instruction such as:

`You are an agent working on this project. Start your work.`

That instruction authorizes the agent to perform the read-only admission process and choose a self-admissible role. It does **not** by itself authorize external mutation unless the instruction or an active human-approved task contract separately satisfies the mutation-authorization protocol.

This distinction is mandatory for safe large-swarm operation.
