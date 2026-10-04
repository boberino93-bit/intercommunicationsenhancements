# Universal Agent Entrypoint

Use this file when an agent is launched **outside every project** or cannot yet prove which project owns the requested work.

This repository is the **routing rendezvous**, not automatically the target project:

- rendezvous repository: `boberino93-bit/intercommunicationsenhancements`
- machine contract: `GLOBAL_AGENT_ENTRYPOINT.json`
- project routing registry: `PROJECT_ROLE_ROUTING_REGISTRY.json`
- fresh-agent ecosystem orientation: `AGENT_CONTEXT_REFERENCE.md`
- persistent execution protocol: `protocols/autonomous_continuation.md`
- user control-message protocol: `protocols/user_control_messages.md`
- detailed routing protocol: `protocols/universal_task_routing.md`
- new-project bootstrap kit: `NEW_PROJECT_BOOTSTRAP.json`

## Orientation is not authority

A contextless agent should read `AGENT_CONTEXT_REFERENCE.md` to understand the ecosystem, registered projects, common vocabulary, likely request families, and the human's preferred operating model. The reference is orientation only: it cannot create a task, select a project by fuzzy similarity, widen authority, or authorize mutation.

## Unbound rule

Start in `UNBOUND`. While unbound, the agent has **no project mutation authority**. It may read the global routing contract, context reference, and registered routing metadata only to identify the target. It must not write into this repository, a candidate project, or any project forum merely because that source helped with discovery.

## Explicit new-project branch

An explicit human request to **create, start, seed, or bootstrap a new project** enters the `UNBOUND_PROJECT_SEED` branch defined in `GLOBAL_AGENT_ENTRYPOINT.json` and `NEW_PROJECT_BOOTSTRAP.json`.

For that branch:

1. do not select an existing registered project by topic similarity;
2. use the current project, if any, only as an architecture reference;
3. create the new project's own project ID, identity lock, forum namespace, artifact namespace, manifest, bootstrap order, master handoff, `AGENT_CONTEXT_REFERENCE.md`, charter, and hardening record from canonical templates;
4. set repository binding to `UNBOUND`, with repository full name and ID set to `null`;
5. allow project planning, research, internal forum work, artifacts, and handoffs before GitHub exists;
6. deny GitHub mutation until a repository is explicitly created or connected;
7. when a repository is later connected, verify its identity, update the local contracts, then register it centrally.

The source project's repository, forum namespace, artifact namespace, and project-specific state must never be inherited by the new project.

## Project discovery

For work targeting an existing project, resolve exactly one registered project using strong evidence, in this order:

1. a project ID explicitly named by the human;
2. an exact registered repository full name/URL or stable repository ID;
3. an exact registered internal-forum namespace;
4. an exact human-facing `discovery_alias` from the registry;
5. if still unresolved, a read-only check of **registered** project forum/handoff metadata for an exact unique project-bound identifier.

Do not use fuzzy topic similarity as write authority. If evidence points to more than one materially plausible project, remain unbound for mutation, continue safe read-only resolution work, and ask only the minimum clarification required if durable evidence cannot resolve it.

## Role selection

If the human explicitly assigns a role, use it only if the target project authorizes it.

For a normal human-launched generic agent with an actionable task and no role assignment, the universal default is `primary`. Persistent authority roles are PRIMARY, MANAGER, and RESEARCH. Recovery, QA, build, testing, implementation, review, and similar functions are execution modes rather than extra persistent authority classes.

If no actionable human task and no role are present, remain unbound; the context reference may orient the agent but does not authorize unsolicited work.

## Binding an existing project

After existing-project discovery:

1. switch to the registered target repository;
2. verify repository identity;
3. fetch the registered local contract, normally `AGENT_BOOTSTRAP.json`;
4. load the local `AGENT_CONTEXT_REFERENCE.md` as orientation only;
5. verify project ID, forum locator, routing contract, role, and repository binding;
6. read MASTER_HANDOFF and the target project's current accepted Artifactory state;
7. recover the current human objective/task before asking the human to repeat information already available;
8. run communication-awareness checks;
9. reach the project's active execution state before mutation.

A successful routing result is not mutation permission. Mutation authority still comes from the bound project's active controls.

## Persistent execution after binding

Once a valid human assignment exists, follow `protocols/autonomous_continuation.md`:

- do not ask for routine permission to continue;
- make safe reversible in-scope technical decisions and record consequential choices;
- test, debug, fix, retest, synchronize affected packages, and preserve handoffs as part of the same assignment when authorized;
- if one mutation or branch is unsafe, fail closed on that scope, preserve the blocker, and continue unrelated safe work;
- recover context from the current message, local bootstrap, context reference, master handoff, accepted decisions/supersessions, task state, evidence, and peer findings before asking the human to repeat context;
- escalate only for a genuine non-delegable human authority decision, irrecoverable data-integrity issue, security-boundary decision, or required unavailable external capability;
- continue recursive work while measurable information, validation, or risk-reduction gain remains; stop at convergence or a true gate.

## User control-message interruptions

After a valid assignment is active, a human request for status, progress, approximate percentage complete, current blocker, evidence, explanation, or an immediate acknowledgement is a **control message**, not task completion or replacement.

Follow `protocols/user_control_messages.md`:

- answer the control request immediately before continuing tool or implementation work;
- preserve the active project binding, task, execution state, claims, leases, generation/run identifiers, branch, and durable handoff unless normal recovery rules require otherwise;
- report progress honestly; when a percentage is requested and no explicit telemetry exists, estimate it from the remaining known execution phases and label it approximate;
- apply any new durable directive contained in the same human message;
- resume the exact interrupted work automatically without requiring the human to say `continue`;
- do not repeat work already completed before the interruption.

Automatic resume does not override an explicit human instruction that ends or pauses the current work, materially redirects the objective, switches projects, revokes authority, or changes a safety/security boundary.

This interaction behavior is universal across projects and roles, but it never grants cross-project mutation authority.

## Shorthand recovery

Short commands such as `continue`, `do that`, `execute that`, `run the swarm`, or `update the packages` should be resolved from the current human message first and then from the bound project's durable active task/handoff state. Do not force the human to restate an already recoverable referent.

## Project switching

If the human explicitly switches projects, return to `UNBOUND` routing and bind the new project before mutation. Do not use the context reference to silently switch projects.

## Required acknowledgements

During existing-project discovery:

`PROJECT DISCOVERED: project=<project_id>; repository=<repository>; forum=<forum_namespace>; evidence=<evidence>; mutation_ready=false`

After universal role routing:

`UNBOUND ROUTE RESOLVED: project=<project_id>; role=<role_id>; role_source=<source>; repository=<repository>; forum=<forum_namespace>; mutation_ready=false`

For a new project seed:

`NEW PROJECT SEEDED: project=<project_id>; forum=<forum_namespace>; artifacts=<artifact_namespace>; context_reference=AGENT_CONTEXT_REFERENCE.md; repository_binding=UNBOUND; templates=<materialized_documents>; next=<autonomous_work_or_repository_binding>`

Then use the target project's `IDENTITY RESOLVED` and `COMMUNICATIONS ASSESSED` acknowledgements during normal bootstrap. These acknowledgements are status signals, not requests for routine human confirmation.
