# Post-Hardening Research-Swarm Launch Readiness

Date: 2026-10-05
Repository: `boberino93-bit/intercommunicationsenhancements`
Audited base: `a6c699f7534ccc1e7a7bc4be8c4b935853fa9bd8`
First canary: `boberino93-bit/duo-open`
Canary repository head inspected: `6497e69218de0f585eb0b32ba6676bc2e7e723ac`
Status: READY FOR PROMPT DEPLOYMENT REVIEW; NOT A SCHEDULED-TASK DEPLOYMENT

## Executive conclusion

The hardened system supports the intended `1 MASTER + 1 MANAGER + 3 RESEARCHERS` operating model with one important boundary: correctness must come from the canonical application-level identity/claim/fencing/bootstrap mechanisms, not from an assumption that the host scheduler serializes overlapping invocations. Five hourly wake-up tasks are appropriate. Stagger them at `:00`, `:05`, `:10`, `:20`, and `:30`. Each invocation independently hydrates current canonical state, discovers active claims, and either resumes/coalesces, selects a distinct unclaimed lane, assists, performs labeled independent validation, defers, or recovers a genuinely stale lane.

The launcher adds no second control plane, no second authority hierarchy, no second canonical state store, no second scheduler semantics, and no new approval authority. It is an execution contract over the hardened mechanisms already present.

## A. Post-hardening capability audit

| Required capability | Current implementation / evidence | Status | Launcher impact / fallback |
|---|---|---|---|
| Cold-start orientation | `protocols/post_normalization_successor.md`, `org_agent_mesh/successor_bootstrap.py` | PROVEN | Require bootstrap validation on every invocation; stale/missing state fails visibly. |
| Human project priority | `HUMAN_PROJECT_PRIORITY` in successor bootstrap and canonical recurring protocol | PROVEN | Default project is Duo Open until a newer authenticated human priority supersedes it. |
| Priority/frontier snapshot | `PriorityFrontierSnapshot` implementation with generated/expiry timestamps | PROVEN | Workers read a fresh snapshot; never guess frontier from recency or file order. |
| Scheduled trigger dedupe | `org_agent_mesh/scheduled_tasks.py` trigger IDs/idempotency keys and claims | PROVEN | Duplicate wake-ups coalesce/reject at application level. |
| Claim lease / stale takeover | `ScheduleClaimStore` lease expiry plus canonical ownership controls | PROVEN primitive | Timer firing is not takeover authority; stale recovery requires valid expiry/reconciliation. |
| Fenced durable writes | `org_agent_mesh/durable_state.py` lease, fencing token, epoch, optimistic state version, atomic fsync replacement | PROVEN primitive | Material writes must use canonical fenced/CAS paths where applicable. |
| End-to-end semantic research task identity | Successor bootstrap launch semantics plus project task/frontier state | PARTIAL | Normalize a semantic work key from canonical project/task/objective identity; do not create a parallel task ledger. |
| Durable resume/checkpoint | Durable-state primitives, successor bootstrap checkpoints, project-local handoff contracts | PROVEN primitive / PARTIAL cross-project | Persist a compact research checkpoint projection into the project's canonical state/handoff surface. No reliance on hidden chat memory. |
| Peer discovery/liveness | Canonical recurring protocol; Duo Open DMSH/3 node/control frames and service checkpoints | PROVEN for Duo / PARTIAL generic | Resolve project-native peer/liveness surface each run; absence means conservative dedupe/defer, not invented visibility. |
| Material finding publication | Duo AgentBus persistence + service checkpoints; canonical provenance/evidence states | PROVEN for Duo / PARTIAL generic | Publish to project-authoritative evidence surface; heartbeat/liveness is not promoted to truth. |
| Exact-action human authorization | `org_agent_mesh/launch_admission.py`, step-up attestation verification, governance authority registry | PROVEN | Class D operations require a valid exact action/target/digest/expiry proof. Chat identity alone is not enough. |
| Scheduled agent self-authorizing Class D | Intentionally unsupported | MISSING / NOT PERMITTED | Queue/batch the decision and continue unrelated safe work. |
| Research-swarm bootstrap contract | Hardened bootstrap + this launcher profile | PARTIAL -> STANDARDIZED BY THIS PACKAGE | This package defines a projection/sequence over canonical state, not a new authority store. |
| Native/connector capability resolution | capability registry and runtime tool discovery | PROVEN dynamic mechanism | Resolve at runtime; never assume a provider because a design mentioned it. |
| Host-level overlap serialization | No scheduler guarantee established | UNPROVEN | Never depend on it. Use semantic identity, idempotency, claims, leases, fencing, and coalescing. |
| State between host invocations | Canonical durable repository/state artifacts | PROVEN | Resume from durable state only; never claim continuous cognition. |
| Human decision batching | Existing blocker/approval/evidence surfaces support source state; no universal dedicated queue proven | PARTIAL | Manager emits a `HUMAN_DECISION_BUNDLE` projection from canonical pending decisions. Do not create a second approval ledger. |

