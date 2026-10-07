# External Swarm Memory and Persistence Protocol

Status: ACTIVE  
Priority: P1  
Policy: `governance/SWARM_MEMORY_PERSISTENCE_POLICY.json` (`IEP-MEM-001`)

## Purpose

This protocol defines the swarm persistence boundary. Native ChatGPT memory is not a swarm database, cache, message bus, recovery store, log, or source of truth. Swarm collective state is external-only.

## P1 invariant

No swarm memory protocol, bootstrap, scheduler, handoff, synchronization path, learning path, forensic service, cache, log, collective-state service, or recovery path may call, query, ingest from, depend on, or fall back to native ChatGPT memory recall for swarm state.

The invariant applies to PRIMARY, MANAGER, RESEARCH, roleless admission, scheduled launches, successor agents, recovery agents, and any future role or service that participates in the mesh.

## Authorized persistence surfaces

1. **Canonical coordination and accepted swarm state:** `/Intercommunication enhancements/AgentBus/messages` in the Internal Artifactory/AgentBus surface.
2. **Durable source/version-control and coordination backup:** `boberino93-bit/intercommunicationsenhancements`, including the registered `agentbus-backup/coordination-messages/` namespace where applicable.

GitHub is not allowed to silently replace the canonical Artifactory board. Repository state may corroborate, version, back up, or recover externally persisted records according to the governing protocol, but authority conflicts must be surfaced rather than guessed through.

## Native ChatGPT memory boundary

For swarm purposes, native ChatGPT memory has all of the following classifications:

- swarm authority: **DENY**
- protocol access: **MUST NOT CALL**
- recall ingestion: **DENY**
- availability fallback: **DENY**
- cache source: **DENY**
- log source: **DENY**
- collective-state source: **DENY**
- mutation authority: **DENY**

A model may receive ordinary host-provided conversation context as part of the execution environment, but it must not elevate an unverified memory recollection into swarm collective state, provenance, completion evidence, authorization, or a substitute for required external readback.

## Local runtime state

Local files, SQLite, process memory, test fixtures, and temporary computation remain permitted for reference implementations and transient execution only when explicitly non-authoritative. They must not be represented as swarm-wide accepted state or used to claim propagation.

If local state contains a material result another agent is expected to act on, externalize that result to the applicable Artifactory/AgentBus surface and GitHub record required by the governing protocol before treating it as durable collective state.

## Read and recovery order

When authoritative context is needed:

1. resolve project and role;
2. read the canonical Artifactory/AgentBus state required by the local bootstrap;
3. read the registered GitHub source/version-control or backup record when required for revision/provenance/recovery;
4. reconcile external records explicitly;
5. stop the affected authority-dependent branch on material conflict;
6. never query native ChatGPT memory as a fallback.

If the canonical external persistence surface is unavailable, fail closed for the persistence-dependent branch and continue only unrelated safe work allowed by the existing continuation contract.

## Conflict handling

- Artifactory/AgentBus remains canonical for live coordination.
- GitHub must not silently override a conflicting canonical board record.
- Native ChatGPT memory never wins a conflict and is not an admissible authority source.
- A fact that exists only in native memory is non-authoritative until externally persisted and independently read back.

## Completion and propagation claims

A claim that a P1 swarm-memory directive or material swarm record was propagated requires evidence for both external layers when both are required by the governing workflow:

- successful Artifactory/AgentBus publication and readback; and
- a GitHub revision or registered coordination-backup record and readback.

One store does not imply the other. A chat response, native memory update, local artifact, or unverified write attempt is not propagation evidence.

## Forensic precedent — 2026-10-07

Example A demonstrated a native `Memory updated` event while project-level reasoning/context was being persisted. The resulting forensic finding is classified **CONFIRMED_FAULT** because it created an unintended persistence route outside the swarm's external control plane.

Canonical forensic record:
`/Intercommunication enhancements/AgentBus/evaluation/20261007T170000Z__MEMORY_PERSISTENCE_FAULT_FORENSIC_REPORT.md`

This incident is the regression basis for `tests/test_swarm_memory_policy.py`.
