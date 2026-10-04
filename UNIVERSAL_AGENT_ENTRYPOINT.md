# Universal Agent Entrypoint

Use this file when an agent is launched **outside every project** or cannot yet prove which project owns the requested work.

This repository is the **routing rendezvous**, not automatically the target project:

- rendezvous repository: `boberino93-bit/intercommunicationsenhancements`
- machine contract: `GLOBAL_AGENT_ENTRYPOINT.json`
- project routing registry: `PROJECT_ROLE_ROUTING_REGISTRY.json`
- detailed protocol: `protocols/universal_task_routing.md`

## Unbound rule

Start in `UNBOUND`. While unbound, the agent has **no project mutation authority**. It may read the global routing contract and registered routing metadata only to identify the target. It must not write into this repository, a candidate project, or any project forum merely because that source helped with discovery.

## Project discovery

Resolve exactly one registered project using strong evidence, in this order:

1. a project ID explicitly named by the human;
2. an exact registered repository full name/URL or stable repository ID;
3. an exact registered internal-forum namespace;
4. an exact human-facing `discovery_alias` from the registry, such as `duo screen`;
5. if still unresolved, a read-only check of **registered** project forum/handoff metadata for an exact unique task identifier, file/repository identifier, ticket/issue identifier, artifact identifier, or other project-bound key.

Do not use fuzzy topic similarity. “Foldable phone work,” “benefits work,” or “research project” is not enough by itself. If evidence points to more than one project, remain unbound and ask for the minimum clarification needed.

The read-only fallback is a routing bridge, not a cross-project data plane: inspect only the registered sources needed to identify ownership, never mutate them, and do not treat a mirror or snapshot as the live forum.

## Role selection

If the human explicitly assigns a role, use it only if the target project authorizes it.

For a normal human-launched generic agent with an actionable task and no role assignment, the declared universal default is `primary`. This is an explicit bootstrap policy so the generic agent can own end-to-end task intake; it is **not** topic-based role inference and does not itself grant write authority.

If no actionable human task and no role are present, remain unbound.

## Binding the project

After project discovery:

1. switch to the registered target repository;
2. verify the repository full name and stable repository ID when available;
3. fetch the target project's registered local contract, normally `AGENT_BOOTSTRAP.json`;
4. verify project ID, repository identity, forum locator, handoff paths, routing-contract version and authorized role;
5. enter the target project's normal bootstrap sequence;
6. run the communication-awareness assessment against what this execution can actually access;
7. read the target project's authoritative internal-artifactory forum and registered handoffs before relying on continuation state;
8. reach the project's `ACTIVE` execution state before mutation.

A successful routing result is not mutation permission. Mutation authority still comes from the bound project's own active-session controls.

## Execution

Once bound, work as though the agent had been launched inside that project from the beginning:

- follow the target project's Primary/Manager/Research workflow and task-intake rules;
- stay inside that project's repository, forum, artifact and task boundaries;
- use delegation normally when the project workflow calls for it;
- persist decisions, evidence and handoff state to the **target project**, never to a neighboring project's board;
- if the user switches projects, return to `UNBOUND` routing and bind again before continuing.

## Required acknowledgements

During discovery:

`PROJECT DISCOVERED: project=<project_id>; repository=<repository>; forum=<forum_namespace>; evidence=<evidence>; mutation_ready=false`

After universal role routing:

`UNBOUND ROUTE RESOLVED: project=<project_id>; role=<role_id>; role_source=<source>; repository=<repository>; forum=<forum_namespace>; mutation_ready=false`

Then use the target project's existing `IDENTITY RESOLVED` and `COMMUNICATIONS ASSESSED` acknowledgements during normal bootstrap.
