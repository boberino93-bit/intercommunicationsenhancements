# State-of-the-Art Orchestration Evaluation Framework

**Project:** `intercommunicationsenhancements`  
**Record date:** 2026-10-07 (America/Vancouver)  
**Origin:** interactive architecture review with the human project owner  
**Origin work unit:** `chat-sota-threshold-20261007`  
**Learning state:** `CANDIDATE`  
**Authority:** `NON_AUTHORITATIVE_RESEARCH_CANDIDATE`  
**Global swarm run:** none; this record was created outside a swarm run  
**Promotion rule:** do not treat this document as operating doctrine until its claims have been tested, falsified where possible, reviewed, and explicitly promoted under `protocols/swarm_learning.md`.

## 1. Core conclusion

The project does not need to become the world's most intelligent AI system to become state of the art in agent orchestration/intercommunication. A defensible SOTA claim would instead require evidence that the coordination/kernel architecture produces a reproducible advantage over strong baselines when the underlying model, tools, information access, and compute/token budget are controlled.

The central hypothesis is:

> Ordinary frontier models + unusually strong cognitive/coordination infrastructure can produce state-of-the-art collective-agent behavior.

The important research target is therefore **architectural lift**, not merely increased aggregate compute or agent count.

## 2. Maturity ladder

Treat the architecture's maturity using the following ladder.

| Stage | Required evidence | Permitted characterization |
|---|---|---|
| A | Kernel/bootstrap mechanisms, controlled spawning, state assimilation, provenance and recovery concepts exist | Experimental architecture |
| B | Formal protocol, typed state, authority boundaries, reproducible execution and durable state | Research prototype |
| C | Consistently beats single-agent and conventional orchestrator/worker baselines using the same underlying model and comparable budgets | SOTA candidate |
| D | Wins across independent long-horizon benchmarks while controlling model, token, tool-call, latency and cost budgets | State-of-the-art orchestration system candidate with strong evidence |
| E | Independent reproduction plus ablation evidence shows that the kernel mechanisms cause the advantage | Defensible SOTA research result |

Do not collapse these stages. In particular, architectural novelty or impressive behavior is not sufficient evidence for Stage D or E.

## 3. Required system properties to test

### 3.1 Same-model advantage

Compare this kernel against a strong single-agent baseline and conventional multi-agent/orchestrator-worker baselines using the **same underlying model family/version wherever possible**. Hold tools, source information, task definitions and evaluation rules constant. Normalize or explicitly account for token use, tool calls, wall-clock time and monetary cost.

A result driven only by more model calls is not sufficient evidence of superior orchestration.

### 3.2 Long-horizon state integrity

Measure whether agents can work through hundreds of actions without progressively:

- losing requirements;
- contradicting earlier accepted decisions;
- forgetting hidden or delayed constraints;
- corrupting shared state;
- silently replacing authoritative evidence with conversational inference;
- losing track of unresolved dependencies.

### 3.3 Fault containment

Deliberately inject faulty subagents and bad intermediate artifacts. Candidate architecture should isolate rather than amplify:

- hallucinated conclusions;
- stale context;
- incomplete task state;
- contradictory evidence;
- overconfident summaries;
- unauthorized actions;
- malformed handoffs;
- poisoned candidate learning.

The measured question is not whether agents ever fail. It is whether local failures remain local and recoverable.

### 3.4 Epistemic provenance

Important conclusions should be reconstructable through a chain equivalent to:

`claim -> evidence -> producing agent/instance -> transformation/reasoning artifact -> confidence/uncertainty -> authority/promotion state`

Confidence must not substitute for provenance or authority.

### 3.5 Recovery rather than restart

Test whether useful work survives:

- agent termination;
- context-window truncation;
- corrupted local context;
- delayed evidence;
- tool/provider interruption;
- replacement of one agent/model with another compatible agent/model.

A new agent should be able to reconstruct the useful state, identify unresolved uncertainty, and continue without requiring the human to repeat recoverable information.

### 3.6 Bounded authority

Role, capability, state ownership and mutation authority must be enforced below the language layer. A research agent must not become an executor simply because the model generates language implying that it should. Identity, authentication, authorization, leases, work claims and evidence authority remain separate concepts.

### 3.7 Controlled scheduling and scaling

The kernel should decide when parallelism has expected value rather than indiscriminately spawning agents. Evaluate whether it can:

- avoid swarms for trivial work;
- parallelize independent work;
- serialize dependency-heavy work;
- retire redundant branches;
- stop escalating compute when marginal information gain falls below cost;
- preserve fault isolation as agent count rises.

### 3.8 Model independence

