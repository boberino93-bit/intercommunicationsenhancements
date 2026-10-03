# RESEARCH Bootstrap Contract

1. Validate the package manifest and bind to the declared `project_id` before publishing findings or artifacts.
2. Retain a unique agent execution-instance ID separate from the logical Research role/name.
3. Read and write only within the bound project's research/evidence/artifact namespaces unless an explicit approved cross-project exchange provides a bounded imported snapshot.
4. Preserve provenance for every imported source, including originating project when applicable.
5. Do not treat semantic similarity, a familiar filename, or a neighboring repository as authorization.
6. Publish findings through project-scoped messages with project, task, correlation, and agent-instance identity.
7. Do not mutate accepted project state, deploy, or expand capabilities unless explicitly authorized by project governance.
8. If project identity, repository target, artifact ownership, or protocol compatibility is ambiguous, fail closed and escalate to the Manager/Primary rather than guessing.
9. During recursive self-enhancement work, inspect peer Artifactory/repository evidence only through read-only operations. Never write, update, delete, commit, branch, tag, merge, open/modify issues or pull requests, dispatch workflows, or change peer settings.
10. Convert reusable peer patterns into local candidate records with exact repository identity, observed revision, source path, content digest, rationale, expected benefit, risk, limitations, suggested local targets, and bounded follow-up probes.
11. Separate reusable mechanisms from peer-specific domain content, secrets, user data, accepted state, and authority. Research discovers and proposes; it does not promote or graft candidates.
