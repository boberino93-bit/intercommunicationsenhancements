# Project + Role Discovery Protocol

This protocol is the **project-bound** discovery gate. It normally runs after the target project's identity lock and before any role-specific work or repository mutation.

## Unbound-agent bridge

If the agent was launched outside every project, or cannot yet prove which project owns the task, do **not** guess a local project and do not start this protocol against a candidate repository.

Instead:

1. remain `UNBOUND` with mutation denied;
2. load `UNIVERSAL_AGENT_ENTRYPOINT.md` and `GLOBAL_AGENT_ENTRYPOINT.json` from `boberino93-bit/intercommunicationsenhancements`;
3. resolve exactly one project under `protocols/universal_task_routing.md`;
4. verify that project's registered repository and local bootstrap contract;
5. only then enter this project-bound protocol in the target project.

The universal layer may use a narrow read-only scan of registered forum/handoff metadata to find an exact unique project identifier. It may not use fuzzy topic similarity or mutate candidate projects during discovery.

## Inputs

- `project_id`: derived from the verified project environment or explicitly named/resolved from registered strong evidence.
- `role_id`: explicitly assigned by the human/deployment package, or resolved through the declared roleless-admission policy for a generic human launch.
- current repository full name and, when available, the provider's stable repository ID.

All identity inputs are evidence, not authority by themselves. Neither project nor repository may be guessed from topic similarity.

## Resolution

1. Validate `PROJECT_IDENTITY_LOCK.json` first when the target project defines one.
2. Load and validate `PROJECT_ROLE_ROUTING_REGISTRY.json` in `FAIL_CLOSED` mode.
3. Resolve the exact `project_id` entry and verify `role_id` is authorized.
4. Verify the current repository full name matches the registered repository.
5. When a stable repository ID is available, verify it matches the registered `repository_id` as an additional anti-spoof/rename check.
6. If the target repository contains the registered local contract (normally `AGENT_BOOTSTRAP.json`), verify its project ID, repository identity, forum locator, handoff paths and routing-contract version agree with the registry. A disagreement fails closed.
7. Resolve the authoritative project forum from `forum_locator.authority` + `forum_locator.namespace`.
8. Treat `forum_locator.repository_view` only as declared. `LIVE_MIRROR` may be consulted as a local view; `SNAPSHOT_BACKUP` is recovery/history evidence and must not be mistaken for current forum state; `CANONICAL` may be authoritative only when the registry explicitly says the repository itself is the forum authority; `NONE` means no repository forum view is registered.
9. Read the registered repository-side handoff/state locations separately from the forum locator.
10. Run `protocols/communication_awareness.md` against capabilities and evidence actually visible to this execution. Classify access as `DIRECT`, `LIVE_MIRROR`, `STALE_MIRROR`, `SNAPSHOT_ONLY`, `HANDOFF_ONLY`, `NONE`, or `CONFLICT`.
11. Default visibility claims to partial. A mirror, snapshot, handoff, current chat, open repository, or prior memory can never by itself justify saying the agent sees all project communications.
12. If direct forum access resolves to a namespace other than the registered project namespace, classify `CONFLICT` and stop before mutation.
13. Emit the communication acknowledgement:

   `COMMUNICATIONS ASSESSED: project=<project_id>; role=<role_id>; forum=<forum_namespace>; access=<access_mode>; coverage=<coverage>; confidence=<confidence>; full_forum_visibility=<true|false>; mutation_blocked=<true|false>`

14. Bind only the registered repository/repositories as authorized mutation targets.
15. Emit the startup acknowledgement:

   `IDENTITY RESOLVED: project=<project_id>; role=<role_id>; forum=<forum_namespace>; repositories=<authorized_repositories>; state=<handoff_or_state_ref>`

16. Only after the acknowledgements may role-specific startup continue.

## Bootstrap service discovery

After identity and project routing are resolved, load the canonical bootstrap control-plane service binding `bootstrap/INTERNAL_SCHEDULER_SERVICE.json` from `boberino93-bit/intercommunicationsenhancements` and validate its referenced protocol, policy, runtime, host-clock path, and scheduling semantics before relying on it.

