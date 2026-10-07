# Project Context Binding Protocol

Status: **ACTIVE HARD GATE**  
Version: **1.4.0**

## Purpose

A worker launched inside a ChatGPT Project must inherit that project as a hard launch boundary before it interprets the task. Project placement is not a hint and must not be reconstructed from recent chats, task topic, repository recency, or another project's handoff.

Canonical machine policy: `governance/PROJECT_CONTEXT_BINDING_POLICY.json`  
Canonical binding registry: `governance/PROJECT_CONTEXT_BINDING_REGISTRY.json`  
Reference runtime: `org_agent_mesh.project_context_binding`

## Project-bound startup order

When host project context is available, execute this order before task interpretation:

1. resolve the exact host ChatGPT Project to one registered `project_id`;
2. bind repository, internal message-board namespace, artifact namespace, and local contract from the binding registry;
3. load the project's local `AGENT_BOOTSTRAP.json`;
4. load the project's local `AGENT_CONTEXT_REFERENCE.md`;
5. validate the project identity lock when present;
6. load the current master handoff and authoritative internal coordination route;
7. load and assess `protocols/speaker_continuity_assurance.md` and `governance/SPEAKER_CONTINUITY_ASSURANCE_POLICY.json` without inferring identity from account, device, history, familiarity, or style;
8. load and satisfy `protocols/human_machine_alignment.md`, `governance/HUMAN_MACHINE_ALIGNMENT_POLICY.json`, `protocols/deferred_human_gate.md`, and `governance/DEFERRED_HUMAN_GATE_POLICY.json`;
9. only after those checks pass, interpret the task and enter role admission.

The required acknowledgement is:

`PROJECT CONTEXT BOUND: project=<project_id>; chat_project=<host project>; repository=<repository>; forum=<internal namespace>; task_interpretation_allowed=true; mutation_authority=false`

## Speaker continuity barrier

Project binding establishes where the agent is operating; it does not establish who is currently holding the human-facing session. Conversation continuity, account continuity, device continuity, writing-style similarity, remembered personal history, and familiarity are not identity proof.

At bootstrap, resume, recovery, after material gaps or discontinuities, before sensitive historical disclosure, and before authorization evaluation, assess speaker-continuity assurance under `protocols/speaker_continuity_assurance.md`. A gap may lower assurance but is never proof that another person took over; absence of a gap is never proof that no handoff occurred.

When continuity is insufficient for an identity-dependent disclosure or protected action, fail closed only on that branch and continue safe identity-independent work. Re-establishment must use the consequence-proportional method defined by the continuity and authority-authentication policies. Human–machine alignment cannot override this barrier.

## Human–machine alignment barrier

Project binding establishes **where** the agent is operating. Human–machine alignment establishes **what the human is trying to accomplish** before the agent optimizes how to do it.

After binding and authoritative context recovery, but before task classification, delegation, optimization, or substantive execution, every project-bound agent must satisfy the Human–Machine Alignment Protocol.

Within valid platform, safety, authority, and security constraints, human–machine alignment is the project's first semantic optimization target. The agent must preserve an accurate shared understanding of the human objective, requested end state, material constraints, success conditions, uncertainty, disagreement, and current correction state.

A clear instruction proceeds without ritual confirmation. Material unresolved ambiguity triggers the minimum necessary clarification. A material human correction invalidates conflicting local assumptions and requires re-alignment of the affected branch.

A brief natural acknowledgement or other proportional pleasantry SHOULD be used when user-facing interaction benefits from demonstrating that the human has been understood. Courtesy is an alignment signal, not a reason for verbosity, canned greetings, or sycophancy.

Alignment does not create mutation authority and does not override stronger safety, project-isolation, evidence, security, or authorization gates.

When a required human action can safely wait, the alignment barrier also activates deferred-human-gate scheduling: the affected branch is frozen, useful independent work continues, adjacent unknowns are resolved, compatible non-urgent decisions may be batched, and the human is asked only when the next useful dependent action truly requires them.

## Child/worker launch envelope

Parents, dispatchers, and scalers that create project-bound workers SHOULD render the canonical machine block with `render_project_launch_context(...)` and include it in the worker instruction:

`ORG_AGENT_MESH_PROJECT_CONTEXT_BINDING`

`<canonical JSON + context_fingerprint>`

`END_ORG_AGENT_MESH_PROJECT_CONTEXT_BINDING`

The child parses that block with `parse_project_launch_context(...)` before task interpretation and revalidates it against the binding registry. A changed repository, forum, project, artifact namespace, or context path invalidates the fingerprint or registry comparison and fails closed. The fingerprint is an integrity checksum, not mutation authorization.

## Precedence

For a project-bound worker, the verified host project context or verified launch envelope wins over task-topic similarity, conversation history, recently accessed repositories, stale handoffs, and neighboring project state. Those sources may provide read-only evidence after binding but may not silently rebind the worker.

An explicit structured project switch that conflicts with the host project is not executed in place. Fail closed on project-specific work and perform a deliberate rebind/new launch.

## Role admission

Project binding does not imply PRIMARY. A generic human-launched worker with no explicit authorized role enters roleless demand-driven admission. PRIMARY is never the default merely because the worker is project-bound.

## Coordination and GitHub

Internal project AgentBus/Artifactory messaging is the canonical coordination surface. Routine project-bound append-only agent messages do not require a separate security token when they satisfy the coordination publication contract.

GitHub is downstream source/version control and backup. The token-free coordination backup lane is limited to append/create-new backup message files in the allowlisted project path. It never includes workflow execution or modification, approvals/reviews, releases, deployments, branch creation, destructive operations, or cross-project writes.

XRP uses `/XRPTHESIS-AgentBus/messages` as the canonical internal message namespace. `boberino93-bit/XRPTHESIS` is downstream source/backup, not the live coordination authority.

## Failure behavior

If host project resolution, repository identity, launch-envelope integrity, local bootstrap, context reference, identity lock, handoff, coordination route, or required human–machine alignment state is missing or conflicting, do not interpret the affected project task as executable work and do not mutate. Preserve the blocker and continue only safe diagnostic work or unaffected work permitted by the Human–Machine Alignment Protocol.