### Safety conclusion

The topology is safe for a canary if launcher deployment preserves the above fallbacks. A missing project-specific peer surface, stale frontier, unavailable persistence path, or failed optional tool is localized. Integrity uncertainty, stale-writer safety failure, project-isolation breach, or attempted authorization bypass is not localized away; it invokes the canonical halt/quarantine behavior.

## B. Recommended five-task topology

### MASTER
Portfolio situational awareness, authenticated human priority, cross-project dependency/conflict detection, swarm health, and portfolio-level decision aggregation. It does not micromanage researcher lanes and is not a synchronous RPC dependency.

### MANAGER
Operational coordinator for the current project. Reconciles the research frontier, claims/liveness, evidence, blockers, convergence, and pending human decisions. Merges evidence instead of concatenating prose. May redirect lane selection without creating authority.

### RESEARCHERS 1-3
Perform actual investigation/experimentation/implementation-feasibility/validation work. All use the same dynamic frontier and common startup contract. Biases are tie-breakers only:

- Researcher 1: platform / Android / Samsung / display-continuity / foundational constraints.
- Researcher 2: implementation / architecture / prototype feasibility.
- Researcher 3: validation / failure modes / UX / adversarial or independent verification.

A higher-value unclaimed frontier item overrides the bias.

## C. Recommended schedule

All five tasks recur hourly as wake-up triggers:

- MASTER: minute `00`
- MANAGER: minute `05`
- RESEARCHER 1: minute `10`
- RESEARCHER 2: minute `20`
- RESEARCHER 3: minute `30`

Rationale: the stagger gives the portfolio/project projections a chance to refresh, reduces simultaneous claim contention, and spreads researcher selection across increasingly current evidence. It is not a dependency chain. Any role may proceed from fresh canonical state without waiting for the prior role's same-hour invocation.

### Overlap/coalescing rule

If a previous invocation is still active, resolve the semantic work identity and current claim before acting. Choose exactly one disposition: `CONTINUE_EXISTING_RUN`, `COALESCE`, `TAKE_DIFFERENT_UNCLAIMED_LANE`, `ASSIST`, `INDEPENDENT_VALIDATION`, `WAIT_DEFER`, or `RECOVER_STALE_LANE`. Never steal ownership because a timer fired. Stale recovery requires the implemented lease/owner rules and reconciliation before write.

## D. Shared bootstrap contract

Every role performs this startup sequence:

1. Identify role, invocation/run identity, project candidate, and execution mode.
2. Load and respect `protocols/primary_recurring_swarm_protocol.md` and `protocols/post_normalization_successor.md` plus project-local bootstrap contracts.
3. Build/read the canonical successor bootstrap and require a fresh priority/frontier projection.
4. Resolve authenticated human project priority. Current order is Duo Open, Intercommunication Enhancements, BenefitFlow, AI Behavioral Control Lab, Samsung Power Bootstrap, Warp Propulsion Lab.
5. Bind project identity and data boundary before mutation. Foreign project writes default deny.
6. Resolve the actual capabilities/connectors available to this invocation. Prefer native equivalent capability when available; do not assume it exists.
7. Discover canonical active task identities, claims/leases, recent liveness, material findings, blockers, checkpoints, pending decisions, and relevant source revisions.
8. Classify overlap. Select/resume/assist/validate only work that is safe and authorized.
9. Acquire or renew only a canonical authorized claim. Use fencing/CAS semantics where the state path supports them.
10. Publish start status through the project-authoritative surface if available, then perform useful work.

For Duo Open specifically, bind `duo-open`, load `AGENT_BOOTSTRAP.json`, `AGENT_CONTEXT_REFERENCE.md`, `AGENT_DISCOVERY_V7.json`, current accepted AgentBus state and any live delta newer than the packaged snapshot before interpreting the frontier. Repository snapshot state is evidence, not a claim of complete live forum visibility.

## E. Shared continuation / resume contract

Uncertainty, a pending human decision, a failed optional path, an unavailable optional tool, or a blocked branch is not by itself a reason to terminate the whole invocation.

Record the issue, preserve evidence, block only the affected scope, re-evaluate the frontier, and continue the highest-value safe authorized work that remains.

