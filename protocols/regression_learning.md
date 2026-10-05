# Regression Learning and Forensic Remediation Protocol

Status: ACTIVE
Scope: Global Swarm observability and bounded maintenance

## Purpose

Convert repeated failures, regressions, recovery incidents, and audit findings into deterministic engineering evidence without creating self-authorizing agents.

Learning is evidence accumulation, recurrence detection, remediation-effectiveness measurement, and generation of test/hotfix/service-pack candidates. Learning is not authority.

## Three operating levels

### UNSCOPED_CHAT
A chat not bound to a project may detect and normalize a regression event locally. It may return the event to the human or publish only through an authorized global intake path. It has no project mutation or global promotion authority.

### PROJECT_CHAT
A project-bound chat may append project-scoped regression events through the existing non-authoritative coordination publication path. It may correlate against that project's history and propose local tests/remediation. Cross-project source mutation remains denied.

### GLOBAL_PRIMARY
The authorized PRIMARY for Intercommunication Enhancements may aggregate normalized regression events across registered projects, perform forensic clustering, measure recurrence and remediation effectiveness, and generate regression tests, hotfix candidates, and service-pack candidates.

## Event invariants

Regression events are append-only and must include event identity, operating level, project binding when applicable, regression family, normalized signature, provenance class, severity, and an evidence reference. Event records never convey authority.

Deterministic fingerprints are derived from normalized family + signature. Duplicate event IDs are replay-denied. Ledger entries are hash chained so silent history modification is detectable.

## Provenance weights

OBSERVED and RETRIEVED evidence carry the strongest confidence. REPORTED_BY_AGENT and INFERRED evidence can raise attention but do not equal direct verification. EXPECTED and UNVERIFIED evidence remain low-confidence until corroborated.

## Candidate promotion

A recurring family may become a HOTFIX_CANDIDATE when corroborated evidence crosses the configured confidence/recurrence threshold. A family becomes a SERVICE_PACK_CANDIDATE when it recurs after remediation, affects multiple projects, or crosses the configured recurrence threshold.

Candidate status never authorizes deployment.

## Bounded PRIMARY maintenance lane

The Intercommunication Enhancements PRIMARY may promote a low-risk maintenance candidate only when policy explicitly classifies it as reversible, bounded, tested, non-destructive, and non-security-sensitive. This lane cannot be used for authentication, authorization, secrets, privilege/role controls, owner recovery, root/universal security governance, destructive operations, schedule activation, or cross-project source writes.

Any protected class remains subject to the normal human/external authorization gates.

## Forensic workflow

incident/audit evidence -> normalize -> fingerprint -> append -> correlate -> measure recurrence -> measure remediation effectiveness -> generate regression test -> classify hotfix/service pack candidate -> validate -> route to authorized promotion path -> verify post-change behavior

## Relationship to self-audit

Validated records from `governance/audit/ledger/` are an active evidence source for regression analysis. The learner must preserve the audit record ID, framework version, provenance classes, and source record hash when deriving a regression event. Audit findings, scores, and recommendations remain non-authoritative evidence and cannot authorize their own remediation.
