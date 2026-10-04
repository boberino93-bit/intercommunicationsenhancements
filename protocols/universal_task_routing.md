# Universal Task Routing Protocol

## Purpose

This protocol closes the gap between a generic, project-agnostic agent and the existing project-bound bootstrap. It lets a human launch one agent outside any project, give it a task, and have it discover the owning project before entering that project's normal workflow.

The protocol does **not** create shared mutable state or a central controller. The universal layer is a read-only rendezvous and routing stage. Project autonomy and fail-closed mutation rules remain unchanged.

## State machine

`UNBOUND -> PROJECT_DISCOVERED -> PROJECT_CONTRACT_VERIFIED -> PROJECT_BOOTSTRAP -> ACTIVE`

- `UNBOUND`: no project mutation authority. Global routing metadata may be read.
- `PROJECT_DISCOVERED`: exactly one registered project is supported by strong evidence, but mutation is still denied.
- `PROJECT_CONTRACT_VERIFIED`: repository identity and the target local bootstrap contract agree with the central registry.
- `PROJECT_BOOTSTRAP`: the target project's own identity, communication-awareness, handoff and execution-session gates are running.
- `ACTIVE`: the target project has granted normal project-scoped execution authority.

Any conflict returns the flow to `UNBOUND` or stops it before mutation.

## Global rendezvous

The stable rendezvous is:

- repository: `boberino93-bit/intercommunicationsenhancements`
- human entrypoint: `UNIVERSAL_AGENT_ENTRYPOINT.md`
- machine entrypoint: `GLOBAL_AGENT_ENTRYPOINT.json`
- registry: `PROJECT_ROLE_ROUTING_REGISTRY.json`

The rendezvous repository is not automatically the target project.

## Strong project evidence

Project discovery may use only registered strong evidence:

1. explicit `project_id` from the human;
2. exact registered repository full name or URL containing that full name;
3. exact stable repository ID;
4. exact registered internal-artifactory forum namespace;
5. exact registered `discovery_alias`;
6. an exact unique project-bound identifier observed during the read-only fallback scan.

Human-facing aliases may be case/whitespace normalized only for matching the alias table. Canonical project IDs, repository identities, stable repository IDs, forum namespaces and artifact namespaces are not rewritten to make them fit.

Topic similarity, semantic resemblance, repository-name guessing and “this sounds like project X” are prohibited as mutation-routing evidence.

## Read-only communication bridge

If the initial request does not contain enough strong evidence, the unbound agent may inspect **registered routing sources only** across candidate projects to find an exact unique ownership key.

Allowed fallback sources:

- the registered authoritative forum, when the runtime actually has direct read access;
- the registered repository mirror or snapshot, with its live/snapshot status preserved;
- registered handoff/state locations;
- repository metadata and exact file/repository identifiers.

The fallback scan is `READ_ONLY_REGISTERED_METADATA`. It exists only to determine project ownership.

The agent must not:

- write to any candidate project;
- claim snapshot data is live forum state;
- search arbitrary unregistered repositories/boards for a likely match;
- choose a project from general subject matter;
- use cross-project observations as execution authority.

If the same identifier appears in multiple projects, or no unique ownership key is found, project identity remains unresolved.

## Role routing

Role selection happens only after project discovery.

- Explicit human role -> use it if the target registry entry authorizes it.
- Actionable human task with no role -> use the declared universal default `primary`.
- No actionable human task and no role -> remain unbound.

The default `primary` role exists so a generic human-launched agent can perform project-local task intake, coordinate specialists and own end-to-end completion. It is a declared bootstrap rule, not semantic role inference. The target project's role authorization and active-session controls still apply.

## Contract verification

Before entering project bootstrap:

1. verify the target repository against the registry;
2. verify stable repository ID when available;
3. load the target `local_contract_path`;
4. validate local contract schema/mode;
5. verify project ID, repository, repository ID, forum authority/namespace/repository view, artifact namespace, handoff paths, role list and routing-contract version;
6. resolve the target route with `org_agent_mesh.project_role_routing`.

Any disagreement is a hard stop.

## Communication awareness and continuation state

After contract verification, run the normal target-project communication-awareness protocol. The universal layer never upgrades a mirror or snapshot into authoritative live communication.

Before relying on prior work, inspect the target project's registered forum/handoff sources and classify current visibility truthfully. Then follow the target project's normal continuation, task-intake, delegation and recovery protocols.

## Project switching

A bound agent may not silently carry authority into another project. When the human changes the target project:

1. finish or persist the current project's handoff;
2. discard project-specific mutation authority;
3. return to `UNBOUND`;
4. resolve and verify the new project independently;
5. enter that project's bootstrap from the beginning.

## Required failure behavior

Stop before mutation when:

- no project is supported by strong evidence;
- multiple projects are supported by conflicting evidence;
- a discovery alias collides with another registered routing identifier;
- the target role is unauthorized;
- repository or stable repository identity conflicts;
- the local contract and central registry disagree;
- the authoritative forum namespace conflicts with the discovered project;
- the current execution cannot complete the target project's normal active-session bootstrap.

This protocol is intentionally asymmetric: cross-project **read-only routing discovery** is allowed in a narrow form; cross-project mutation remains denied.
