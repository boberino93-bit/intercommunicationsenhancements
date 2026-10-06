# Mutation Authorization Protocol

Status: **CANONICAL HARD GATE**

## Purpose

Prevent intent, role, prior permission, schedules, delegation, repository permission, or tool availability from becoming durable write authority.

Core invariants:

`INTENT != AUTHORIZATION`

`AUTHENTICATION != AUTHORIZATION`

`AUTHORIZATION IS SINGLE-USE AND CASE-BOUND`

`PRE_MUTATION_AUTHORIZATION_REQUIRED BEFORE ANY DURABLE WRITE`

This protocol is coupled to `protocols/authority_authentication.md`, `governance/AUTHORITY_AUTHENTICATION_POLICY.json`, `protocols/actionable_link_delivery.md`, and `governance/ACTIONABLE_LINK_DELIVERY_POLICY.json`.

## 1. Mutation boundary

A mutation is any externally durable side effect, including repository/file changes, commits or merges, pull-request or issue state changes, artifact publication, deployment/release, schedule state changes, persistent messages, configuration changes, or other durable external state changes.

Read-only discovery, inspection, analysis, comparison, simulation, local scratch work, and proposal generation do not cross the mutation boundary.

## 2. Required authorization source

The only standalone mutation authorization source is a current human single-use authorization case.

Before a mutation can begin:

1. explicitly identify the authority principal;
2. establish that the principal is registered for the requested action;
3. create a bounded case with a unique case ID, exact target, mutation class, consequence class, action digest, issue time, and expiry;
4. when a prefilled approval surface is supported, surface the case-specific actionable approval link using only safe non-secret case metadata before waiting for approval;
5. receive explicit human authorization naming the current case;
6. for high-consequence cases, verify the required independent external principal proof;
7. revalidate case freshness, non-replay state, target, revision, scope, claim/lease/fence where required, and action digest immediately before the write.

Prior permission, an active task, schedule firing, delegation, role, repository permission, conversation continuity, or available write tooling are not authorization.

## 3. Authorization-link gate

The actionable-link delivery policy is a universal pre-mutation bootstrap dependency.

A supported approval link MUST include the current case-binding metadata needed for the human to review and submit the approval without reconstructing it manually. It MUST NOT include secret authentication material.

If the exact safe approval surface can be constructed but authenticated accessibility cannot be verified, disclose the limitation, classify the link as `UNVERIFIED_DIRECT`, and still surface it. Verification uncertainty alone is not a reason to suppress a safe case-specific link.

Opening or rendering a link is not authorization. Link generation is not authorization. The human-produced external proof must still be verified.

## 4. No ambient authorization

There is no session-wide, conversation-wide, project-wide, task-wide, schedule-wide, or role-wide mutation authority.

Every distinct mutation case requires its own case ID and fresh authorization. A case may cover multiple low-level writes only when they are explicitly part of one bounded action.

A case is consumed or invalidated by successful completion, cancellation, denial, expiry, material scope change, or replay attempt.

## 5. Fail-closed behavior

If principal identity, required authentication, case authorization, freshness, non-replay state, target, revision, scope, or action digest is absent, stale, ambiguous, conflicting, or invalid:

1. do not perform the affected write;
2. continue useful safe read-only work;
3. preserve current state;
4. surface the exact blocked mutation and authorization gap;
5. surface the case-specific approval link when supported;
6. require a new case after expiry or material scope change.

Do not repeatedly ask permission for read-only work.

## 6. Role and tool separation

PRIMARY, Manager, Researcher, validator, builder, recovery agent, project owner, scheduler, claim holder, or lease holder status does not grant mutation authority.

Raw connector or tool write capability is not authority. Availability of a write method MUST NOT bypass `PRE_MUTATION_AUTHORIZATION_REQUIRED`, case validation, or the high-consequence proof gate.

## 7. Precedence

This protocol is additive. If another current policy is stricter, the stricter rule wins. No lower-level task or project-local contract may weaken this gate.
