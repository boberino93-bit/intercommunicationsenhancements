# Self-Audit Bootstrap Overlay

Status: ACTIVE
Scope: Intercommunication Enhancements agents and globally routed project agents consuming canonical governance

## Trigger invariant

When an agent is asked to self-evaluate, audit itself, assess its performance or capability, review its behavior/compliance, or perform an equivalent introspective assessment, it MUST:

1. load `governance/audit/AUDIT_PROTOCOL.md`;
2. load the current `governance/audit/templates/AGENT_SELF_AUDIT_FRAMEWORK.md`;
3. identify its agent identity, role, role version, instance, project, task, and parent/controller where applicable;
4. execute the common framework plus the applicable role extension;
5. classify material evidence using the canonical provenance classes;
6. create a new immutable audit record under `governance/audit/ledger/`;
7. validate the existing ledger chain, new record hash, previous-record linkage, and `governance/audit/LEDGER_HEAD.json`;
8. append the new record without changing historical audit files;
9. advance the anchored ledger head only after the new record is durably present and verified;
10. return the human-readable audit to the requester.

If the canonical framework cannot be retrieved, return `AUDIT_FRAMEWORK_UNAVAILABLE`. Do not improvise another evaluation framework.

## Authority boundary

`Finding != Recommendation != Authorization != Execution`.

Audit records, scores, trends, framework recommendations, recurring findings, and regression-learning outputs do not create mutation authority. Any operational remediation remains subject to existing project, role, authorization, security, lease/fence, hold, backup, validation, and audit controls.

## History and framework evolution

Historical records are append-only. A correction or changed conclusion is a new record referencing the earlier one; do not silently edit or delete an unfavorable record.

Framework changes are separate governed operations. Agents may recommend changes but may not activate them during audit execution.

## Regression-learning handoff

A validated audit record may be consumed by the regression-learning system only as non-authoritative evidence. Preserve the audit record ID, framework version, provenance classes, and source record hash when deriving a regression event.
