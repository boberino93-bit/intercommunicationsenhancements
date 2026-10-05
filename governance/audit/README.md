# Agent Self-Audit Ledger

This directory is the canonical repository-readable self-audit subsystem for Intercommunication Enhancements.

## Structure

- `AUDIT_PROTOCOL.md` — trigger, append-only, integrity, provenance, framework-evolution, and authority rules.
- `templates/AGENT_SELF_AUDIT_FRAMEWORK.md` — current authoritative framework.
- `templates/AUDIT_RECORD_SCHEMA.json` — canonical record schema.
- `framework-history/` — immutable framework-version snapshots.
- `ledger/` — one immutable JSON file per audit record.
- `LEDGER_HEAD.json` — current anchored record count/head ID/head hash.

## Append procedure

1. Resolve the current framework and framework version.
2. Identify agent, role, instance, project, task, and parent/controller when applicable.
3. Perform the common core plus the applicable role extension.
4. Classify material evidence using the canonical provenance classes.
5. Create the next audit record without editing prior ledger files.
6. Set `previous_audit_record` and `previous_record_hash` from the anchored head.
7. Compute `record_hash` from deterministic canonical serialization excluding the `record_hash` field itself.
8. Validate the existing chain, new record, and expected head.
9. Create the new ledger file.
10. Advance `LEDGER_HEAD.json` only after the new record is durably present and verified.

Corrections and changed conclusions are new records. Historical audit files are never silently edited or deleted.

## Comparability

All roles share the mandatory comparative score keys. Role extensions add relevance without replacing the common core. Framework versions are preserved on every record so longitudinal and cross-agent analysis can account for scoring/schema changes.

## Authority

Audit history is observability data. Findings, scores, trends, recommendations, and recurring patterns are not execution authority.
