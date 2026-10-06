# Universal Agent Entrypoint

Use this file only when an agent is launched **outside every ChatGPT Project** or cannot prove a host project. If a host ChatGPT Project is available, do **not** start here: run `protocols/project_context_binding.md` first and hard-bind that project before task interpretation.

The universal repository is a routing rendezvous, not automatically the target project:

- machine contract: `GLOBAL_AGENT_ENTRYPOINT.json`
- routing registry: `PROJECT_ROLE_ROUTING_REGISTRY.json`
- project-bound binding policy: `governance/PROJECT_CONTEXT_BINDING_POLICY.json`
- project-bound binding registry: `governance/PROJECT_CONTEXT_BINDING_REGISTRY.json`
- detailed unbound routing protocol: `protocols/universal_task_routing.md`
- fresh-agent orientation: `AGENT_CONTEXT_REFERENCE.md`
- autonomous continuation: `protocols/autonomous_continuation.md`

## Unbound rule

An unbound agent has no project mutation authority. It may inspect registered routing metadata and registered read-only forum/handoff metadata only to resolve exactly one project. Topic similarity, recent chats, repository recency, or a neighboring project's handoff are never sufficient routing authority.

## Existing-project discovery

When no host project exists, resolve exactly one project from registered strong evidence such as an explicit project ID, exact registered repository identity/ID, exact registered internal-forum namespace, or exact registered discovery alias. If evidence conflicts, remain unbound for project execution.

After project discovery, load and verify the target local `AGENT_BOOTSTRAP.json`, local `AGENT_CONTEXT_REFERENCE.md`, identity lock, master handoff, and authoritative internal coordination route before task interpretation or execution.

## Role selection

If the human explicitly assigns a role, use it only if the target project authorizes it. Otherwise a normal human-launched generic agent enters **roleless demand-driven admission**. It does **not** default to PRIMARY, and PRIMARY may not be self-selected merely because a project was resolved.

Recovery, QA, build, implementation, testing, and review are execution modes/functions; they do not silently create a persistent authority role.

## Coordination and GitHub

Internal project AgentBus/Artifactory messaging is the canonical coordination surface. GitHub is downstream source/version control and backup. A valid append-only project-scoped coordination publication may occur through the narrow token-free coordination lane, but that exception never includes workflow runs or workflow changes, approvals/reviews, releases, deployments, branch creation, destructive operations, or cross-project writes.

## New projects

An explicit request to create/seed a new project enters `UNBOUND_PROJECT_SEED`. Create the new project's own identity, internal coordination namespace, artifact namespace, bootstrap/context material, and handoff before binding any GitHub repository. Never inherit another project's writable repository or AgentBus namespace.

## Project switching

A project switch is a rebind, not a silent routing update. Discard the old project-specific role/claim context, resolve and verify the new project, then run its bootstrap from the beginning.

## Authority

Project discovery and project binding establish scope only. They do not grant protected mutation authority, approval authority, release/deployment authority, workflow authority, security/credential authority, or cross-project write authority.
