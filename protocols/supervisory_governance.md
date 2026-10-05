# SUPERVISORY GOVERNANCE OVERLAY

Status: **CANONICAL ACTIVE OVERLAY**

This protocol adds lifecycle supervision, intentional-stop persistence, human-gated scheduled-task activation, and ChatGPT Project placement semantics to the existing Org Agent Mesh. It is additive. It does not replace project isolation, capability gates, consequence authorization, lease/fencing rules, the frozen normalized runtime baseline, or stronger safety controls.

## 1. Authority

Lifecycle supervision order is:

`USER > MASTER > PRIMARY > SUBORDINATE`

The User is the highest authority. The MASTER has global lifecycle supervision across registered project trees. A PRIMARY may supervise only its own project tree unless a stronger authorized control path explicitly delegates otherwise.

Global lifecycle supervision does **not** grant unrestricted cross-project source mutation. Repository writes, production actions, destructive operations, credentials, releases, and other consequential effects remain governed by existing project/capability/consequence controls.

Scheduled-task activation is a separate gate from lifecycle supervision. No autonomous role inherits task-enablement authority from MASTER/PRIMARY lifecycle authority.

## 2. Master is global and roaming

The MASTER must remain unbound from ChatGPT sidebar Projects:

- `roaming = true`
- `project_id = null`
- `chat_project = null`
- lifecycle authority = global

A scheduled trigger caused by a project must not attach the MASTER conversation to that project.

## 3. Project chat placement

Non-roaming project agents use the canonical mapping in `governance/SWARM_SUPERVISION_POLICY.json` through `org_agent_mesh.chat_project_routing.ChatProjectRouter`.

Rules:
1. prefer direct conversation creation inside the expected ChatGPT Project;
2. if direct creation is unavailable, create globally and move through the host adapter;
3. verify `expected_project == detected_project` after the external action;
4. retry movement only a bounded number of times;
5. if mapping is unknown, do not guess and leave an existing conversation unchanged;
6. if the actual host has no supported API, a browser/UI adapter may implement the contract using stable identifiers/accessible selectors;
7. code-path success without host-side verification is not external-placement success.

## 4. Machine-readable runtime states

Agents participating in supervised execution use these lifecycle states:

`STARTING`, `RUNNING`, `REDIRECT_REQUESTED`, `PAUSE_REQUESTED`, `PAUSED`, `STOP_REQUESTED`, `STOPPING`, `STOPPED`, `COMPLETED`, `FAILED`.

Natural-language messages may accompany control actions, but they are not the authoritative control state.

## 5. Supervisory actions

Supervisors may use:

`CONTINUE`, `REDIRECT`, `PAUSE`, `STOP`, `STOP_TREE`.

Use the least disruptive effective intervention. The governing question is whether continued execution is currently expected to materially advance the governing objective.

Valid reasons include goal misalignment, instruction drift, scope creep, redundancy, low expected information gain, circular work, invalid assumptions, superseded work, poor methodology, weak evidence, project-goal conflict, architecture conflict, unexpected risk, destructive behavior, resource imbalance, blocked execution, agent conflict, premature implementation, premature research, quality degradation, changed project state, user direction, Master direction, or another defensible governance reason.

## 6. Stop semantics

`STOP EXECUTION != DELETE WORK`

When practical, preserve research, citations, source references, analysis, code/patches, test output, logs, failure information, hypotheses, unanswered questions, intermediate artifacts, and next steps.

`STOP_TREE` applies the stop request to the target and all registered descendants. A parent under stop may not begin another child execution.

Control operations are idempotent in effect: repeating STOP against already-stopped work must not restart it or convert it back to runnable state.

## 7. Bounded work units

Long-running agents must check control state between bounded units of work. An already-running atomic operation may finish only when interruption would risk corruption/inconsistency; the agent must then honor the authoritative state before beginning another unit.

`org_agent_mesh.supervision.CooperativeAgentRuntime` provides the reference behavior.

## 8. Redirect and pause

REDIRECT persists the current partial state, increments assignment revision, applies the new direction, and resumes only under the revised assignment.

PAUSE persists current partial state and enters a machine-readable paused state. Resume requires a valid control transition; the schedule firing by itself is not a resume instruction.

