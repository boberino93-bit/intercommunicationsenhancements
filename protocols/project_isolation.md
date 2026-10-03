# Project Isolation Protocol

`project_id` is an authorization boundary, not descriptive metadata. An agent is bound once at initialization and all mutating operations validate requester ownership against target ownership. Missing or conflicting project identity fails closed. Child agents inherit the parent binding and may not self-select a foreign project.

Ordinary message, task, artifact, repository, presence, lock, lease, and package operations are project-scoped. Global infrastructure may enumerate projects but may not erase project identity.

## Required behavior

- Unbound agents may inspect only the minimum information needed to resolve project identity and may not mutate state.
- Project binding is immutable for the execution instance.
- Human-readable agent/task/artifact names are not globally unique identities.
- Resource ownership is checked again at mutation time.
- Paths are canonicalized before project-root authorization.
- Project mismatches are policy failures, not transient routing errors, and must not be retried blindly.
