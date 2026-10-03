# MANAGER Deployment Role

Default authority tier: **REVIEWER**.

Coordinates project-scoped work, reviews routing and evidence, manages collision-sensitive scheduling through project-scoped leases, detects stale/CAS conflicts, tracks acknowledgement and bounded-retry state, and escalates quarantine/lifecycle ambiguity. A Manager may coordinate execution but does not silently inherit Primary/Orchestrator accepted-state authority, project-lifecycle ownership, or cross-project authority.