## 9. Intentional-stop persistence and respawn protection

An intentional STOP or STOP_TREE sets `allow_respawn = false` for the affected execution. Schedulers, timers, liveness recovery, and unfinished-task scans must treat that state as intentional termination rather than missing work.

A new logical execution may be authorized by:

- explicit User instruction; or
- MASTER/authorized PRIMARY with a materially newer task revision.

A clock firing, an incomplete status, or a stale prompt is insufficient authority to revive the old execution.

Logical restart authority does **not** imply authority to enable a disabled recurring scheduled task. Those are separate gates.

## 10. Scheduled-task activation gate

Scheduled swarm tasks may be **enabled only by an explicit current human request**.

This is a hard control-plane invariant, not a preference or optimization. The following actors may never turn a disabled swarm task on autonomously:

- MASTER;
- PRIMARY;
- Manager;
- Researcher;
- recovery/reconciliation logic;
- migration/alignment logic;
- bootstrap/startup logic;
- liveness or stale-task recovery;
- another scheduled task;
- generic system automation.

Rules:

1. disabled scheduled tasks are a deliberate human control gate, not a health failure;
2. a disabled task must not be treated as stale, crashed, incomplete, or needing automatic recovery;
3. no startup, migration, alignment, protocol-upgrade, project-activation, or swarm-recovery path may enable it;
4. updates to prompts, cadence metadata, routing metadata, governance revisions, or task titles must preserve the current enabled/disabled state unless the human explicitly requested that state change in the current instruction;
5. automatic re-enable after STOP, PAUSE, failure, restart, migration, or a new task revision is forbidden;
6. Master/Primary lifecycle restart authority applies only after a scheduled invocation is already legitimately available; it cannot cross the disabled-task gate;
7. disabling a task may be used as a containment/safety action by an authorized control path, but re-enabling still requires explicit human action;
8. agent code must not call task-enable/resume operations on its own behalf;
9. any attempted autonomous `disabled -> enabled` transition must fail closed and be auditable;
10. the reference enforcement helper is `org_agent_mesh.schedule_activation`.

The human enable action is intentionally manual because enabling multiple recurring agents can open concurrent mutation lanes and create code conflicts. Keeping enablement outside autonomous swarm authority preserves the human-controlled gate over when concurrency is allowed to begin.

## 11. Scheduled launches

Every scheduled/cold-start swarm launch that has already been human-enabled must:

1. load current supervisory governance alongside the existing recurring/successor protocols;
2. validate exact project/role launch context against the local contract;
3. load current control/intentional-stop state before starting or replacing work;
4. preserve occurrence identity across provider retry;
5. refuse blind respawn of deliberately stopped work;
6. keep scheduled MASTER invocations global/roaming;
7. route scheduled project agents through the project-placement mechanism when a host adapter is available;
8. preserve User > MASTER > PRIMARY authority;
9. treat the schedule as a wake-up trigger, never an independent authority system;
10. never modify its own or another task's enabled state.

## 12. Alignment monitoring

PRIMARY and MASTER supervisors should combine current user objective, project instructions, architecture, completed sibling work, evidence quality, remaining uncertainty, progress, duplication probability, resource cost, risk, and blockers. Do not reduce governance to a single arbitrary score threshold.

PRIMARY optimizes for project success, not subordinate activity. MASTER optimizes for the user's portfolio objectives, not utilization or keeping every branch alive.

Schedule alignment is configuration alignment only. It may update prompts or governance references while preserving disabled/enabled state; it is never permission to activate the swarm.

## 13. Audit records

Autonomous lifecycle interventions should record at least supervisor, target, project where applicable, action, reason code, concise explanation, state-preservation result, respawn disposition, and timestamp. Scheduled-task state-change attempts should also record actor, prior state, requested state, whether explicit human authorization was present, and disposition. Never record authentication tokens, session secrets, passwords, cookies, credentials, or private authentication material.

## 14. Compatibility

This overlay intentionally reuses existing project identity, lease/fence, scheduling, consequence, recovery, handoff, and audit infrastructure. If this overlay conflicts with a stronger current safety/security/consequence rule, the stronger rule wins and the conflict must be surfaced rather than guessed away.