Stop only when runtime ends, convergence criteria are met, no meaningful safe authorized work remains, a canonical invariant/policy requires halt, integrity is uncertain and quarantine is required, or the entire authorized scope is genuinely blocked.

Before ending, persist/reference: project, role/agent instance, run identity, semantic work identity, claim/lease/fence state, phase, last milestone, objective, material findings and provenance, contradictions, pending decisions, blockers/dependencies, failed approaches worth not repeating, checkpoint, next safe action, recovery instructions, applicable protocol/policy versions, repository/state revisions, and external-effect verification status.

A successor resumes from that state. It does not reconstruct continuity from hidden conversation memory and never claims work continued after its actual execution ended.

## F. Human decision batching contract

Decision classes:

- **A — delegated/reversible:** decide within authority, record provenance, continue.
- **B — human required/nonblocking:** record durable pending decision on canonical project state, block only affected branch, continue elsewhere.
- **C — human required/globally blocking:** checkpoint; produce exact decision request; block only the actual global scope.
- **D — security/high consequence/step-up:** require implemented exact-action authorization. Chat text is not substituted for the required proof. Continue unrelated safe work when possible.

The Manager periodically emits a `HUMAN_DECISION_BUNDLE` projection containing decision ID, project, affected task/branch, exact decision, why human authority is required, options, recommendation when justified, evidence/uncertainty, consequences, blocked/continuing work, downstream unlock, consequence class/authentication strength, exact action digest/reference where supported, expiry/freshness, deferrability, conflicts, and a concise response format.

The bundle is a view of canonical pending decisions; it is not a second approval ledger.

## G-K. Final scheduled prompts

The exact reviewed prompt texts are stored in:

- `research_swarm/prompts/master.md`
- `research_swarm/prompts/manager.md`
- `research_swarm/prompts/researcher_1.md`
- `research_swarm/prompts/researcher_2.md`
- `research_swarm/prompts/researcher_3.md`

## L. Duo Screen / Duo Open canary validation plan

Canary objective is dual: materially advance Duo Open and test the swarm architecture.

Current inspected Duo state identifies Gen7 continuity/presentation work and a bounded next Android candidate around tickets `02 + 03 + 04`: attempt-scoped INNER wake lifetime, exact-current presentation/readiness evidence, and terminal/native-cover stale-work fencing. This is the seed frontier only. Every invocation must reconcile newer live AgentBus state and current `main` before claiming work.

Research allocation is dynamic. A useful starting bias is: R1 validate platform/device constraints underlying 02/03/04; R2 analyze implementation/prototype architecture for the highest-value candidate; R3 independently attack failure modes, exact-current evidence, stale-work races, and validation design. Manager changes this immediately if current evidence changes the frontier.

Canary measurements: bootstrap latency; duplicate-work rate; claim collision rate; stale-writer/fence violations; useful-work ratio; material findings per run; evidence-quality distribution; manager synthesis latency; decision batching quality; human interruption frequency; resume success; stale-worker recovery; idle invocation rate; and whether staggered offsets reduce collision without adding dependency waits.

### Canary halt conditions

Halt/quarantine the affected canary when integrity is uncertain, fencing/lease safety is unreliable, project isolation is breached, an external effect has unknown consequence and blind retry would be unsafe, a high-consequence authorization path is bypassed/fails closed, persistence is unavailable and mutation would become unreconstructable, or systemic invariant failures make ownership/evidence untrustworthy.

Ordinary blocked branches, unavailable optional tools, or nonblocking approvals do not halt the canary.

## M. Failure / recovery matrix

| Failure | Recovery disposition |
|---|---|
| MASTER unavailable | Manager/research continue project-local authorized work from fresh canonical priority/state. |
| MANAGER unavailable | Researchers continue owned work or safely self-allocate if current project contract permits and claims are safe. |
| One researcher unavailable | Manager/researchers recover only after valid stale-owner/lease rules. |
| Duplicate schedule trigger | Coalesce/reject duplicate via trigger/work idempotency; do not duplicate work. |
| Prior invocation still active | Resume/coalesce/alternate lane/assist/labeled validation/defer; no blind takeover. |
| Stale owner | Validate lease expiry and fence; reconcile; then recover with new valid ownership. |
| Stale frontier snapshot | Refresh; if freshness cannot be established, do not guess mutation priority. |
| Optional capability unavailable | Record failure and continue with another safe lane or supported fallback. |
| Persistence unavailable | Analysis may remain read-only where safe; no mutation whose state/effect cannot be durably reconstructed. |
| Nonblocking human decision | Queue/batch; continue unrelated work. |
| Global human decision | Checkpoint and block only when no useful authorized work remains. |
| Class D operation | Require exact-action authorization; no inferred/chat-only approval. |
| Unknown external effect | Verify/recover before retry; never blind retry. |
| Integrity / isolation failure | Quarantine/halt affected scope per canonical policy. |

