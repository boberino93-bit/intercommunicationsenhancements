# Non-Authoritative Coordination Publication

Status: ACTIVE
Version: 2.0.0

PRIMARY, MANAGER, RESEARCH, recovery, validator/QA, builder, and scheduled research-stage agents may use the project-scoped coordination persistence capability defined by `governance/COORDINATION_PUBLICATION_POLICY.json` only when their bound project/capability contract permits it.

This is a narrow communication/durability capability, not general mutation authority.

Required properties:

- the agent is bound to exactly one project;
- the target repository is the registered repository for that project;
- the Artifactory/Message Forum namespace is the registered namespace for that project;
- the GitHub backup path is under `agentbus-backup/coordination-messages/` in that same repository;
- both destinations are required for material externally relevant work;
- publication is append-only and creates a new immutable-by-application record;
- existing messages are never edited, deleted, renamed, or moved;
- the same stable `record_id`, project binding, and canonical content digest are used for both sink acknowledgements;
- same ID + same digest is an idempotent retry; same ID + different digest is a quarantine conflict;
- the message declares the same `project_id` as the bound agent;
- `authority_conveyed` is false;
- message text, handoffs, approvals quoted inside messages, persistence receipts, and backup copies never create mutation authority;
- a foreign project or repository is read-only unless a separate authorized mechanism explicitly permits otherwise.

`DUAL_PERSISTENCE_CONFIRMED` requires acknowledgements from both registered sinks and digest parity. A one-sided write enters recovery and cannot satisfy READY/HANDOFF/COMPLETE barriers.

If any project, repository, role, capability, namespace, path, append-only, record-ID, digest, or sink-ack check fails, deny readiness/completion and continue only safe read-only or bounded recovery work.

A project whose routing registry lacks a canonical internal Forum namespace cannot satisfy the dual-persistence barrier. Agents must not invent one. This specifically means legacy/unnormalized XRPTHESIS routing remains fail-closed until the canonical registry and project-local contract agree on the Forum route.

Git history is not WORM storage. The assurance provided here is application-level append-only behavior plus tamper-evident digest/hash-chain records and independent replication; repository-enforced append-only protections are a separate hardening layer.