Repeat key tests across multiple compatible underlying models or model revisions. The orchestration advantage should survive reasonable model substitution. Otherwise the result may be a model-specific prompting effect rather than a general coordination architecture.

## 4. The key experimental distinction

Do **not** test only whether 50 agents outperform one agent. Current multi-agent systems are already known to benefit from increased parallel exploration and larger aggregate token budgets.

The research question is:

> Does this kernel produce better reliability, recovery, provenance, cost-adjusted task success and constraint retention than alternative architectures at comparable underlying capability and resource budgets?

That is the comparison capable of isolating architectural value.

## 5. Proposed Kernel Stress Benchmark

Build a controlled long-horizon benchmark specifically around the failure modes this project is intended to solve. One canonical scenario can contain roughly 300 ordered actions/work units and introduce controlled disturbances.

Example disturbance schedule:

- **Step 47:** introduce evidence contradicting an earlier working assumption.
- **Step 83:** terminate the current planning/coordinating agent.
- **Step 117:** inject a subagent conclusion known to be false.
- **Step 146:** change a user constraint in an authoritative control message.
- **Step 191:** remove or truncate part of conversational context while leaving durable state intact.
- **Step 230:** introduce an authoritative document contradicting current swarm consensus.
- **Step 270:** require a newly launched agent with no chat history to assume coordination responsibility from durable state.

Variants should randomize disturbance positions, task domains and affected agent roles to prevent overfitting to one script.

## 6. Benchmark metrics

At minimum record:

- final task success;
- partial task success;
- first-pass success;
- requirement/constraint retention;
- authoritative-state adherence;
- contamination propagation distance;
- false-claim survival rate;
- recovery accuracy after interruption;
- recovery latency/tool calls;
- provenance completeness;
- handoff defects;
- unauthorized mutation attempts blocked;
- stale-write/lease conflict frequency;
- redundant work rate;
- unnecessary agent spawning;
- token consumption;
- tool-call consumption;
- wall-clock latency where meaningful;
- monetary execution cost where meaningful;
- number of human corrections required;
- amount of irrelevant context loaded;
- convergence rate across repeated stochastic runs.

A SOTA claim should report both capability and efficiency/reliability tradeoffs rather than task completion alone.

## 7. Baseline suite

The evaluation harness should compare at least:

1. one strong frontier agent with full task context and the same tools;
2. a conventional supervisor/orchestrator + worker architecture;
3. independent parallel agents with final synthesis;
4. this Intercommunication Enhancements kernel with its normal state, authority, provenance, learning and recovery mechanisms;
5. ablated versions of this kernel.

Where possible, run multiple seeds/repetitions and report confidence intervals or other appropriate uncertainty estimates.

## 8. Ablation program

Ablations are required to establish causality rather than correlation. Candidate removals include:

- forensic reconciliation;
- authoritative-state hierarchy;
- bootstrap reconstruction/context recovery;
- contamination isolation/quarantine;
- typed provenance;
- bounded mutation authority;
- lease/ownership fencing;
- learning promotion gates;
- communication-awareness checks;
- adaptive spawn/scheduling controls;
- durable state capsules/handoffs.

If the full architecture wins but removing individual mechanisms does not materially reduce performance, the project has not yet shown that those mechanisms caused the result.

### Illustrative result only — NOT observed evidence

The following values are a **hypothetical example of the kind of result that would be persuasive**, not project measurements:

- conventional orchestrator: 61% success;
- single frontier agent: 68%;
- generic multi-agent system: 73%;
- Intercommunication Enhancements kernel: 91%.

Illustrative ablations:

- without forensic reconciliation: 79%;
- without authoritative-state hierarchy: 74%;
- without bootstrap reconstruction: 81%;
- without contamination isolation: 70%;
- full architecture: 91%.

Never quote these numbers as experimental results.

## 9. External research context verified on 2026-10-07

These sources are evidence/context, not project authority.

### Anthropic — multi-agent research system

Source: https://www.anthropic.com/engineering/multi-agent-research-system

Anthropic reported that an internal multi-agent research configuration using Claude Opus 4 as lead and Claude Sonnet 4 subagents outperformed single-agent Claude Opus 4 by **90.2%** on its internal research evaluation. Anthropic also reported that token use explains a large amount of performance variance in BrowseComp-style research and that its multi-agent research system uses substantially more tokens: roughly **15x chat interactions** in the cited production analysis (with individual agents about 4x chat interactions). Anthropic explicitly notes that highly parallelizable research tasks are a better fit than dependency-heavy tasks.

Implication for this project: simply beating one agent with a larger swarm is not enough. Resource-normalized comparison is mandatory.

### OSWorld 2.0 — long-horizon computer-use benchmark

