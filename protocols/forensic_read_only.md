---
title: Permanent Read-Only Forensic Investigation Protocol
protocol_id: IE-FORENSICS-READ-ONLY-PERPETUAL
protocol_version: 1.0.0
status: ACTIVE_HARD_GATE
policy: governance/FORENSIC_READ_ONLY_POLICY.json
---

# Permanent Read-Only Forensic Investigation Protocol

## Absolute invariant

Every forensic investigation concerning Intercommunication Enhancements MUST operate in read-only mode. This rule is perpetual and applies to the project kernel, all agents, child agents, swarms, sub-swarms, validators, scheduled agents, reconstructed sessions, replacement agents, and any execution environment operating from project-derived context.

**Capability is not authority. Discovery is not authorization. Forensics is not remediation.**

A forensic investigator MUST NOT mutate the system or evidence being investigated merely because write-capable tools exist, a vulnerability appears obvious, sensitive information is discovered, consensus exists, or a security incident appears urgent.

## Read-only tool gate

Before every tool invocation during forensic work, determine whether the operation is read-only.

If the operation's mutation semantics are unknown, ambiguous, undocumented, or reasonably suspected to produce a side effect, fail closed on that path. Record the limitation and continue with safe read-only work where possible.

Do not route around a denial by selecting a different mutating tool or endpoint.

## Evidence preservation

Preserve original evidence, ordering, timestamps, identifiers, hashes, provenance, revision history, contradictions, failed attempts, incomplete records, deletion/modification indicators, and uncertainty.

Do not clean, redact, sanitize, rewrite, close, delete, rotate, revoke, repair, or otherwise change source evidence during the forensic investigation.

Inspection of an independently acquired forensic copy is permitted when acquisition itself does not alter the source.

## Investigation/remediation separation

FORENSIC_INVESTIGATION and REMEDIATION are separate operational modes.

A forensic report may recommend deletion, redaction, credential rotation, revocation, patching, reconfiguration, isolation, closure, or other containment. The recommendation does not authorize the action.

Remediation requires a separately identified operational mode and separate explicit authority. The mode switch MUST NOT be inferred from urgency, severity, consensus, or possession of write-capable tools.

Finding an active security issue does not grant the forensic investigator containment or remediation authority.

## Delegation and swarm inheritance

Every delegated forensic child inherits read-only mode automatically.

Delegation may narrow access. It may never expand mutation authority. A parent may not grant a forensic child mutation authority while that child remains in forensic mode.

Agent consensus, including unanimous consensus, may support a finding or recommendation but cannot override this read-only boundary.

## Memory and persistence

Model-native, conversational, or temporary memory is non-authoritative convenience only. It MUST NOT be the source of truth for this rule, MUST NOT override it, and MUST NOT substitute for durable project governance.

The canonical durable authorities are:

- `governance/FORENSIC_READ_ONLY_POLICY.json`
- `protocols/forensic_read_only.md`

Resumed conversations, context reconstruction, agent replacement, model changes, or execution-environment changes do not reset this rule.

## Permitted activity

Read, search, enumerate, inspect, compare, hash, calculate, reconstruct chronology, inspect historical revisions and metadata, retrieve without source mutation, analyze forensic copies, correlate evidence, report findings, and recommend remediation without applying it.

## Default interpretation

When uncertain whether an action is investigation or remediation, or whether an operation is read-only or mutating, preserve state and remain read-only.

**Default outcome: READ ONLY.**

> Forensics observes. Forensics preserves. Forensics explains. Forensics does not alter the system it is investigating.
