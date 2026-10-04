# Swarm Learning and Organizational Memory Protocol

Protocol status: `alpha`

## Purpose

The swarm SHOULD become more effective and efficient as agents complete work, without treating conversational continuity or model-weight training as the learning mechanism. Learning is an explicit control-plane process: agents leave evidence, the system validates reusable lessons, and only promoted knowledge is inherited by future agents.

This protocol does **not** claim to retrain the underlying model. It governs cumulative operational intelligence stored in project-scoped durable state and authoritative project doctrine.

## Core invariant

**Experience is not authority.** A single agent observation, successful run, failure explanation, hypothesis, or recommendation MUST NOT silently become swarm policy.

Learning flows through three authoritative layers:

1. **Raw experience** — append-only evidence from work: outcomes, failures, measurements, run logs, experiments, diagnostics, and proposed lessons. Raw experience is non-authoritative.
2. **Validated knowledge** — reusable conclusions that have passed an explicit validation method appropriate to their risk and scope.
3. **Operating doctrine** — concise bootstrap-loadable rules, procedures, heuristics, and defaults approved for routine inheritance by later agents.

Candidate lessons are a transition state inside the raw-experience layer, not a fourth authority tier.

## Lifecycle

The normative lifecycle is:

`OBSERVED -> CANDIDATE -> VALIDATED -> DOCTRINE`

A record may instead transition to `REJECTED`, `SUPERSEDED`, or `EXPIRED` at any stage after observation. Promotion MUST be monotonic with respect to review: downstream agents may not relabel raw experience as validated knowledge or doctrine merely because it appears repeatedly in handoffs or messages.

### OBSERVED

Every agent SHOULD record material execution experience when it could improve future work. Useful observations include:

- a failure mode or recovery path;
- a procedure that materially reduced retries, latency, cost, or coordination overhead;
- an assumption that proved false;
- a reproducible diagnostic signal;
- a task-routing or delegation heuristic;
- a concurrency, lease, packaging, communication, or bootstrap edge case;
- negative evidence showing that a proposed technique did not help.

Agents MUST NOT manufacture a lesson when none was learned. A valid learning checkpoint may explicitly state `NO_MATERIAL_LEARNING`.

### CANDIDATE

An agent may propose a reusable lesson when evidence supports generalization beyond the immediate task. Candidate records MUST include provenance and scope and MUST identify known counterevidence or uncertainty.

Candidates are advisory only. They MAY be retrieved for review, but MUST NOT be injected into future agents as authoritative operating instructions.

### VALIDATED

A candidate may become validated knowledge only after an explicit validation action. Validation MAY include one or more of:

- independent reproduction by another execution instance;
- automated test or benchmark evidence;
- successful use across multiple materially distinct tasks;
- reviewer/manager analysis against source evidence;
- controlled comparison against the current doctrine;
- adversarial attempt to falsify the lesson.

Higher-risk lessons require stronger validation. Any lesson that changes identity, authorization, project boundaries, cross-project exchange, destructive mutation, release gates, or security behavior MUST receive reviewer validation and MUST NOT auto-promote.

### DOCTRINE

Operating doctrine is the smallest, highest-confidence set of lessons that future agents should routinely inherit. Doctrine MUST be concise, scoped, versioned, reversible, and traceable to validated evidence.

Doctrine promotion requires the project's integration authority (PRIMARY/ORCHESTRATOR) unless a narrower project policy explicitly delegates a class of low-risk promotions. Doctrine changes that affect packaged agent behavior MUST pass the ordinary exact-SHA release/package verification gate before being considered deployment-complete.

## Required provenance

Every learning record MUST identify, directly or through immutable references:

- `project_id`;
- `global_run_id` when produced inside a swarm run;
- logical `agent_id` and `agent_instance_id`;
- originating task/work-unit identifier;
- creation time and schema version;
- claim or observation;
- evidence references and integrity hashes where available;
- confidence with an explanation of what the confidence means;
- applicability scope and known exclusions;
- validation state and validation method;
- reviewer/promoter identity when promoted;
- supersession or expiry metadata when applicable.

Confidence MUST NOT substitute for evidence or promotion state.

## Storage and project isolation

Runtime learning state is project-local. Recommended sharding is:

`.swarm/learning/<global_run_id>/{experience,candidates,validation}/...`

Stable validated-knowledge indexes and doctrine pointers MAY be stored on authoritative project surfaces outside a single run, but every promoted item MUST retain immutable provenance back to its source run(s) and evidence.

The ordinary project-identity, capability, lease, compare-and-set, idempotency, and audit rules apply to learning mutations. Cross-project learning is observation-only unless an explicit cross-project exchange is approved. A project MUST NOT write learning state into a peer repository. Slack MAY transport a learning notification or pointer but is never canonical learning state.

## Bootstrap inheritance

New or restarted agents MUST NOT ingest the entire historical learning corpus by default.

Bootstrap SHOULD load, in order:

1. current operating doctrine relevant to the bound project and role;
2. task-relevant validated knowledge selected by explicit scope;
3. raw experience only when required for investigation, validation, or provenance review.

This ordering keeps inherited context small and prevents unvalidated history from becoming accidental policy.

If doctrine conflicts with current human intent, the project identity lock, capability policy, or a newer authoritative protocol, the higher-authority/current control wins and the conflict MUST be surfaced rather than reconciled silently.

## End-of-work learning checkpoint

Before handoff or normal termination, an agent SHOULD persist a learning checkpoint containing:

- material outcome of the work;
- failures/retries and their causes when known;
- reusable lesson candidates, if any;
- evidence references;
- whether existing doctrine was confirmed, contradicted, or unaffected;
- efficiency observations where measurable;
- unresolved uncertainty or follow-up validation needed.

The checkpoint MUST be idempotent for the same execution/work unit and MUST obey project-scoped mutation authority. A failed learning write MUST NOT retroactively invalidate already-verified task output, but it MUST be reflected in the handoff/audit trail when possible.

## Learning metrics

Projects MAY measure whether learning is actually improving swarm performance. Useful metrics include:

- task success and first-pass success rate;
- retry/rework frequency;
- repeated failure recurrence;
- handoff defects;
- stale-write or lease-conflict frequency;
- validation yield (candidate -> validated);
- doctrine rollback/supersession frequency;
- task completion latency where reliably observable;
- unnecessary context loaded per agent where reliably observable.

Metrics are diagnostic evidence, not permission to bypass review gates.

## Anti-poisoning and error propagation controls

The learning system MUST fail closed against institutionalizing mistakes:

- raw observations never become authority through repetition alone;
- promotion retains evidence and reviewer provenance;
- contradictory validated lessons trigger reconciliation rather than last-writer-wins replacement;
- doctrine changes are versioned and reversible;
- expired or superseded lessons are excluded from normal bootstrap inheritance;
- evidence that cannot be revalidated after corruption/tamper detection is quarantined;
- peer-project observations cannot directly mutate local doctrine without local review;
- agents may challenge doctrine with evidence, but may not silently override it.

## Relationship to agent roles

- **RESEARCH/SPECIALIST** agents primarily observe, experiment, and propose candidates.
- **MANAGER/REVIEWER** agents primarily validate, falsify, reconcile, and recommend promotion or rejection.
- **PRIMARY/ORCHESTRATOR** owns doctrine integration and project-wide promotion decisions.

These are default responsibilities, not independent sources of authority; all actions remain subject to the bound session's capabilities and project policy.

## Desired system property

The target property is **cumulative operational intelligence**: later agents should begin with better validated procedures and fewer repeated mistakes than earlier agents, while preserving evidence, reversibility, project isolation, and explicit human/project authority.
