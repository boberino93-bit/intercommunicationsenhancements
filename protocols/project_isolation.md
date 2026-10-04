# Project Isolation Protocol

Framework 1.6 treats `project_id` as a security boundary, not descriptive metadata.

1. Validate current human intent and local identity lock before continuation state.
2. Bind one execution instance to immutable project/repository/root/protocol/capability state.
3. Permit mutation only from an `ACTIVE` bound session with the required capability.
4. Never accept a caller-provided project string as proof of requester identity.
5. Reject invalid identifiers instead of lossily sanitizing them.
6. Children inherit project identity and a fresh instance; capabilities may only stay equal or decrease.
7. Project-owned task, artifact, message, lease, state and audit identifiers are project-qualified.
8. Repository/filesystem mutation stays beneath the validated project root.
9. Cross-project ordinary messaging/writes are denied; use explicit exchange.
10. Quarantine invalid evidence without executing it.
