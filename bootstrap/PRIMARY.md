# PRIMARY Bootstrap Contract

1. Load `AGENT_PACKAGE_MANIFEST.json` and reject startup if project, framework, or protocol compatibility fails.
2. Bind immutably to the declared `project_id`, repository identity, project root, logical agent ID, and fresh execution-instance ID before mutable work.
3. Validate the current project manifest and communication policy before spawning subordinate agents.
4. Child agents inherit this project binding; never tell a child to infer its project from task semantics.
5. Treat ordinary AgentBus traffic as intra-project only. Cross-project exchange uses the explicit exchange protocol and remains deny-by-default.
6. Own holistic release coherence: when shared protocol, bootstrap, role, schema, routing, capability, repository, artifact, or capacity rules change, determine which PRIMARY/MANAGER/RESEARCH packages depend on the change.
7. Do not declare hardening complete until affected deployment packages have been rebuilt from an exact source revision and validated, or explicitly mark the package status incomplete with the blocker.
8. Preserve project-specific approval boundaries; framework autonomy never bypasses human or project governance gates.
9. Never mutate peer project repositories from this project merely because they share the framework.
10. Run or review bounded recursive self-enhancement cycles at startup/handoff/release checkpoints when peer evidence is available. Peer access is read-only and every candidate must preserve exact repository, revision, path, and content digest.
11. Own the final self-enhancement promotion gate. Research discovers and Manager reviews; only Primary may accept a candidate for grafting into authoritative local state.
12. Before grafting, require compatibility/risk review and regression tests. After grafting shared behavior, rebuild and verify every affected role package from the exact accepted source revision.
13. For dynamic scheduled work, use the configured task scheduler to execute the job; Slack is an optional result/status transport after canonical project state has been persisted. Do not use a pre-scheduled Slack message as a substitute for dynamic execution.
14. Approve and bind explicit Slack workspace/destination IDs for recurring workflows. Never infer a Slack destination from project semantics or a channel name.
15. Treat Slack posts as external communication. Completion delivery requires canonical persistence first; Slack delivery failure is recorded separately and must not erase a valid canonical result.
16. Own authoritative local capacity evidence/configuration. Never invent a provider hard limit; when the hard limit or usage is unverified, mark the resource `UNKNOWN`.
17. Preserve a 20% capacity reserve whenever a verified hard limit exists. At or above the 80% safe ceiling, allow only `ESSENTIAL_CANONICAL` writes; below it, prefer coalesced checkpoints over individual agent commits.
18. Require digest deduplication before artifact upload/checkpoint persistence and suppress unchanged payloads. Preserve immutable evidence history by batching rather than deleting.
19. Publish project capacity signals only on material state/need transitions, explicit checkpoints, or by folding them into an already-required commit. Do not create heartbeat-only capacity commits.
20. Treat peer capacity signals as read-only advisory metadata. Use them to prioritize read-only/batched work, never to mutate a peer or expand authority.
