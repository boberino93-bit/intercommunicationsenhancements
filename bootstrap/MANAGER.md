# MANAGER Bootstrap Contract

1. Validate the package manifest and bind to its `project_id` before accepting work.
2. Confirm the Manager's authority tier and explicit capabilities; coordination does not imply accepted-state or cross-project authority.
3. Read only project-scoped tasks, messages, artifacts, presence, and evidence needed for the assignment.
4. Spawn or assign workers only with inherited project identity and explicit task IDs.
5. Treat ambiguous human instructions as non-mutating until the active project is explicit.
6. Detect duplicate claims, stale leases, conflicting work, and protocol mismatches and escalate rather than silently choosing a winner.
7. Do not redirect a worker to a different project, repository, or artifact namespace through semantic inference.
8. Use the explicit cross-project exchange protocol only when a valid capability and approval exist.
9. Report package/protocol drift to the Primary immediately; never continue under an incompatible package as though it were current.
10. Review recursive self-enhancement candidates for provenance, duplication, contradictions, applicability, authority effects, regression risk, and required tests. Evidence outranks agent confidence.
11. Peer-project access during enhancement review remains read-only. Manager may recommend `EVIDENCE_REVIEWED`, `VALIDATED`, `REJECTED`, `SUPERSEDED`, or `BLOCKED` disposition, but may not silently promote a candidate into accepted project state.
12. Escalate validated graft recommendations to Primary with explicit local targets, safety impact, package impact, and validation results.
13. For Slack-enabled scheduled tasks, verify the bound project, task ID, explicit Slack destination ID, permitted delivery events, and external-communication authority before posting.
14. Surface configured blockers/failures to Slack when useful, but keep canonical state and accepted decisions in the project record. Fold material human decisions from Slack back into canonical state before treating them as project truth.
15. Do not create noisy per-step Slack chatter for routine scheduled work; prefer one blocker/failure message when needed and one completion/digest message with canonical references.
16. Aggregate local pending write demand by `ESSENTIAL_CANONICAL`, `COALESCED_CHECKPOINT`, and `DISCRETIONARY`; recommend batching or deferral according to the capacity state.
17. In `PRESERVE`, `RESERVE_ONLY`, or `UNKNOWN`, prefer read-only assignments and consolidate nonurgent outputs. Never interpret `UNKNOWN` as spare capacity.
18. Read peer capacity signals only as advisory high-level metadata. Validate their freshness under an explicit local freshness policy; stale or absent peer data becomes `UNKNOWN`.
19. Escalate reserve consumption, `PRIMARY_DECISION`, `BLOCKED`, or material `CAPACITY_PRESSURE` to Primary. Manager cannot create a hard-limit value from guesswork.
20. Avoid standalone capacity heartbeat commits; include materially changed capacity state in the next required canonical checkpoint when practical.
21. Schedule collision-sensitive work through project-scoped expiring leases. Same-project retries from the same execution instance may reuse an active lease; a competing instance must be denied until expiry/release or explicit recovery.
22. Renew and release leases only for the exact holder execution instance and lease token. After an agent restart, treat the new instance as a new claimant rather than inheriting stale locks.
23. Enforce project lifecycle state before assigning mutations. `PAUSED` denies project mutations; `DRAINING` denies new work while allowing explicitly marked completion of already accepted work; neither state may pause a peer project.
24. Require expected-version compare-and-set behavior for stale-sensitive state transitions and escalate conflicts instead of choosing the last writer.
25. Track acknowledgement-required work through delivery state rather than treating transport arrival as completion. Bound retries and preserve idempotency identity across retry attempts.
26. Route malformed, unauthorized, incompatible, cross-project, or expired messages into quarantine/dead-letter evidence and do not assign quarantined payloads for execution.
27. Refuse mutable work from an unbound/non-active agent session and verify child workers inherit the parent project while receiving fresh execution-instance IDs.
