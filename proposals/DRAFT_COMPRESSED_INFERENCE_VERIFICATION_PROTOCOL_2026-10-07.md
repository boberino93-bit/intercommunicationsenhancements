# Draft Proposal: Compressed Inference With Mandatory Verification

Status: **DRAFT — PRIMARY REVIEW REQUIRED**  
Origin project: `benefitflow`  
Target project: `intercommunicationsenhancements`  
Proposed deployment scope: global bootstrap / swarm-wide after review and validation  
Mutation authority conveyed by this draft: **NO**

## Summary

Introduce a governed capability that allows an agent to form a rapid **provisional inference** from convergent patterns, constraints, prior failures, governance signals, and current evidence before every contributing step has been explicitly enumerated.

The capability is intended to capture the useful part of instinct-like reasoning — fast anomaly detection and compressed pattern recognition — while preventing the provisional inference from being treated as truth or authority.

The required control loop is:

`signals -> compressed provisional inference -> falsification/confirmation search -> explicit verification -> verified/revised conclusion -> action`

The provisional inference is never itself sufficient authorization for an external side effect, irreversible mutation, identity/authority judgment, or high-consequence conclusion.

## Motivation

BenefitFlow Alpha 0.4 exposed a useful failure-detection pattern. Persisted project state described the application too generously as beta. Once current source, simulator behavior, test coverage, UI state, and build artifacts were examined together, the evidence rapidly converged on a different classification: a substantial alpha demonstrator rather than a defensible production beta.

The useful capability was not an ungrounded guess. It was rapid recognition that several independent signals were inconsistent with the existing classification, followed by explicit verification. Encoding this pattern may improve swarm efficiency and anomaly detection without weakening governance if the inference is treated as provisional until verified.

## Proposed capability

An agent MAY form a `PROVISIONAL_INFERENCE` when multiple independent signals materially converge.

Before that inference can affect a consequential state assertion or action, the agent MUST:

1. mark the inference as provisional;
2. identify the strongest accessible evidence that could confirm or falsify it;
3. test the inference against that evidence;
4. revise or discard it if contradictory evidence appears;
5. distinguish the original inference from the verified conclusion when auditability matters; and
6. preserve all existing authority, identity, security, user-approval, and project-boundary controls.

## Safety invariants

A provisional inference MUST NOT:

- authenticate a user, agent, or principal;
- create or extend authorization;
- bypass approval, identity, security, or evidence gates;
- justify cross-project mutation;
- convert uncertain medical, legal, financial, safety, or other high-consequence conclusions into facts;
- trigger irreversible external actions without the verification already required by the governing protocol;
- be silently rewritten as if it had been verified from the start.

If verification is impossible, the result remains provisional and must be represented as uncertainty rather than promoted to fact.

## Relationship to chain-of-thought

This proposal does not require agents to expose private reasoning traces. The auditable object is a compact operational record when needed:

- provisional conclusion;
- material signals/evidence classes;
- verification performed;
- verified/revised outcome;
- confidence or unresolved uncertainty.

The intent is auditable decision provenance, not disclosure of hidden internal reasoning.

## BenefitFlow local trial

BenefitFlow has been configured as the first local trial. Its local bootstrap enables `compressed_inference_validation` while explicitly marking the capability `PROVISIONAL_INFERENCE_ONLY` and blocking use for authority, security bypass, cross-project mutation, high-consequence fact promotion, or irreversible unverified mutation.

Local bootstrap commits:

- `36ef717f8147aaed6c321c58efa7e19b80087f1c` — human-readable bootstrap contract
- `1a4a4368a78ed0b5157b91fd142ff37f2a5dba97` — machine-readable local capability registration

This local trial is evidence for review, not precedent that automatically authorizes global rollout.

## Proposed evaluation

Before global promotion, Primary should evaluate the capability against at least these classes:

1. stale-state detection — can it notice when persisted state conflicts with current artifacts?
2. architecture inconsistency — can it detect incompatible contracts or assumptions before mutation?
3. simulator failure modes — does it improve early recognition of ambiguous/retry-unsafe states?
4. false-positive resistance — how often does rapid pattern recognition raise an anomaly that explicit verification rejects?
5. confirmation-bias resistance — does the falsification requirement materially reduce premature conclusions?
6. authority isolation — can tests prove provisional inference never creates identity, authorization, or cross-project write authority?
7. audit preservation — can a later reviewer tell what was inferred versus what was verified without requiring hidden chain-of-thought?

## Suggested rollout model

If Primary approves the design after testing:

- Stage 0: BenefitFlow local trial only.
- Stage 1: opt-in deployment to one or two low-consequence research/build projects.
- Stage 2: controlled multi-project rollout with telemetry on provisional-inference acceptance/rejection rates.
- Stage 3: bootstrap template inclusion for new projects.
- Stage 4: global default only after authority-isolation and false-positive tests remain green.

Every stage should be reversible and should preserve project-local mutation authority.

## Failure / rollback conditions

Roll back or disable the capability if it causes any of the following:

- provisional conclusions being represented as verified facts;
- increased unauthorized or cross-project mutation attempts;
- authority or identity being inferred rather than proven;
- systematic confirmation bias;
- degraded performance on ambiguity handling;
- unbounded logging of sensitive reasoning or data;
- measurable reduction in auditability.

## Requested Primary review

Primary is asked to:

1. review the conceptual distinction between compressed inference and verified conclusion;
2. threat-model interaction with authority/security overlays;
3. define a canonical schema/event if this should become a protocol-level capability;
4. build adversarial simulator tests before broad rollout;
5. decide whether the capability belongs in `AGENT_BOOTSTRAP`, a dedicated reasoning-governance protocol, or both; and
6. approve, revise, reject, or stage the rollout explicitly.

Until Primary acts, this document is a non-binding draft and conveys no global mutation or deployment authority.
