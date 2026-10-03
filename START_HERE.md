# Intercommunications Enhancements — Start Here

This repository is derived from the Organization Agent Mesh v1.0.0 seed package and is dedicated to hardening multi-agent communication for simultaneous unrelated projects.

## Current alpha

1. `project_id` is treated as an authorization boundary.
2. Internal messages require matching source/destination project identity.
3. Cross-project exchange uses a distinct explicit contract and is denied by default.
4. Lanes, presence, and agent instances are project-scoped.
5. PRIMARY, MANAGER, and RESEARCH packages carry project/protocol/framework versions and are validated against stale or foreign deployment.
6. Run `python tests/run_all.py` for the current hardening tests.
7. Build role packages with `python tools/build_agent_packages.py --source-revision <commit>` and validate with `python tools/verify_agent_packages.py`.

Read `PROJECT_CHARTER.md`, `ROADMAP.md`, and `protocols/project_isolation.md` before changing intercommunications behavior.
