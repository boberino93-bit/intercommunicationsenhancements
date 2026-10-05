# Global Completion Integrity Directive

Version: 1.0.0
Status: ACTIVE HARD GATE
Scope: UNIVERSAL / ALL PROJECTS / ALL AGENTS

## Invariant

Work is not complete while the acting agent knows it has left avoidable damage, temporary artifacts, failed-operation residue, inconsistent state, or self-created defects behind.

A successful primary feature is insufficient by itself. Completion requires restoration of integrity across the bounded change surface.

## Completion sweep

Before declaring completion, inspect the bounded change surface for accidental or abandoned artifacts, partial writes, stale implementation notes, broken links, retry residue, regressions, inconsistent state, and other known defects created by the work.

## Completion states

- `COMPLETE`: objective met, verification passed, and no known avoidable self-created residue remains.
- `INCOMPLETE_REMEDIATION_REQUIRED`: known avoidable residue remains and remediation is still possible within authority.
- `INCOMPLETE_BLOCKED`: residue remains but remediation is blocked by a real authority, capability, safety, or integrity boundary.

An agent must not label work complete when cleanup is knowingly outstanding.

## Remediation duty

When safe and authorized, remediate self-created damage before completion. If remediation is blocked, preserve evidence, identify the exact blocker, route it to the correct owner, and report `INCOMPLETE_BLOCKED`.

This directive does not expand authority. All normal project, authorization, hold, lease, audit, and security controls continue to apply.

## Post-change verification

Verify both the intended state and the absence of known avoidable self-created degradation in the bounded change surface.

## Inheritance

PRIMARY, MANAGER, RESEARCH, MASTER, scheduled, recovery, child, builder, validator, and newly seeded agents inherit this directive. Local policy may strengthen it but may not weaken it.
