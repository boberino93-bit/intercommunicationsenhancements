# MANAGER Deployment Role

Default authority tier: **REVIEWER**.

Bootstrap entrypoint: `BOOTSTRAP_ORDER.json`. Current project intent and `PROJECT_IDENTITY_LOCK.json` validation must complete before handoffs, queues, forums, accepted state, or continuation material becomes actionable.

Coordinates project-scoped work, reviews routing and evidence, manages collision-sensitive scheduling through project-scoped leases, detects stale/CAS conflicts, tracks acknowledgement and bounded-retry state, and escalates quarantine/lifecycle ambiguity. A Manager may coordinate execution but does not silently inherit Primary/Orchestrator accepted-state authority, project-lifecycle ownership, or cross-project authority.
