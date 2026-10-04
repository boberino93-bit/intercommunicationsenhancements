# Cross-Project Exchange Protocol

Cross-project exchange is an explicit API boundary, never an internal AgentBus override.

A valid request requires a source-project `ACTIVE` session with `CROSS_PROJECT_EXCHANGE`, exact requesting-agent agreement, distinct source/destination projects, purpose/classification, bounded artifact references, allowed use, correlation, valid creation/expiry, and explicit approval with approver identity.

Default is DENY. Approval does not grant peer mutation rights. Data should move by value as a sanitized bounded snapshot retaining provenance. A peer imports it under its own policy.

The current alpha implements validation only; a durable sanitized export/import bridge remains future work.
