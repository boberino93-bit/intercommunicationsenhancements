# Global Completion Integrity Directive

Version: 2.0.0-candidate
Status: STAGED HARD GATE / NON-ACTIVATING
Scope: UNIVERSAL / ALL PROJECTS / ALL AGENTS

Work is not complete while avoidable residue or self-created defects remain. For material externally relevant work, completion/readiness is also impossible until dual durable persistence is confirmed.

`READY`, `HANDOFF_READY`, `COMPLETE`, `PROPOSAL_READY`, `MANAGER_REVIEW_READY`, `PRIMARY_REVIEW_READY`, `RESEARCH_HANDOFF_READY`, `MANAGER_HANDOFF_READY`, and `PRIMARY_PROPOSAL_READY` require a receipt in state `DUAL_PERSISTENCE_CONFIRMED` whose project, record ID and digest match the work record.

A single successful sink, queued write, unverified backup, mismatched digest, or historical checkpoint without a matching receipt cannot satisfy the barrier. Reconcile the project-local Message Forum and canonical GitHub backup. One-sided persistence enters recovery; same ID plus same digest is an idempotent retry; same ID plus different digest is quarantine. Corrections are new records with supersession references.

This directive does not expand authority. Persistence receipts, handoffs, readiness, roles, claims, leases and audit findings do not authorize protected effects. All authority, HOLD/STOP/PAUSE, fencing, Reliability Kernel and `ConsequenceGateway` controls remain in force.
