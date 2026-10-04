# Task Intake, New-Project Routing and Delegation Protocol

Status: **STABLE FRAMEWORK GUIDANCE**

This protocol tells a bound Organization Agent Mesh agent where new work belongs and how to convert a broad request into safe, recoverable project work without contaminating unrelated projects or treating research recommendations as authority.

## 1. Route before mutation

After identity bootstrap and accepted-state loading, classify the request before any project mutation.

Allowed intake modes:

- `EXISTING_PROJECT_TASK` — the request belongs to the currently validated project.
- `NEW_PROJECT_BOOTSTRAP` — the request creates a distinct project/failure domain.
- `CROSS_PROJECT_EXCHANGE` — bounded information must cross project boundaries through the approved exchange protocol.
- `FRAMEWORK_MAINTENANCE` — the request changes the reusable Organization Agent Mesh framework itself.
- `AMBIGUOUS_PROJECT` — the target project cannot be safely determined.

`AMBIGUOUS_PROJECT` fails closed for mutation. A caller-supplied project name or repository is intent evidence, not authorization. When the human has explicitly named the target project or explicitly requested creation of a new project, do not ask them to repeat that information; validate it against local identity/state instead.

## 2. New-project isolation rule

A framework repository, template repository or source project is not the new project's state store.

For `NEW_PROJECT_BOOTSTRAP`, establish a separate project identity and project-scoped coordination/recovery environment before project-specific mutation. Project-specific manifests, forums, queues, handoffs, research findings, accepted state, evidence and artifacts must not be written into the framework project or another unrelated project's state.

The new project must have, at minimum, durable records for:

1. project identity and repository/workspace binding;
2. Primary execution/recovery identity;
3. message-board/forum or equivalent coordination root;
4. handoff/queue/evidence roots or equivalent project-scoped state;
5. initial task intake;
6. source-of-truth hierarchy;
7. workstream decomposition;
8. initial research-assistance/topology decision.

If the runtime cannot establish the required isolated coordination state, initialization is incomplete and risky project mutation remains blocked.

## 3. Problem definition before solution selection

Primary must begin from the problem and architecture, not from an assumed modification or implementation approach.

The initial intake records:

- objective and problem statement;
- known constraints and explicit non-goals;
- ranked source-of-truth hierarchy;
- unknowns and contested assumptions;
- actual technical/operational domains;
- dependencies between domains;
- consequence of incorrect findings;
- safety, rollback and recovery boundaries;
- conditions that block risky implementation.

A source-of-truth hierarchy should prefer direct/authoritative evidence over summaries or agent inference. External material begins untrusted or provisional until verified under the project's evidence policy.

## 4. Workstream decomposition

Decompose by independently executable fronts, not by arbitrary question count.

Each workstream should declare:

- workstream ID and objective;
- dependencies/prerequisites;
- source-of-truth references;
- allowed write scope;
- expected evidence/output;
- completion condition;
- known overlap with other workstreams.

High dependency density reduces useful parallelism. Sequential dependencies should not be converted into extra agents merely because the topic is broad.

## 5. Research-assistance assessment

Primary performs an initial local assessment before allocating additional agents. Consider together:

- confidence;
- local attempt count and stall count;
- genuinely parallel unresolved fronts;
- dependency density;
- number of domains;
- conflicting evidence;
- explicit independent-verification need;
- consequence of an incorrect conclusion;
- tool/capability gaps;
- novelty;
- context pressure where relevant.

Research assistance is justified when additional independent capacity is likely to increase evidence quality, resolve a capability/verification gap, or exploit genuinely parallel work without creating more coordination cost than useful work.

Research capacity follows executable parallel fronts rather than raw question count. Manager capacity follows integration and coordination load rather than a fixed researcher ratio.

Any adaptive or experimental sizing algorithm is advisory evidence only. It does not grant spawn, mutation or restructuring authority. Only the bound `ACTIVE` Primary execution instance may authorize Research/Manager allocation or topology changes.

## 6. Delegation contract

Every delegated Research or Manager assignment must have an explicit durable delegation contract. At minimum it contains:

- contract/project/parent identity;
- assignee role or identity;
- objective;
- in-scope resources;
- explicit out-of-scope boundaries;
- allowed tools;
- capability ceiling;
- write boundaries;
- source-of-truth references;
- evidence requirements;
- output contract;
- completion condition;
- failure condition;
- expiry/cancellation rules when applicable;
- parent task/trace linkage when available.

A child agent must not infer expanded scope from conversation semantics. Scope expansion returns to Primary for authorization.

## 7. Evidence and authority separation

Durable findings should distinguish at least:

- `VERIFIED_FACT` — validated under an explicit verification process;
- `EXECUTION_EVIDENCE` — logs, tests, hashes, tool output, measurements or receipts;
- `DERIVED_KNOWLEDGE` — analysis derived from evidence;
- `HYPOTHESIS` — unresolved explanatory or implementation claim;
- `REJECTED_HYPOTHESIS` — investigated and rejected with reason/evidence;
- `IMPLEMENTATION_RECOMMENDATION` — proposed action that is not itself authority.

Research findings never become accepted configuration or implementation authority merely because multiple agents agree. Promotion remains a Primary/local-policy decision and may require independent review or human approval.

## 8. Dynamic swarm review

During an authorized research campaign, Primary periodically reassesses capacity using observable signals such as:

- unresolved parallel fronts;
- stalled cycles;
- duplicate-work rate;
- idle capacity;
- new domains;
- cross-agent disagreement;
- verification gaps;
- integration/manager overhead.

Scale up only for sustained unmet parallel demand, missing capability or verification need. Scale down for persistent duplication or idle capacity. Add management only when integration burden warrants it. Avoid one-cycle topology flapping.

Research and Manager agents may recommend changes but may not authorize them.

## 9. Risk gate

When the project concerns security boundaries, safety-critical systems, destructive operations, privileged access, firmware/kernel/hardware changes, financial/production effects or other high-consequence mutation, architecture and recovery boundaries must be understood before risky modification begins.

The intake must explicitly record whether risky modification is blocked and the evidence required to unblock it.

## 10. Completion and recovery

Useful state must survive agent loss. Preserve project-scoped:

- intake and source hierarchy;
- delegation contracts;
- findings and provenance;
- rejected hypotheses;
- experiments/test results;
- decisions and rationale;
- unresolved fronts and blockers;
- current swarm/topology state;
- handoff/recovery instructions.

A replacement Primary reruns the identity gate, loads durable project state and continues from those records rather than reconstructing authority or facts from chat history.

## 11. First-output rule for new projects

The first substantive Primary output for a new project should state:

1. project identity/boundaries established or the exact blocking condition;
2. problem definition and source-of-truth hierarchy;
3. technical/operational research decomposition;
4. whether a research swarm is warranted;
5. if warranted, the proposed Research/Manager topology and rationale;
6. the safety/recovery gate preventing premature risky implementation.

This output is a status/decision record. It does not replace durable project-scoped state.