Source: https://arxiv.org/abs/2606.29537

OSWorld 2.0 contains **108 long-horizon workflows**. The paper reports a median human completion time of about **1.6 hours** per task and an average of **318 tool calls** with Claude Opus 4.7 at maximum thinking, compared with about 30 in OSWorld 1.0. Under the paper's primary binary completion metric at a 500-step cap, Claude Opus 4.8 with maximum thinking and batched tool calls achieved **20.6%** completion with a 54.8% partial score. Reported frontier failure modes include losing constraints, missing information arriving during execution, guessing instead of correctly recovering state, and skipping verification.

Implication for this project: these failure modes overlap strongly with the kernel's target mechanisms and provide a credible external long-horizon evaluation domain.

### OpenAI — SWE-bench Verified retirement as frontier signal

Source: https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/

On 2026-02-23 OpenAI stated that it had stopped using SWE-bench Verified as a frontier capability signal because of benchmark contamination and evaluation defects, and recommended SWE-bench Pro instead. Its audit found material test/design issues in a substantial fraction of frequently failed tasks and evidence of benchmark exposure in frontier models.

Implication for this project: benchmark quality, contamination resistance and independent/held-out evaluation matter. A high score on a saturated or contaminated benchmark cannot support a defensible SOTA claim by itself.

## 10. SOTA claim threshold

A technically defensible claim should require all of the following:

1. statistically meaningful/reproducible advantage over strong baselines;
2. multiple long-horizon environments rather than one hand-built demonstration;
3. comparable underlying models, tools and information access;
4. explicit accounting for tokens, tool calls, cost and latency;
5. fault-injection and recovery tests;
6. provenance and authority-integrity evaluation;
7. ablation evidence tying gains to kernel mechanisms;
8. no known benchmark contamination sufficient to explain the result;
9. independent review/reproduction before using the strongest wording.

Until those conditions are satisfied, prefer wording such as **experimental architecture**, **research prototype**, or **SOTA candidate**, depending on evidence maturity.

## 11. Research program implied by this framework

Future swarms working on architecture quality should treat the next major leap as **measurement and falsification**, not simply more agents or more complexity.

Recommended work sequence:

1. formalize kernel invariants as machine-checkable assertions where possible;
2. define benchmark task schemas and disturbance injection points;
3. implement baseline adapters with identical model/tool budgets;
4. implement telemetry for provenance, state integrity, recovery and resource consumption;
5. run deterministic/unit-level fault tests before expensive swarm trials;
6. run repeated stochastic long-horizon trials;
7. perform ablations;
8. analyze failure clusters rather than only aggregate success;
9. promote only independently supported lessons into validated knowledge/doctrine;
10. seek external reproduction after internal results become stable.

## 12. Candidate lessons for swarm digestion

The following are candidate lessons, not doctrine:

- **Kernel quality before swarm scale.** Scaling agent count before state, authority, provenance and recovery invariants are reliable can amplify errors faster than it amplifies intelligence.
- **Hallucination tolerance is an architectural property.** The target is not zero hallucinations; it is preventing one agent's unsupported claim from becoming collective authoritative state.
- **Context recovery should be evaluated as continuity, not memory theater.** A fresh agent should reconstruct task state from durable evidence and explicit authority rather than pretending to remember inaccessible chat context.
- **Authority must be non-linguistic.** Text generated by a model cannot by itself widen permissions or promote evidence.
- **Cumulative intelligence requires gated learning.** Raw experience becomes useful organizational intelligence only through validation and promotion, with provenance retained.
- **State-of-the-art is a measurement claim.** The architecture earns the label only when controlled evidence shows that it exceeds strong alternatives.

## 13. Falsification conditions

This hypothesis should be weakened or rejected if controlled testing shows any of the following:

- the performance gain disappears after matching token/tool budgets;
- gains occur only with one underlying model or one benchmark;
- the kernel adds complexity without improving reliability or cost-adjusted success;
- ablations show no meaningful contribution from the claimed mechanisms;
- swarm size increases contamination propagation or authority violations faster than task success;
- fresh-agent recovery depends on hidden conversational state rather than durable project state;
- benchmark gains are explainable by contamination, evaluator leakage or task-specific overfitting.

## 14. Relationship to existing project learning protocol

This record intentionally remains `CANDIDATE`. It should be consumed by RESEARCH agents as a testable hypothesis and by MANAGER/REVIEWER agents as a validation target. PRIMARY/ORCHESTRATOR may promote only the portions supported by evidence under `protocols/swarm_learning.md`.

The desired endpoint is not agreement with this document. The desired endpoint is a body of reproducible evidence that either validates, modifies, or falsifies it.