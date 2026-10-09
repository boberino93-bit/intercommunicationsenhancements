# Pending Work — Memory Retention, Continuity, and Communication Hardening

**Status:** CANDIDATE / NON-CANONICAL / NOT DEPLOYED  
**Branch:** `pending-work/memory-continuity-2026-10-09`  
**Change class:** `UNIVERSAL_SWARM_CHANGE`  
**Purpose:** Preserve today's continuity findings in a contained staging area without changing the active bootstrap, active memory policy, AgentBus contract, or canonical runtime during the recommendation/timelock window.

## Why this exists

The current system already has two important active protections:

1. `IEP-MEM-001` — swarm collective state is external-only; native ChatGPT memory is not a swarm database, fallback, log, cache, authority source, or canonical state.
2. `IEP-CTX-001` — context is layered and provenance-bound; an agent must inspect available authorized layers before declaring context missing or asking the human to reconstruct it.

The current incident/reconstruction showed a further failure mode:

```text
MATERIAL KNOWLEDGE CAN SURVIVE
+
RELATIONSHIPS AMONG KNOWLEDGE CAN FAIL TO SURVIVE
=
DISTRIBUTED CONTEXT FRAGMENTATION
```

The pending work therefore extends retention from "store the state" toward:

```text
CAPTURE
→ PRESERVE
→ PROVE
→ LINK
→ DISCOVER
→ RECONSTRUCT
→ CHALLENGE
→ RESTORE
```

without weakening:

```text
PRIVACY
PROJECT ISOLATION
AUTHORITY SEPARATION
EPISTEMIC STATUS
CONTRADICTION PRESERVATION
AUTHORSHIP PROVENANCE
```

## Files in this pending-work package

- `MEMORY_RETENTION_CONTINUITY_PLAN.md` — consolidated implementation requirements.
- `AI_BEHAVIOUR_LAB_COMMUNICATION_IMPORT.md` — security-reviewed communication/capacity controls proposed for import from AI Behaviour Control Lab.
- `PORTABLE_AGENT_RECOVERY_BIOS.md` — the proposed "AI Agent BIOS" / portable recovery kernel concept.
- `PENDING_POLICY_DELTA.json` — machine-readable pending policy delta.

## Active-policy boundary

Nothing in this directory supersedes or mutates:

- `governance/SWARM_MEMORY_PERSISTENCE_POLICY.json`
- `protocols/external_swarm_memory.md`
- `governance/LAYERED_CONTEXT_POLICY.json`
- `protocols/layered_context_resolution.md`
- `AGENT_BOOTSTRAP.json`
- `BOOTSTRAP_ORDER.json`
- any current authorization, hold, lease, or fence.

Possession of this pending-work package conveys **zero mutation authority**.

## Security posture

This folder intentionally excludes:

- credentials, tokens, secrets, or authentication material;
- private human conversation payloads;
- customer/employer data;
- raw cross-project research payloads;
- any mechanism that converts metadata visibility into cross-project write permission;
- any rule that uses restored memory as authority.

The AI Behaviour Control Lab material imported here is limited to communication/continuity controls whose current source explicitly prohibits secrets, personal data, unredacted research payloads, credentials, unrestricted task content, and cross-project mutation authority.

## Advancement gate

Do not merge or deploy until all of the following are satisfied:

```text
ACTIVE PAUSE / TIMELOCK EXPIRED OR FORMALLY RESOLVED
→ CURRENT SOURCE SHAS RE-READ
→ PRIVATE-STORE DECISION COMPLETE
→ SECURITY / PRIVACY REVIEW
→ HERD REVIEW
→ ZERO UNRESOLVED CRITICAL OBJECTIONS
→ EXACT CHANGESET DIGEST
→ FRESH CASE-BOUND AUTHORIZATION
→ READ-ONLY / SHADOW CANARY
→ FAILURE INJECTION
→ READBACK
→ CONTROLLED PROMOTION
```
