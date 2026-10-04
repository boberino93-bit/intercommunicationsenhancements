# Intercommunications Enhancements — Start Here

This repository hardens the Organization Agent Mesh for simultaneous unrelated projects.

## Universal launch path

An agent launched **outside any project** must begin at `UNIVERSAL_AGENT_ENTRYPOINT.md`, not by guessing a project from the task topic. The universal layer stays read-only while it resolves exactly one registered project, can consult registered forum/handoff metadata only for exact ownership identifiers, then verifies the target project's local contract and enters that project's normal bootstrap.

The machine-readable anchor is `GLOBAL_AGENT_ENTRYPOINT.json`; the detailed protocol is `protocols/universal_task_routing.md`.

## Bootstrap order

For an already project-bound agent:

1. Validate current human project intent.
2. Validate `PROJECT_IDENTITY_LOCK.json`.
3. Validate the package manifest/project/repository/source identity.
4. Bind one immutable execution instance and its declared capability set.
5. Initialize and become `ACTIVE` before any mutation.
6. Only then load handoffs, queues, forums and accepted state.
7. Classify the incoming work through `protocols/task_intake_and_delegation.md` before project mutation.
8. Execute only inside the validated project/task/delegation boundaries.

## Task entry and routing

Every agent must distinguish the kind of work it has received before acting:

- `EXISTING_PROJECT_TASK`: continue only after loading the validated project's accepted state, handoffs, queues and applicable task/delegation scope.
- `NEW_PROJECT_BOOTSTRAP`: do **not** write the new project's state into this framework project or any unrelated project. Establish a distinct project identity, repository/workspace boundary and project-scoped coordination/recovery state first; then define the problem, source-of-truth hierarchy, workstreams and research-assistance decision.
- `CROSS_PROJECT_EXCHANGE`: use the explicit approved cross-project exchange contract; ordinary internal messaging is not a bridge.
- `FRAMEWORK_MAINTENANCE`: changes to this reusable framework remain framework-scoped and must not absorb instance-specific project state.
- `AMBIGUOUS_PROJECT`: fail closed on mutation until the target project identity is resolved.

A user instruction naming a target project or explicitly asking for a new project is intent evidence, not permission to bypass identity, capability, isolation or write-boundary checks.

## Primary intake responsibility

For a new project or materially new workstream, Primary must persist a task intake record before risky implementation. The intake defines the problem and source-of-truth hierarchy first, decomposes actual technical/work domains, records risk and uncertainty, determines whether research assistance is justified, and records the proposed Research/Manager topology. Delegated work must use explicit delegation contracts with scope, sources, tools, write boundaries, evidence requirements, output contract, completion condition and failure condition.

Research findings, hypotheses and implementation authority remain distinct. Adaptive sizing or experimental policy may inform a Primary decision, but never grants spawn or mutation authority by itself.

## Current alpha invariants

- Unbound agents may read routing metadata but cannot mutate any project.
- A generic human-launched task agent defaults to the target project's `primary` workflow only after one project is resolved; the target project must still authorize and activate that role.
- Caller-supplied project IDs are untrusted; bound session identity authorizes mutation.
- Invalid canonical IDs are rejected rather than rewritten into ambiguous aliases.
- Internal messages require matching projects and bound sender identity.
- Cross-project exchange uses its own approved capability-gated contract.
- Children inherit project identity and may only retain or reduce capabilities.
- Task/lease/artifact/state mutations are project-scoped and version/ownership protected.
- PRIMARY, MANAGER and RESEARCH packages are dependency-closed, exact-SHA traceable, component-hashed and reproducible.
- A child never infers expanded task scope from conversation context; scope changes return to Primary for authorization.

Run `python tests/run_all.py` for tests. Build with `python tools/build_agent_packages.py --source-revision <commit> --out dist`, validate with `python tools/verify_agent_packages.py`, independently rebuild to another directory, then compare with `python tools/check_reproducible_packages.py dist <other-dir>`.