## N. Metrics and review plan

### After 24 hours
Check all five wake-ups are independently hydrating; verify zero accidental stale-writer violations; inspect duplicate/claim collision rate, useful-work ratio, decision batching, and whether any role incorrectly waited on another role's same-hour run.

### After 72 hours
Verify at least one interruption/resume path and stale-worker recovery where naturally encountered or safely simulated; assess manager evidence merging, frontier reprioritization, fixed-bias usefulness, overlap behavior, and human interruption load.

### After one week
Trend duplicate rate, idle invocations, bootstrap/context cost, stale snapshot frequency, write amplification, approval burden, evidence-quality mix, synthesis cost, convergence progress, and physical/device validation bottlenecks. Tune offsets or researcher biases only from evidence.

### Longer review
Use roughly 30 days of stable operation, including multiple frontier changes and recovery events, before treating the topology as broadly stable for lower-priority projects. Expansion requires no unresolved integrity/consequence-control failures and evidence that the canary's project-specific assumptions do not masquerade as universal architecture.

## O. Human operating instructions

Expect progress to continue while you are absent wherever authority permits. You should see concise project/portfolio summaries and batched genuinely human-required decisions, not a stream of routine micro-approvals. A decision request should state exactly what is blocked, what continues, what action is needed, and the consequence/authentication class.

Intervention is necessary for Class C decisions when the authorized frontier is globally blocked, and for Class D actions through the implemented exact-action authorization path. Do not provide passwords, passkeys, recovery codes, private keys, or root secrets in a model conversation.

This package does **not** create or deploy the five recurring tasks. Creation/deployment remains a separate explicit human action after review.

## Answers to the directive's 20 design questions

1. **Topology supported?** Yes, for canary operation with the documented partial/generic fallbacks.
2. **All hourly?** Yes; treat them as wake-up triggers, not one-hour work boundaries.
3. **Staggered?** Yes: `:00/:05/:10/:20/:30` to reduce claim collisions and increase frontier freshness without hard dependencies.
4. **Prior invocation running?** Reconcile identity/claim and choose resume/coalesce/other lane/assist/validation/defer/stale recovery.
5. **Startup reads?** Canonical protocols, fresh priority/frontier, project bootstrap/handoff, claims/liveness, findings, blockers, decisions, capability/data boundaries, source revisions.
6. **End writes?** Material evidence/provenance, current phase/milestone, contradictions, decisions, blockers, checkpoint, claim/fence disposition, next safe action, recovery instructions, revisions/effect status.
7. **Semantic dedupe?** Normalize canonical project + objective/task identity + relevant target/revision; combine with idempotency/claim state rather than a new task ledger.
8. **Claims/stale workers?** Lease/fencing/CAS; takeover only after valid expiry and reconciliation.
9. **Delegated vs gated?** Class A delegated; B/C human authority; D exact-action/step-up.
10. **Human batching?** Manager emits one bundle projection from canonical pending decisions; Master may aggregate cross-project bundles.
11. **Continue around approvals?** Block branch only and select next safe frontier item.
12. **Global blocker?** No meaningful safe authorized work remains, or a canonical integrity/policy condition requires global halt for that scope.
13. **Manager synthesis?** Merge evidence by provenance, confidence, contradiction, dependency impact, and freshness; do not concatenate prose.
14. **Researcher diversity?** Dynamic frontier with platform / implementation / adversarial-validation tie-breaker biases.
15. **Independent validation?** High-risk/uncertain/platform-variable/high-cost architecture/adversarial assumptions; label it explicitly.
16. **Resume?** Hydrate durable checkpoint + claim/evidence state and continue from next safe action.
17. **Unavailable component?** Graceful degradation per matrix; persistence loss forbids unreconstructable mutations.
18. **Success metrics?** Dedupe, liveness, useful-work ratio, evidence quality, bootstrap cost, write amplification, approval burden, synthesis/resume/recovery quality.
19. **Canary halt?** Integrity/isolation/fencing/authorization/unknown-effect systemic failures or genuinely blocked authorized scope.
20. **Before expansion?** Tune from 24h/72h/1w evidence, validate project-specific assumptions, and require a longer stable window before lower-priority rollout.
