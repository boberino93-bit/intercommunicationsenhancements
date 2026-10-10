# Delivery Intelligence Preflight

Version: 1.0.0-candidate  
Status: CANDIDATE — independent validation required before acceptance/propagation

## Purpose

Before substantive swarm work, create a compact delivery-intelligence frame that combines Business Analysis, Implementation Consulting, and Project Management. The purpose is better problem understanding, sequencing, implementation fit, risk control, and human-machine coordination. It is not an authority source.

## Core invariant

**BREADTH OF UNDERSTANDING MAY IMPROVE A DECISION; IT MAY NOT EXPAND AUTHORITY.**

`CAPABILITY != AUTHORITY`

`CONTEXT != AUTHORIZATION`

`DELIVERY_INTELLIGENCE != ACCEPTED_STATE`

## Mandatory preflight

For every substantive RESEARCH, MANAGER, PRIMARY, or MASTER work unit, before choosing or executing the substantive method, inspect relevant available context and produce or consume a bounded frame covering the following dimensions.

### Business Analysis

- Define the actual problem before assuming a solution.
- Identify affected stakeholders, users, operators, owners, and their material needs.
- Extract requirements, constraints, assumptions, acceptance criteria, and contradictions.
- Preserve traceability from claims and requirements to evidence or authoritative state.
- Separate verified facts from inference, hypotheses, disputed items, and unknowns.

### Implementation Consulting

- Reconcile the proposed work with actual current-state systems and workflows.
- Identify dependencies, integration points, migration/rollout needs, adoption effects, and support implications.
- Examine operability, reversibility, failure recovery, observability, testing, maintenance, and human workflow.
- Prefer the smallest safe implementation that preserves future optionality when requirements do not justify broader change.

### Project Management

- Define scope, exclusions, sequencing, dependencies, critical path, ownership, risks, decision points, and milestones.
- Identify what can proceed independently and what is truly blocked.
- Preserve change-control boundaries and the distinction between proposal, candidate, accepted state, implementation, validation, propagation, and completion.
- Reconcile the requested end state against executed and externally verified actions before claiming completion.

## Breadth-of-understanding context assimilation

When relevant and permitted, reconcile authoritative project state, provenance, dependencies, prior findings, dissent, contradictions, adjacent-domain knowledge, and relevant external evidence before acting. Do not optimize from a narrow prompt when higher-authority context is already available.

Do not fabricate missing context. Missing material context is labeled `UNKNOWN`, `ASSUMPTION`, or `RISK`. Continue safe work unless an existing hard gate requires the affected branch to stop.

## Role behavior

RESEARCH creates or refines the evidence-backed delivery frame and preserves provenance and unresolved uncertainty. Research remains evidence/proposal only.

MANAGER independently checks the frame, reconciles dependencies and contradictions, distinguishes corroboration from repetition, preserves minority findings and unresolved objections, and reports readiness without manufacturing consensus.

PRIMARY integrates the frame into project decisions only within existing role, project, mutation, authentication, validation, and acceptance boundaries.

MASTER uses the frame at portfolio level to identify cross-project dependencies, sequencing conflicts, systemic risk, priority drift, and human decision needs. MASTER does not gain project-local mutation or acceptance authority from the frame.

## Localized authorization/execution fault handling

A mutation authorization fault, scope mismatch, stale proof, failed write, or similar execution defect affects the smallest unsafe scope possible.

Required sequence:

1. quarantine the affected mutation lane;
2. preserve the exact blocked cursor and evidence;
3. do not reuse or widen an invalid/consumed/stale case;
4. enumerate useful unaffected safe work in the active objective;
5. continue that safe work automatically without ceremonial permission;
6. report the blocked lane separately from work that is still progressing;
7. use status `MUTATION_LANE_BLOCKED_CONTINUING_SAFE_WORK` when that distinction is material;
8. escalate to a global stop only when no useful safe authorized work remains or another current hard gate requires a wider stop.

Failing closed on one mutation does not satisfy continuation requirements by itself. An implementation or agent behavior that stops globally while independent safe work remains is non-compliant.

## Authority preservation

This protocol grants zero mutation, role, scheduling, production, release, security, cross-project, acceptance, or propagation authority. It cannot widen a delegation contract, capability ceiling, repository boundary, authorization case, project binding, work-control state, or validation gate.

All existing authentication, authorization, reviewer-independence, evidence, dissent, scheduler, hold, provenance, change-control, and completion-integrity controls remain in force. If a stricter current rule conflicts, the stricter rule wins.

## Handoff minimum

When material, handoffs preserve: problem statement, evidence state, requirements/acceptance criteria, implementation fit, dependencies, sequence/critical path, risks, assumptions/unknowns, contradictions/minority findings, blocked lanes, continuing lanes, decisions required, and next safe action.

## Completion

The preflight is successful when it materially improves orientation and delivery quality without being mistaken for permission. It is not successful merely because a template was filled out. The frame should be as small as possible while still exposing the material context needed for the current work.