Then load `governance/INTERNAL_SPAWN_PROJECT_BINDINGS.json` from the canonical repository and require an exact entry matching the already-resolved project ID, repository full name, and stable repository ID. For registered projects whose entry requires a local scheduler binding, load the target repository's `bootstrap/INTERNAL_SCHEDULER_SERVICE.json` and `INTERNAL_SCHEDULER_SERVICE_BINDING.json`. The local binding must match the same project/repository identity and may narrow but never broaden the canonical service authority.

The internal scheduler service is infrastructure, not an agent role and not mutation authority. Its checked-in binding may authorize bounded scheduled spawn-ticket creation only to the extent explicitly delegated by `governance/INTERNAL_SPAWN_SCHEDULER_POLICY.json`. A spawn ticket is never proof that a session exists. Require the host start receipt defined by `protocols/internal_scheduler_service.md` before treating a scheduled launch as started.

For scheduler-launched work, permitted worker roles are limited to the intersection of the canonical scheduler policy, the project routing registry, and the local scheduler binding. PRIMARY and MASTER spawning and autonomous full-swarm start remain prohibited. Ordinary project role availability does not imply scheduler-spawn availability.

Do not let scheduler-service discovery alter existing ChatGPT Scheduled Task enablement. Existing disabled tasks remain human control gates. Scheduler/spawn authority does not convey project mutation authority, claim ownership, lease ownership, fence authority, credential access, production acceptance authority, or permission to override project HOLD/PAUSE/STOP state.

If the project binding is missing, mismatched, broader than canonical policy, or otherwise unverifiable, classify scheduler spawning for that project as `SCHEDULER_PROJECT_BINDING_BLOCKED`; continue unrelated safe project discovery/work under ordinary authority rather than treating the whole project as failed.

## Answering communication-visibility questions

When the human asks whether the agent sees the communications happening around it, do not answer from intuition. Re-run the communication-awareness assessment and state:

- the project and authoritative forum resolved;
- the strongest communication source actually visible now;
- whether it is direct, mirrored, stale, snapshot-only, handoff-only, or absent;
- whether full registered-forum scope has actually been proven;
- what remains unseen or unverifiable;
- whether any identity/namespace conflict blocks safe mutation.

A truthful answer such as “I can see the registered snapshot and handoff, but I do not have verified live access to the internal forum” is preferred over an ungrounded yes/no.

## Registry integrity checks

The registry itself is invalid if it contains duplicate repository bindings, duplicate stable repository IDs, duplicate forum or artifact namespaces, unsafe relative paths, malformed role sets, invalid forum authority, a forum namespace mismatch, an invalid repository-view mode/path pair, colliding discovery aliases, or discovery aliases that impersonate another project's canonical routing identifiers. Invalid registry state must stop startup before mutation.

## Fail-closed conditions

Stop before mutation if any of the following is true:

- project is unknown;
- project discovery is ambiguous or supported only by topic similarity;
- role is unknown or unauthorized;
- project and repository identity disagree;
- stable repository ID disagrees when available;
- central registry and local bootstrap contract disagree;
- forum authority or namespace cannot be resolved;
- direct forum namespace conflicts with the resolved project;
- a repository snapshot is presented as though it were the live forum;
- handoff/state source cannot be resolved;
- two projects appear equally plausible;
- a repository is requested that is not registered for the resolved project.

Do not rewrite, normalize, or guess canonical identifiers to make them fit. Human-facing registered discovery aliases may use case/whitespace normalization only for exact alias matching. Do not invent a repository forum path when the forum is external to GitHub.

## Cross-project framework rollout

A framework rollout may update peer projects only when all of these are true:

- the human explicitly authorizes a cross-project rollout;
- each target exists in the routing registry;
- the change is framework/bootstrap-only, not domain logic;
- the target receives only project-local routing/bootstrap metadata;
- mutation is limited to the resolved target repository;
- each target is validated after deployment.

Ordinary project work remains cross-project deny-by-default. Universal discovery adds only a narrow read-only routing bridge; it does not create a cross-project mutation channel.
