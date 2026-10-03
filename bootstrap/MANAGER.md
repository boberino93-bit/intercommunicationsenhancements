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
