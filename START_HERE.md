# Intercommunications Enhancements — Start Here

This repository hardens the Organization Agent Mesh for simultaneous unrelated projects.

## Bootstrap order

1. Validate current human project intent.
2. Validate `PROJECT_IDENTITY_LOCK.json`.
3. Validate the package manifest/project/repository/source identity.
4. Bind one immutable execution instance and its declared capability set.
5. Initialize and become `ACTIVE` before any mutation.
6. Only then load handoffs, queues, forums and accepted state.

## Current alpha invariants

- Caller-supplied project IDs are untrusted; bound session identity authorizes mutation.
- Invalid canonical IDs are rejected rather than rewritten into ambiguous aliases.
- Internal messages require matching projects and bound sender identity.
- Cross-project exchange uses its own approved capability-gated contract.
- Children inherit project identity and may only retain or reduce capabilities.
- Task/lease/artifact/state mutations are project-scoped and version/ownership protected.
- PRIMARY, MANAGER and RESEARCH packages are dependency-closed, exact-SHA traceable, component-hashed and reproducible.

Run `python tests/run_all.py` for tests. Build with `python tools/build_agent_packages.py --source-revision <commit> --out dist`, validate with `python tools/verify_agent_packages.py`, independently rebuild to another directory, then compare with `python tools/check_reproducible_packages.py dist <other-dir>`.
