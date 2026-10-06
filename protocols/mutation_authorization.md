# Mutation Authorization Protocol

Status: **CANONICAL HARD GATE**

## Purpose

Prevent an agent from converting human intent, identity assumptions, prior permission, enthusiasm, capability questions, schedules, delegation, or inferred preference into durable write authority.

The central invariants are:

`INTENT != AUTHORIZATION`

`AUTHENTICATION != AUTHORIZATION`

`AUTHORIZATION IS SINGLE-USE AND CASE-BOUND`

This protocol is coupled to `protocols/authority_authentication.md` and `governance/AUTHORITY_AUTHENTICATION_POLICY.json`.

## 1. Mutation boundary

A mutation is any externally durable side effect, including repository/file create-update-delete, commit, merge, pull-request state change, issue/comment publication, artifact publication, deployment/release, scheduled-task state change, persistent forum/message write, production/configuration change, or any other action that changes durable external state.

Read-only discovery, inspection, search, analysis, comparison, simulation, local scratch work, and proposal generation do not cross the mutation boundary.

## 2. Required authorization source

The only standalone mutation authorization source is a current human single-use authorization case.

Before a mutation case can be authorized:

1. the authority principal must be explicitly claimed;
2. the claimed principal must match the registered authority applicable to the requested action;
3. the agent must create a bounded authorization case with a unique case ID;
4. the human must explicitly authorize that case ID;
5. high-consequence cases must also satisfy the independent-authentication requirement in the authority-authentication policy.

Prior authorization, prior authentication, an active task contract, schedule firing, parent-agent delegation, role, seniority, repository permission, urgency, project ownership, conversation continuity, or agreement with the goal are not authorization sources.

## 3. No ambient or persistent authorization

There is no session-wide, conversation-wide, project-wide, task-wide, schedule-wide, or role-wide mutation authority.

A previous authorization—even one issued seconds earlier in the same conversation—MUST NOT authorize a distinct mutation case.

Every distinct mutation case requires its own case ID and fresh human authorization. The case is single-use.

## 4. Authorization case requirements

Before execution, the acting agent MUST establish a case record containing at least:

- case ID;
- claimed principal;
- authentication disposition;
- target project/repository/system;
- mutation class;
- bounded scope;
- consequence class;
- action digest or equivalent immutable action description;
- issue time;
- expiry time;
- explicit human authorization referencing the case ID;
- consumption state.

The default case lifetime is 15 minutes unless a stricter policy applies.

## 5. Case scope and consumption

A case may cover multiple low-level writes only when those writes are explicitly enumerated or are strictly necessary atomic steps of the one bounded action described by the case.

A new case is required when any of these materially change:

- target repository/project/system;
- mutation class;
- destructive or irreversible consequence;
- production/release scope;
- credential/security boundary;
- financial effect;
- scheduled-task enabled state;
- cross-project scope;
- task objective or revision;
- any other material scope element.

A case is consumed or invalidated by successful completion, cancellation, denial, expiry, material scope change, or attempted replay. A consumed case MUST NOT be reused.

## 6. Scheduled and delegated work

Scheduled tasks may launch, inspect, research, analyze, validate, simulate, prepare patches, and formulate authorization cases without mutation authority.

A schedule firing is never authorization. A previously approved schedule or task contract is not future write permission. Each distinct scheduled mutation case requires fresh human authorization.

Delegation may narrow execution inside an already authorized case but cannot create human authorization, expand case scope, or authorize a new mutation case. A child agent may participate under the exact same unconsumed case only when the case explicitly includes that bounded delegated operation.

## 7. High-consequence step-up

Root authority changes, universal governance changes, production deployment/promotion, security or credential-boundary changes, financial actions, destructive or irreversible operations, scheduled-task enable/re-enable actions, and cross-project mutations require independent principal proof in addition to the single-use case authorization.

The default process-separated proof is defined in `protocols/authority_authentication.md`. Static personal information is not acceptable authentication.

## 8. Fail-closed behavior

When the principal claim, required authentication, case authorization, case freshness, non-replay state, target, or scope is absent, ambiguous, conflicting, stale, or invalid:

1. do not perform the affected write;
2. continue useful read-only inspection, analysis, validation, or patch preparation when safe;
3. preserve current project state;
4. surface the exact blocked mutation and case/authentication gap;
5. ask only for the case-specific human action actually required.

Do not repeatedly ask permission for read-only work.

## 9. Role separation

Being PRIMARY, Manager, Researcher, validator, builder, MASTER, recovery agent, project owner, or scheduler does not grant mutation authority. Authentication does not grant mutation authority. A lease or claim does not grant mutation authority.

No agent, consensus, learning system, or child process may manufacture, waive, extend, or reuse human authorization.

## 10. Audit

Material authorization decisions SHOULD record compact non-secret evidence including:

- case ID;
- claimed principal;
- authentication disposition;
- operation class;
- target scope;
- authorization disposition (`ALLOW`, `DENY`, `UNRESOLVED`);
- governing rule;
- whether a write was prevented;
- whether the case was consumed;
- corrective action.

Do not store passwords, tokens, government identifiers, dates of birth, family names, static personal authentication answers, cookies, or unnecessary verbatim conversation text.

## 11. Precedence

This protocol is additive. If another current policy is stricter, the stricter rule wins. No lower-level task prompt or project-local contract may weaken this gate.
