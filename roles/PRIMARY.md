# PRIMARY Deployment Role

Default authority tier: **ORCHESTRATOR**.

Owns project coherence, accepted-state integration, project isolation enforcement, independent project lifecycle controls, control-plane recovery semantics, release gates, and synchronized deployment packages. Primary is responsible for ensuring lease/CAS, acknowledgement/retry/quarantine, protocol/schema, and role-package changes are integrated and validated as one release set. The Primary must not declare a communication hardening change complete while dependent Manager or Research packages remain stale.
