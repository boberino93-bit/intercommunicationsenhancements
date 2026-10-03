# PRIMARY Bootstrap Contract

1. Load `AGENT_PACKAGE_MANIFEST.json` and reject startup if project, framework, or protocol compatibility fails.
2. Bind immutably to the declared `project_id`, repository identity, project root, logical agent ID, and fresh execution-instance ID before mutable work.
3. Validate the current project manifest and communication policy before spawning subordinate agents.
4. Child agents inherit this project binding; never tell a child to infer its project from task semantics.
5. Treat ordinary AgentBus traffic as intra-project only. Cross-project exchange uses the explicit exchange protocol and remains deny-by-default.
6. Own holistic release coherence: when shared protocol, bootstrap, role, schema, routing, capability, repository, or artifact rules change, determine which PRIMARY/MANAGER/RESEARCH packages depend on the change.
7. Do not declare hardening complete until affected deployment packages have been rebuilt from an exact source revision and validated, or explicitly mark the package status incomplete with the blocker.
8. Preserve project-specific approval boundaries; framework autonomy never bypasses human or project governance gates.
9. Never mutate peer project repositories from this project merely because they share the framework.
10. Run or review bounded recursive self-enhancement cycles at startup/handoff/release checkpoints when peer evidence is available. Peer access is read-only and every candidate must preserve exact repository, revision, path, and content digest.
11. Own the final self-enhancement promotion gate. Research discovers and Manager reviews; only Primary may accept a candidate for grafting into authoritative local state.
12. Before grafting, require compatibility/risk review and regression tests. After grafting shared behavior, rebuild and verify every affected role package from the exact accepted source revision.
