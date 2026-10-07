# Intercommunications Enhancements

## Mission

Turn the Organization Agent Mesh seed framework into a hardened, rapidly reusable multi-project communications control plane that safely supports several autonomous project teams at once.

## Ownership boundary

This repository owns reusable communication, identity, authorization, isolation, concurrency, cross-project exchange, deployment-package and validation contracts. It does **not** own Duo Open, BenefitFlow, or other downstream domain implementation. Each downstream Primary remains responsible for its project and synchronized deployable role packages.

## Speaker identity continuity invariant

**Conversation continuity is not identity continuity.** The swarm must never infer that the current speaker is the registered human principal merely because the same account, device, conversation, project, writing style, personal history, or familiar relationship appears to continue. Material gaps, resumes, device/session discontinuities, or security-relevant context changes lower assurance but do not prove takeover. Sensitive historical disclosure and protected action require consequence-proportional re-establishment of speaker continuity. High-consequence action continues to require fresh principal claim, independent proof, and case-bound authorization under the existing authority controls. Continuity uncertainty never changes the root-authority registry and blocks only identity-dependent branches while safe unrelated work continues.

## Paramount semantic invariant

After non-negotiable platform safety, project-binding, authority, security, and mutation-control gates are satisfied, **human–machine alignment is the first semantic optimization target**. The system must preserve an accurate shared understanding of the human objective, requested end state, material constraints, success conditions, uncertainty, disagreement, and corrections before optimizing task speed, autonomy, swarm throughput, elegance, or agent convenience.

Alignment is not agreement, sycophancy, or routine confirmation. A blocker is not a stop condition or completion state while safe goal-advancing work remains; agents continue through machine-resolvable paths until the requested solution is available or a genuine non-delegable human gate remains with no further safe progress. Clear instructions should proceed without ceremony; material ambiguity should be surfaced; material human corrections are high-priority state updates. Brief, natural pleasantries are encouraged as functional human-interface alignment signals when appropriate, never as filler that hides disagreement, uncertainty, bad news, or blockers.

Human attention is scheduled as a scarce control-plane resource. When a human gate can safely wait, the swarm freezes only the dependent branch and drains all useful independent work before interrupting the human. Compatible non-urgent decisions should be batched when that does not delay urgent or architecture-determining choices. The intended result is that human approval unlocks a minimal residual execution set rather than a large body of work that could already have been completed.

The project treats the human–machine collaboration itself as a governed learning system. Reusable lessons may arise from task outcomes, human corrections, communication failures, scheduling mistakes, or failures in the learning process itself, but they become inherited doctrine only through evidence, validation, provenance, dissent preservation, reversibility, and authorized promotion. This is cumulative control-plane learning, not a claim that conversation retrains model weights or that recursive improvement can authorize itself.

Communication channels should match the information topology. Text is preferred for exact directives and durable decisions; screenshots for static visual state; video for temporal workflows, transitions, timing, and reproduction sequences; narration for synchronized intent or expectation; structured files/logs for exact machine evidence. Human credentials and machine capability are not substitutes for evidence. Claims of uniqueness or novelty must be actively falsified rather than rewarded for sounding exceptional.

## Core invariants

1. Every active agent is immutably bound to exactly one project and execution instance.
2. Mutation authority comes from the active bound session plus capabilities, never a self-asserted project ID.
3. Child agents inherit project/repository/protocol identity and cannot escalate parent capabilities.
4. Mutable resources belong to one project; canonical identifiers are validated without lossy normalization.
5. Ordinary AgentBus traffic is intra-project and claimed sender identity must match the bound session.
6. Cross-project exchange is explicit, capability-gated, approved, bounded, provenance-preserving and copy-by-value.
7. Missing/conflicting/foreign identity fails closed; invalid input is retained only as non-executable quarantine evidence.
8. Collision-sensitive work uses project-scoped execution-instance leases; stale-sensitive writes use expected versions.
9. Deployment packages declare project, role, capability set, protocol/framework/package versions, dependency-map hash, source revision and component hashes.
10. Package dependency closure is recomputed from source; a protocol/framework change is incomplete until affected roles are rebuilt, verified and reproducible.
