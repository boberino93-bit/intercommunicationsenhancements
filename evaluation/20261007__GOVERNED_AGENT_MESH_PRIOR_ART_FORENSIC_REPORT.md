# Governed Agent Mesh Prior-Art / Novelty-Falsification Forensic Report

**Project:** `intercommunicationsenhancements` / Intercommunications Enhancements  
**Investigation date:** 2026-10-07 (America/Vancouver local date; web snapshot gathered 2026-10-08 UTC)  
**Repository baseline examined:** `main@c38968c5e08c6fd14007c0c5dcabe4a2a71e6936`  
**Role posture:** RESEARCH / specialist evidence investigation  
**Classification:** `CANDIDATE` — non-authoritative; requires PRIMARY/MANAGER validation before doctrine or external novelty claims  
**Mutation authority:** false for accepted/canonical state; this report records evidence only  
**Finding ID:** `GOVERNED-AGENT-MESH-PRIOR-ART-2026-10-07`

---

## 1. Executive finding

The broad claim **“nobody else has done this” is not supportable** on the available evidence. Nearly every major primitive in the current architecture has substantial antecedent art: shared blackboards, distributed task negotiation, supervisor/worker trees, specialist routing, multi-agent orchestration, external memory/reflection, human approval, policy decision/enforcement separation, zero-trust workload identity, capability/least-privilege authorization, stateful agent messaging, durable workflows, retries/idempotency, leases/fencing, provenance, audit logging, cross-domain federation, and policy-governed autonomous software agents.

A stronger and presently defensible technical statement is narrower:

> **This investigation found no single public system, paper, standard, framework, or patent that obviously implements the exact full conjunction of governance semantics presently expressed by Intercommunications Enhancements.**

That is an **absence-of-found-match result**, not proof of novelty, originality, patentability, or priority. The search materially falsified broad novelty while leaving a **combination-level distinctiveness hypothesis** unresolved.

The strongest potentially distinctive area is not “an intelligent generalist delegates to specialists.” That pattern is common. The strongest candidate lies in the **specific composition of identity-bound authorization, fail-closed lifecycle admission, capability non-escalation, cross-project non-conveyance of authority, immutable/sanitized copy-by-value knowledge exchange, explicit context evidence/authority separation, staged externally persisted organizational learning, execution-instance/lease binding, and reproducible role packaging**.

Patent evidence significantly raises the bar. In particular:

- `US20190068451A1` (priority 2014-07-16) expressly covers policy-governed software agents operating autonomously inside governing constraints, including agent capabilities and precedence of local policy.
- `US12580768B2` / `US20260019268A1` (priority 2024-05-31, related family priority 2024-01-19) covers governed LLM persona agents, metadata-bound roles, policy constraints, supervisor gating, session-memory governance, immutable audit, delegation chains, federated policy tokens, and receiving-domain validation.
- `US20250350644A1` (priority 2024-05-07) covers security processing for multi-agent systems using execution plans plus policy enforcement points controlling agent access and input/output.
- `US20250373432A1` covers federated compliance tokens for persona-agent sessions including delegation chain, credential lineage, policy snapshots, expiry/revocation, cross-boundary inheritance, provenance, and linked audit trails.
- `US20260252697A1` / related PCT family claims priority to US provisional `63/743,249` dated 2025-01-09 and describes governed assistant/agent execution with structural separation of intent, authorization, execution, specialized-agent routing, non-self-authorizing executive agents, policy isolation, append-only audit, and heterogeneous nodes.

Those disclosures do **not** establish that the current project is unoriginal as a whole. They do establish that governance, role/persona binding, delegation, cross-domain policy validation, specialist orchestration, and audit cannot safely be presented as individually unprecedented.

**Forensic verdict:**

- **Broad architectural novelty claim:** FALSIFIED / unsupported.
- **Individual mechanism novelty:** mostly FALSIFIED or strongly weakened by prior art.
- **Exact-combination novelty:** UNRESOLVED; no exact public match found in this investigation.
- **Patent/legal novelty:** NOT ASSESSED to a professional legal standard; requires claim construction, priority-date reconstruction, classification/citation searching, and counsel if pursued.
- **Most credible differentiation locus:** governance composition and boundary semantics, not multi-agent delegation itself.

---

## 2. Question under investigation

The investigation was triggered by the observation that the system was beginning to behave like a capable generalist that can recognize when deeper expertise is required and invoke specialist analysis, while remaining governed rather than uncontrolled.

The forensic question is therefore not “do multi-agent systems exist?” They plainly do. The useful questions are:

1. Which parts of the architecture are established prior art?
2. Which parts are contemporary convergent practice?
3. Which exact conjunctions were not located elsewhere?
4. Which patent disclosures create especially close overlap?
5. Is the science-fiction analogy evidence of novelty? (No; it is best treated as conceptual inspiration.)
6. What claims can the swarm responsibly make after attempting to falsify novelty?

---

## 3. Internal architecture actually examined

This report assesses the implementation/documented architecture rather than the conversational metaphor.

Primary internal evidence examined included:

- `ARCHITECTURE.md`
- `AGENT_CONTEXT_REFERENCE.md`
- `PROJECT_IDENTITY_LOCK.json`
- `roles/RESEARCH.md`
- `protocols/swarm_learning.md`
- `.interagent/handoffs/dynamic-context-integration-primary-review-2026-10-07.json`
- `.interagent/directives/2026-10-07-recommendation-pause.json`
- `.swarm/README.md`

Salient project mechanisms under test:

1. **Project identity is an authorization boundary**, with immutable project binding and fail-closed recovery/revalidation.
2. **Session lifecycle controls mutation authority** (`UNBOUND -> BOUND -> INITIALIZED -> ACTIVE -> DRAINING -> TERMINATED`); only an active bound session may mutate.
3. **Agent identity and execution-instance identity are distinct**; children get fresh execution instances.
4. **Authority tier and capability set are separate**; children inherit the same or a strict subset of capability and cannot self-escalate.
5. **Provider/admission lifecycle precedes model invocation**, with bounded launches, deterministic staggering, retries/backoff, and launch identity.
6. **Messaging carries project/source/destination identity plus causation/correlation/idempotency/expiry** and requires an active publisher capability.
7. **Tasks/artifacts/messages/locks/leases/audit state are identity-bound**; stale execution instances cannot inherit authority merely from old state.
8. **Context is layered**: presence, evidence quality, and authority are distinct concepts; provenance/temporal state/conflict must be preserved.
9. **Swarm memory is external-only**; model-native memory is explicitly not collective control-plane state.
10. **Organizational learning is staged**: raw experience -> candidate -> validated knowledge -> doctrine, with promotion authority separated by role.
11. **Bootstrap is selective**: doctrine first, scoped validated knowledge second, raw history only on demand.
12. **Cross-project exchange is explicit and non-authority-bearing**: approval/scope/purpose/expiry, `authority_conveyed=false`, target-side revalidation, immutable/sanitized copy-by-value evidence.
13. **Semantic federation is separated from execution authority**, and routing lineage rejects cycles/repeated project visits.
14. **Release packaging is exact-revision and role-specific**, with reproducibility checks across PRIMARY/MANAGER/RESEARCH artifacts.
15. **Canonical accepted-state mutation is role-governed**; RESEARCH can produce evidence but not promote it.

These are the actual features against which public antecedents were compared.

---

## 4. Method

This was a technical forensic prior-art / novelty-falsification scan, not a marketing comparison.

### 4.1 Search strata

Evidence was collected across:

- classical distributed AI / multi-agent systems;
- blackboard architectures and control blackboards;
- distributed negotiation and task allocation;
- supervisor/worker fault-tolerance hierarchies;
- mixture-of-experts routing;
- LLM multi-agent orchestration and specialist handoffs;
- memory/reflection/context architectures;
- human-in-the-loop approvals and resumable execution;
- policy engines and authorization languages;
- zero-trust/workload identity/federation;
- provenance and audit standards;
- durable workflow/reconciliation/idempotency/lease patterns;
- A2A/MCP/agent interoperability and identity infrastructure;
- 2025-2026 agent security/governance standards;
- patent publications targeting policy-governed agents, multi-agent security, federated compliance, cross-domain authorization, agent identity, orchestration, and governed execution.

### 4.2 Standard of conclusion

This report distinguishes:

- **FOUND PRIOR ART:** a materially similar mechanism is publicly documented.
- **CONVERGENT PRACTICE:** multiple modern systems independently implement the same broad pattern.
- **NO EXACT MATCH FOUND:** the search did not reveal the exact conjunction; this is not proof of novelty.
- **UNRESOLVED:** insufficient evidence for a stronger conclusion.

No negative search result is promoted to “nobody has done it.”

---

## 5. Classical antecedents

### 5.1 Blackboard systems — shared context + specialist knowledge sources

**Hearsay-II (1980)** is a direct historical antecedent to the idea that independent specialist processes can cooperate through structured shared working state. Its architecture coordinated multiple knowledge sources through a blackboard and control mechanisms.

Reference: Lee D. Erman, Frederick Hayes-Roth, Victor R. Lesser, D. Raj Reddy, *The HEARSAY-II Speech-Understanding System: Integrating Knowledge to Resolve Uncertainty*, ACM Computing Surveys 12(2), 1980, DOI `10.1145/356810.356816`.

**Effect on novelty:** shared global working context and specialist invocation are not new. A system in which specialist modules contribute selectively to a common problem has at least 1980-era lineage.

### 5.2 Blackboard control architecture — governance/control as its own problem

Barbara Hayes-Roth's work on blackboard control architectures explicitly separated domain problem solving from control reasoning and represented control knowledge as first-class architecture.

**Effect on novelty:** the insight that “who should act next, under what conditions?” deserves an explicit control layer is longstanding.

### 5.3 Contract Net Protocol — distributed delegation/selection

Reid G. Smith's **Contract Net Protocol (1980)** specified distributed task allocation by negotiation between nodes offering tasks and nodes capable of performing them.

Reference: Reid G. Smith, *The Contract Net Protocol: High-Level Communication and Control in a Distributed Problem Solver*, IEEE Transactions on Computers C-29(12), 1104-1113, DOI `10.1109/TC.1980.1675516`.

**Effect on novelty:** assigning subtasks to suitable agents, negotiation/resource allocation, and distributed control are decades-old ideas.

### 5.4 Supervisor trees

Erlang/OTP supervision trees formalize hierarchical supervisor/worker relationships with fault detection, restart strategy, and child lifecycle management.

**Effect on novelty:** manager/worker hierarchy and controlled child lifecycles are not novel. The project may still differ in authorization semantics tied to each child execution instance.

### 5.5 FIPA agent communication

FIPA ACL standards define agent message structures, communicative acts, sender/receiver identities, protocol/conversation correlation and agent management/discovery patterns.

**Effect on novelty:** standardized agent-to-agent messaging and conversation identifiers are established multi-agent-system primitives.

---

## 6. Specialist routing and orchestration

### 6.1 Mixture of Experts

Shazeer et al. (2017) introduced a sparsely gated Mixture-of-Experts layer in which a learned gating mechanism activates a sparse subset of expert subnetworks for each input.

Reference: arXiv `1701.06538`, *Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer*.

This is model-internal rather than organizational multi-agent orchestration, but it is strong conceptual antecedent for **conditional routing from a general input path to specialized expertise**.

### 6.2 AutoGen

AutoGen (2023/2024) explicitly supports applications composed from multiple customizable agents that converse, use tools, incorporate humans, and implement flexible interaction patterns.

Reference: arXiv `2308.08155`, *AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation*.

### 6.3 MetaGPT

MetaGPT assigns diverse specialist roles and encodes standardized operating procedures into multi-agent workflows, decomposing complex tasks into role-specific subtasks and verification stages.

Reference: arXiv `2308.00352`, ICLR 2024.

### 6.4 Magentic-One

Magentic-One uses a lead **Orchestrator** that plans, tracks progress, replans, and directs specialist agents to perform browser, file, coding and execution tasks.

Reference: arXiv `2411.04468`, Microsoft Research technical report MSR-TR-2024-47.

### 6.5 OpenAI Agents SDK

As of the research snapshot, the OpenAI Agents SDK documents both:

- **manager-style orchestration** where an orchestrator remains in control and calls specialist agents as tools; and
- **handoffs** where a triage agent delegates and a specialist becomes the active agent.

It also provides sessions, guardrails, tracing, human-in-the-loop, resumable run state, sandboxed specialists and durable-execution integrations.

Primary docs:

- `https://openai.github.io/openai-agents-python/`
- `https://openai.github.io/openai-agents-python/multi_agent/`
- `https://openai.github.io/openai-agents-python/handoffs/`
- `https://openai.github.io/openai-agents-python/tracing/`

Notably, the handoff documentation warns that when authorization depends on handoff fields, authorization should be checked before side effects. This is direct evidence that specialist handoff and authorization gating are now mainstream implementation concerns.

### 6.6 Verdict on the “master's calls PhD” metaphor

**FALSIFIED as a novelty basis.** A generalist/triage/orchestrator recognizing task type and invoking a specialist is a common modern pattern and has historical analogues much older than LLMs.

What remains potentially distinctive is the **governance envelope around the delegation** — identity, authorization, provenance, scope, non-escalation, external persistence, cross-project barriers, acceptance semantics, and release discipline.

---

## 7. Memory, reflection, context and organizational learning

### 7.1 Generative Agents

Park et al. (2023) store a natural-language record of experience, synthesize higher-level reflections, and dynamically retrieve memories for planning.

Reference: arXiv `2304.03442`; ACM UIST 2023 DOI `10.1145/3586183.3606763`.

### 7.2 MemGPT

MemGPT treats context management analogously to operating-system memory hierarchies, moving information between memory tiers and using interrupts/control flow to support long-running conversational state.

Reference: arXiv `2310.08560`.

### 7.3 Reflexion

Reflexion stores linguistic feedback/reflection in episodic memory and uses it to improve later trials without changing model weights.

Reference: arXiv `2303.11366`.

### 7.4 W3C PROV

The W3C PROV family formalizes interoperable provenance for entities, activities and agents, including derivation, versioning, provenance-of-provenance, bundles, constraints, access and query.

References:

- `https://www.w3.org/TR/prov-overview/`
- `https://www.w3.org/TR/prov-o/`
- `https://www.w3.org/TR/prov-dm/`
- `https://www.w3.org/TR/prov-constraints/`

### 7.5 Internal staged learning compared with prior art

The project's explicit sequence:

`OBSERVED -> CANDIDATE -> VALIDATED -> DOCTRINE`

plus separated role authority for proposing, validating/falsifying, and promoting knowledge is **not equivalent** to merely having long-term memory or reflection.

Prior art clearly covers:

- persistent experience memory;
- reflection and summarization;
- provenance;
- validation/review workflows in general;
- knowledge bases and policy promotion in non-agent domains.

**No exact public match was found in this search** for the full project-specific organizational-learning lifecycle combined with role-separated promotion authority, external-only swarm state, project scoping, doctrine-first bootstrap and raw-history-on-demand.

**Status:** combination-level distinctiveness candidate; not proven novel.

---

## 8. Policy engines, authorization, zero trust and workload identity

### 8.1 Open Policy Agent (OPA)

OPA explicitly **decouples policy decision-making from policy enforcement** and evaluates structured request data against declarative policy.

Reference: `https://www.openpolicyagent.org/docs`

**Effect on novelty:** centralized/decoupled policy decisions and policy-as-code are established.

### 8.2 Cedar

Cedar models authorization as **principal + action + resource + context**, with permit/forbid policies and contextual request information. Current guidance explicitly discusses automated/AI agents acting on behalf of users.

References:

- `https://docs.cedarpolicy.com/`
- `https://docs.cedarpolicy.com/auth/authorization.html`
- `https://docs.cedarpolicy.com/bestpractices/bp-using-the-context.html`

**Effect on novelty:** explicit identity-action-resource-context authorization is established, including agent-mediated requests.

### 8.3 NIST Zero Trust

NIST SP 800-207 shifts trust from network location to resource- and identity-centered authorization, rejecting implicit trust based on location. SP 800-207A extends the model toward cloud-native application and service identities.

References:

- NIST SP 800-207, DOI `10.6028/NIST.SP.800-207`
- NIST SP 800-207A (2023)

### 8.4 SPIFFE/SPIRE

SPIFFE defines cryptographic workload identity, trust domains, SVIDs and federation. Each trust domain has its own authority and may federate without collapsing administrative isolation.

References:

- `https://spiffe.io/docs/latest/spiffe-specs/spiffe-id/`
- `https://spiffe.io/docs/latest/spiffe-specs/spiffe_federation/`
- `https://spiffe.io/docs/latest/spiffe-specs/spiffe_workload_api/`

**Effect on novelty:** immutable/structured workload identity, trust-domain isolation, runtime identity issuance and cross-domain federation are established security concepts.

### 8.5 Capability security / attenuation

Capability-based security predates modern agent systems and centers authorization on possession of unforgeable, scoped authority. Macaroon-style caveats further demonstrate attenuation/delegation under contextual restrictions.

**Effect on novelty:** “child gets no more authority than parent” and least-authority inheritance are conceptually grounded in longstanding security practice.

### 8.6 Internal difference that may matter

The project combines the above ideas into an agent-execution rule set where:

- project identity is the authorization boundary;
- each execution instance is fresh and separately attributable;
- authority tier is not the same object as capability set;
- children inherit the same or strict-subset capability set;
- stale instances cannot reuse ownership merely because artifacts/locks exist;
- cross-project context does not itself convey authority;
- receiving projects re-authorize independently.

No single comparator examined implemented all of those semantics together in the same form.

---

## 9. Human-in-the-loop, approvals and guarded execution

Human approval for sensitive agent actions is now well-established across current agent frameworks. OpenAI Agents SDK, AutoGen, LangGraph and durable workflow systems expose pause/interrupt/review/resume patterns.

**Effect on novelty:** human-in-the-loop itself is not novel.

Potentially differentiating project semantics are the coupling of approval to immutable project/session identity, exact capabilities, accepted-state authority, collision rules and cross-project non-conveyance.

---

## 10. Durable workflows, reconciliation, idempotency, leases and stale-writer defense

Multiple non-AI systems provide direct antecedents:

- **Temporal** and similar durable-workflow engines persist execution history and resume after process failure.
- **Kubernetes controllers** continuously reconcile current state toward desired state.
- **Transactional outbox/idempotent-consumer patterns** address duplicate message delivery and state/message consistency.
- **Leases + fencing tokens / CAS** prevent stale holders from continuing to mutate shared resources after ownership changes.

Reference for controller pattern: `https://kubernetes.io/docs/concepts/architecture/controller/`

**Effect on novelty:** retry state machines, durable execution, reconciliation, idempotency, leases and stale-writer rejection are established distributed-systems techniques.

The project-specific novelty hypothesis can therefore only lie in how those mechanisms are bound to agent/project/execution identity and governance, not in their existence.

---

## 11. Agent interoperability: A2A, MCP and AGNTCY

### 11.1 A2A

The Agent2Agent (A2A) protocol defines concepts including Agent Cards, messages, stateful Tasks, context IDs, artifacts, discovery, authentication and lifecycle semantics.

Primary spec: `https://a2a-protocol.org/dev/specification/`

A2A `contextId` groups related tasks/messages; `taskId` identifies stateful units of work.

**Effect on novelty:** agent discovery, identity/capability description, task lifecycle and context correlation are convergent public standards work.

### 11.2 MCP authorization

The Model Context Protocol authorization specification defines transport-level authorization for clients acting on behalf of resource owners, using OAuth-family mechanisms and protected resource metadata/discovery.

Reference: `https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization`

**Effect on novelty:** scoped authorization around agent/tool access is standardized infrastructure work, though MCP is not itself a swarm governance system.

### 11.3 AGNTCY

AGNTCY describes open infrastructure for agents to discover one another, verify capabilities, communicate securely and collaborate across framework/organizational boundaries. Its components cover directory/discovery, secure messaging, capability schema, decentralized identity/policy-based access, hardened runtime and observability.

Reference: `https://docs.agntcy.org/`

**Effect on novelty:** secure discovery + identity + messaging + capability description + cross-organization collaboration is active public infrastructure, making broad claims of unique “agent control plane” architecture untenable.

---

## 12. Current security/governance convergence (2026)

### 12.1 NIST AI Agent Standards Initiative

NIST/CAISI launched the AI Agent Standards Initiative on 2026-02-17 specifically around interoperable agents capable of acting securely on behalf of users.

Reference: `https://www.nist.gov/news-events/news/2026/02/announcing-ai-agent-standards-initiative-interoperable-and-secure`

### 12.2 OWASP Agent Control Standard

OWASP's Agent Control Standard (ACS), released into the GenAI Security Project in September 2026, emphasizes that enterprise agents should be inspectable, traceable, instrumentable and controllable at runtime, with middleware hooks and portable declarative controls.

Reference: `https://genai.owasp.org/resource/agent-control-standard-acs/`

**Effect on novelty:** inspectability, runtime policy, traceability, identity/privilege boundaries and governance are rapidly becoming baseline expectations rather than niche ideas.

### 12.3 Consequence

The field is converging quickly on exactly the categories this project emphasizes: identity, least privilege, runtime control, scoped tool use, memory isolation, provenance, approvals, registries, revocation and audit.

Therefore, distinctiveness should be expressed in **specific enforceable invariants and compositions**, not broad category labels such as “governed swarm,” “secure multi-agent system,” or “agent orchestration.”

---

## 13. Patent forensic scan

This section is intentionally separated from the general literature because patent overlap has different evidentiary implications. Publication/priority metadata were checked through Google Patents or other public patent-family indexes where available. This remains a search snapshot, not legal advice.

### 13.1 US20190068451A1 — Policy Governed Software Agent System and Method of Operation

- **Prior art date:** 2014-07-16
- **Publication:** 2019
- **Status shown by Google Patents:** granted family
- **Core overlap:** autonomous software agents constrained by overarching policy; local policy precedence; capability information; high-assurance operation.

This is a major antecedent to the general concept “autonomous agents, but governed.”

**Novelty impact:** severe against any broad claim that constraining autonomous software agents with policy is new.

### 13.2 US20250350644A1 — Security Processing of Multi-Agent System

- **Priority:** Korean filings beginning 2024-05-07
- **Core overlap:** execution plan containing multiple agents; policy enforcement points controlling access/input/output; multi-agent security policies; centralized policy management and security status.

**Novelty impact:** strong against claims centered on security-policy enforcement among multiple LLM agents.

### 13.3 US12580768B2 / US20260019268A1 — Decentralized Persona Agent Governance

- **Priority shown:** 2024-05-31; related parent family traces to 2024-01-19
- **Core overlap:** persona/role construction bound to metadata, policy constraint engine, supervisor gating, session memory governance, audit logging, delegation chain, federated policy tokens, receiving-domain policy validation, cryptographically linked audit.

This is one of the closest public overlaps located.

**Novelty impact:** substantial. Any claim around metadata-bound personas/roles, policy gates, supervisor review, federated delegation and audit must be carefully distinguished from this family.

### 13.4 US20250373432A1 — Federated Compliance-Token Inheritance / Digital Artifact Registry

- **Core overlap:** per-agent-session signed token containing delegation chain, credential lineage, policy snapshot, expiry/revocation; transfer/inheritance across organizational/jurisdictional boundaries; immutable provenance and audit.

**Novelty impact:** substantial against broad claims around cross-boundary agent delegation with lineage/policy/provenance.

### 13.5 US20250244964A1 — AI Capabilities in Software Applications

Public text describes multi-agent orchestration in which agents operate within authorized domains, share through credential-respecting interfaces, and are subject to higher-level orchestration and least-privilege credential review.

**Novelty impact:** supports the conclusion that least-privilege specialist-agent collaboration is convergent practice.

### 13.6 US20250259043A1 — Fault-Tolerant Security-Enhanced Collaborative/Negotiating Agent Networks

Public text describes an orchestration engine and deontic subsystem enforcing obligations, permissions and prohibitions over specialist outputs, including halting/transforming output and policy-compliance intervention.

**Novelty impact:** strong overlap with policy-enforced collaborative-agent execution.

### 13.7 US20250373451A1 — Trust-Enabled AI / Non-Human Identity Orchestrator

Public abstract describes cryptographic identity for AI agents/services/workloads, signed publications, trust rules, access control, provenance validation, policy delegation, federated domains, zero-trust enforcement, secure cross-domain communication and selective replication.

**Novelty impact:** strong overlap with agent identity, federation, provenance, and cross-domain policy.

### 13.8 US20250315514A1 — Cross-Domain Authorization / Cross-Domain Call

- **Prior art date:** 2021-08-27
- **Core overlap:** explicit authorization policies for cross-domain calls, requester/target in different network domains, permission determination before establishing a cross-domain route.

**Novelty impact:** cross-domain reauthorization and policy-gated routing are established outside specifically LLM-agent systems.

### 13.9 US20260252697A1 — Governed Execution Across Heterogeneous Nodes

- **US filing:** 2026-01-09
- **Claims benefit of provisional:** US `63/743,249`
- **PCT family listing shows priority:** 2025-01-09
- **Core overlap:** structured state separated from execution logic; governance evaluates intended actions; authorization artifact/token; enforcement boundary; structural separation between intent derivation, authorization and execution; specialized agents; executive orchestration unable to self-authorize; policy isolation; append-only audit; governed agent runtime; multi-role approval.

This disclosure is exceptionally important because its language overlaps the project's core framing of **governed, non-sovereign orchestration**.

**Novelty impact:** substantial against broad “orchestrator cannot self-authorize / governance separate from execution” claims.

### 13.10 CN121997321A — Authority-Boundary Agent Sensitive-Operation Tracking

- **Filing/prior-art date shown:** 2026-04-09
- **Core overlap:** authority-boundary context, identity delegation chains, sensitive-effect tracing, minimal boundary-crossing analysis, causal evidence packets.

**Novelty impact:** demonstrates current 2026 convergence around explicit authority-boundary forensic tracing for agents.

### 13.11 Patent-scan bottom line

The patent landscape contains materially close work **before the current October 2026 implementation period**. Accordingly:

- governance is not new;
- multi-agent security enforcement is not new;
- role/persona binding is not new;
- delegation chains are not new;
- federated policy validation is not new;
- immutable/auditable agent traces are not new;
- least-privilege multi-agent collaboration is not new;
- separating intended action from authorization and execution is not new.

What remains unresolved is whether the project's **exact combination and specific invariant set** is anticipated by any single reference or would have been obvious over a combination of references. That is a legal/claim-construction question, not something this report can establish.

---

## 14. Component-level claim chart

| Internal mechanism | Closest antecedent(s) found | Forensic status |
|---|---|---|
| Generalist routes to specialist | MoE; AutoGen; Magentic-One; OpenAI Agents SDK; MetaGPT | **Established / convergent** |
| Shared working context | Hearsay-II / blackboard systems | **Established** |
| Task delegation / allocation | Contract Net; modern orchestrators | **Established** |
| Supervisor/worker lifecycle | Erlang/OTP; workflow engines | **Established** |
| Human approval before sensitive action | modern agent frameworks; policy engines | **Established / convergent** |
| Policy decision separate from enforcement | OPA; XACML lineage; governed-agent patents | **Established** |
| Principal/action/resource/context auth | Cedar and ABAC systems | **Established** |
| Workload identity / trust-domain federation | SPIFFE/SPIRE; zero trust | **Established** |
| Agent messaging, task IDs, context IDs | FIPA; A2A | **Established / standardized** |
| External long-term memory / reflection | Generative Agents; MemGPT; Reflexion | **Established** |
| Provenance / derivation / versioning | W3C PROV | **Established** |
| Durable execution / retry / resume | Temporal-class workflows; Agents SDK integrations | **Established** |
| Reconciliation / desired state | Kubernetes controllers | **Established** |
| Idempotency / stale-writer defense | distributed-systems outbox/idempotency/fencing/CAS | **Established** |
| Policy-governed autonomous agents | US20190068451A1 and later work | **Established** |
| Multi-agent security PEP/PDP style | US20250350644A1; OPA/XACML concepts | **Established / directly overlapping** |
| Delegation chain + cross-domain policy token | US12580768B2; US20250373432A1 | **Direct overlap** |
| Governed orchestrator cannot self-authorize | US20260252697A1 | **Direct overlap** |
| Project ID as immutable authorization boundary | zero-trust/trust-domain/workload-ID antecedents, but exact formulation not found | **Combination candidate** |
| Fresh child execution identity + stale lease rejection | workload identity + fencing antecedents; exact combination not found | **Combination candidate** |
| Authority tier separate from capabilities + strict-subset spawn | capability security antecedents; exact project semantics not found | **Combination candidate** |
| `authority_conveyed=false` cross-project semantics | federation/reauthorization antecedents; exact explicit invariant not found | **Combination candidate** |
| Immutable sanitized copy-by-value knowledge exchange | provenance/federation/data-diode-like concepts; exact agent pattern not found | **Combination candidate** |
| Context presence vs evidence quality vs authority separation | provenance/trust/context systems overlap; exact tripartite rule not found | **Combination candidate** |
| External-only swarm memory | external memory common; explicit prohibition on native model memory as control-plane state not found as a standard pattern | **Combination candidate** |
| OBSERVED -> CANDIDATE -> VALIDATED -> DOCTRINE with role-separated promotion | reflection/knowledge validation/SOP antecedents; exact lifecycle not found | **Combination candidate** |
| Doctrine-first bootstrap; raw history only on demand | layered memory retrieval antecedents; exact governance ordering not found | **Combination candidate** |
| Provider admission control before model invocation with deterministic staggering | distributed admission/backoff patterns established; exact integration not found | **Combination candidate** |
| Exact-SHA reproducible role deployment packages | reproducible-build/supply-chain practice established; exact multi-agent role packaging not found | **Combination candidate** |

---

## 15. The strongest unresolved “distinctive conjunction”

The search did not locate one public system that clearly combines **all** of the following:

1. immutable project binding as the primary authorization namespace;
2. fresh per-agent execution-instance identity on spawn/recovery;
3. authority tier represented separately from capability set;
4. child capability inheritance restricted to equal-or-strict-subset, with self-escalation denied;
5. mutation rights dependent on a current active bound session, not merely possession of historical context/artifacts;
6. task/message/artifact/lease/audit records bound to project + execution identity, with stale-instance rejection;
7. cross-project exchange that carries information/provenance but explicitly carries **no execution authority** (`authority_conveyed=false`), followed by target-local acceptance;
8. immutable/sanitized copy-by-value knowledge transfer rather than a global mutable cross-project knowledge bus;
9. context modeling that explicitly separates **presence**, **evidence quality**, and **authority**;
10. external-only collective memory with raw experience -> candidate -> validated knowledge -> doctrine promotion under separated role authority;
11. bootstrap that prefers doctrine then scoped validated knowledge, loading raw history only on demand;
12. provider/start admission control before model invocation, including bounded concurrency, spacing/staggering, retry/backoff and occurrence identity;
13. exact-revision role packaging and reproducibility gates for deployable agent bundles.

This conjunction is the **highest-value object for further falsification**, not a confirmed novelty claim.

Important: several patents found contain large subsets of this list. The fact that no one reference obviously contains every item does not establish patentability; combination/obviousness analysis may combine multiple references.

---

## 16. What the investigation actively disproved

The following formulations should be treated as disproved or materially unsafe:

- “No one has built multi-agent orchestration like this.”
- “No one has built a generalist that calls specialists.”
- “Governed autonomous software agents are new.”
- “Human approval for agent actions is new.”
- “Role-based specialist agents are new.”
- “Agent memory/reflection is new.”
- “Agent identity, discovery and messaging are new.”
- “Policy-based agent authorization is new.”
- “Cross-domain agent delegation with policy/provenance is new.”
- “Auditability and provenance for agent actions are new.”

The investigation supports a more disciplined statement:

> “The constituent ideas have substantial prior art. The project may still be distinctive in the exact way it composes identity, authorization, cross-project non-authority, provenance, learning, lifecycle and reproducible deployment into one fail-closed agent mesh. No exact public match was located in this scan.”

---

## 17. Science fiction as conceptual input

Star Trek, Battlestar Galactica and related fiction can legitimately function as **mental-model sources**, for example:

- chain of command;
- specialist stations/roles;
- command authority vs technical expertise;
- escalation to specialists;
- compartmentalization;
- independent checks / civilian or command oversight;
- fail-safe and emergency modes;
- distributed crews pursuing a shared mission.

However, fiction is not strong technical prior-art evidence for implementation mechanisms unless a specific enabling disclosure is sufficiently concrete. It should not be used to establish novelty.

The credible interpretation is cognitive rather than legal: fictional organizational models may have helped the designer recognize a useful composition of real engineering patterns accumulated through prior professional experience.

---

## 18. Epistemic constraints

1. This was a broad web/standards/paper/patent scan, **not** an exhaustive professional prior-art search.
2. Patent searching was keyword/concept driven; CPC/IPC classification trees, backward/forward citation graphs, prosecution histories and non-English full-text families were not exhaustively traversed.
3. “No exact match found” is highly sensitive to terminology. Another system may implement materially equivalent semantics under different names.
4. Private/internal systems, unpublished applications, preprints not indexed, dissertations, standards drafts and commercial products may contain closer matches.
5. Patent **priority dates** matter. Publication in 2026 can still rely on earlier provisional/foreign priorities.
6. Patentability involves jurisdiction-specific law, claim language, anticipation and obviousness; this report makes no legal determination.
7. The project's own invention/implementation chronology has not been reconstructed claim-by-claim. A ten-year accumulation of experience is not the same thing as a ten-year priority date for a technical invention.
8. Public standards and frameworks are evolving rapidly in 2026; distinctiveness can shrink as the ecosystem converges.
9. Internal architecture documents describe target/in-progress behavior; an external novelty claim should distinguish implemented/tested invariants from aspirational architecture.
10. The active 2026-10-07 recommendation-pause directive permits assigned verification/research but this report intentionally does not promote new architecture recommendations.

---

## 19. Unresolved questions for PRIMARY/MANAGER validation

These are validation questions, not discretionary feature recommendations:

1. Which of the 13 conjunction elements in Section 15 are **implemented and tested today**, versus target architecture?
2. What is the earliest dated evidence for each allegedly distinctive invariant (commits, design notes, messages, prototypes)?
3. Which exact invariants are necessary to describe the system, and which are incidental implementation choices?
4. Does any single patent claim identified above read on the implemented system when mapped element-by-element?
5. Do combinations of `US20190068451A1`, `US12580768B2`, `US20250350644A1`, `US20260252697A1`, zero-trust/workload-identity standards, and modern orchestration frameworks make the unresolved combination technically obvious?
6. Does AGNTCY or another 2026 control-plane project implement stronger target-side authority non-conveyance than surfaced by this search?
7. Are there older security/distributed-computing systems that already use copy-by-value sanitized federation with receiving-domain reauthorization in an equivalent way?
8. Is the learning lifecycle truly specific to agents, or an application of established evidence-promotion / knowledge-management pipelines?
9. Is exact-SHA role packaging materially architectural, or simply application of reproducible-build and software-supply-chain practice?
10. What external claim language, if any, remains accurate after separating **component novelty** from **combination-level distinctiveness**?

---

## 20. Swarm learning candidate

**Candidate claim:**

> In governed multi-agent systems, apparent novelty often lies less in delegation, memory, specialist routing or policy controls individually than in the enforceable composition of identity, authorization, lifecycle, provenance, federation and learning boundaries. Broad novelty claims should be actively falsified at the component level before any combination-level distinctiveness is asserted.

**Evidence state:** CANDIDATE  
**Confidence:** high for the “components have prior art” portion; medium for “exact conjunction not found”; low/none for legal novelty.  
**Promotion:** requires MANAGER/REVIEWER falsification and PRIMARY acceptance under `protocols/swarm_learning.md`.

---

## 21. Primary source / identifier ledger

### Classical / academic

- Erman, Hayes-Roth, Lesser, Reddy (1980), *The HEARSAY-II Speech-Understanding System: Integrating Knowledge to Resolve Uncertainty*, DOI `10.1145/356810.356816`.
- Smith (1980), *The Contract Net Protocol: High-Level Communication and Control in a Distributed Problem Solver*, DOI `10.1109/TC.1980.1675516`.
- Shazeer et al. (2017), *Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer*, arXiv `1701.06538`.
- Wu et al., *AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation*, arXiv `2308.08155`.
- Hong et al., *MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework*, arXiv `2308.00352`, ICLR 2024.
- Fourney et al., *Magentic-One: A Generalist Multi-Agent System for Solving Complex Tasks*, arXiv `2411.04468`, MSR-TR-2024-47.
- Park et al., *Generative Agents: Interactive Simulacra of Human Behavior*, arXiv `2304.03442`, DOI `10.1145/3586183.3606763`.
- Packer et al., *MemGPT: Towards LLMs as Operating Systems*, arXiv `2310.08560`.
- Shinn et al., *Reflexion: Language Agents with Verbal Reinforcement Learning*, arXiv `2303.11366`.

### Standards / infrastructure

- OpenAI Agents SDK: `https://openai.github.io/openai-agents-python/`
- A2A specification: `https://a2a-protocol.org/dev/specification/`
- AGNTCY documentation: `https://docs.agntcy.org/`
- MCP authorization: `https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization`
- NIST SP 800-207: DOI `10.6028/NIST.SP.800-207`
- NIST AI Agent Standards Initiative: `https://www.nist.gov/news-events/news/2026/02/announcing-ai-agent-standards-initiative-interoperable-and-secure`
- SPIFFE standard: `https://spiffe.io/docs/latest/spiffe-specs/`
- Open Policy Agent: `https://www.openpolicyagent.org/docs`
- Cedar: `https://docs.cedarpolicy.com/`
- W3C PROV: `https://www.w3.org/TR/prov-overview/`
- Kubernetes controller pattern: `https://kubernetes.io/docs/concepts/architecture/controller/`
- OWASP Agent Control Standard: `https://genai.owasp.org/resource/agent-control-standard-acs/`

### Patent publications / families examined

- `US20190068451A1` — Policy Governed Software Agent System and Method of Operation — priority 2014-07-16.
- `US20250350644A1` — Method/Apparatus/System/Computer Program for Security Processing of Multi-Agent System — priority 2024-05-07.
- `US12580768B2` / `US20260019268A1` — Decentralized Persona Agent Governance in Regulated Environments Using LLMs — priority 2024-05-31; related parent family 2024-01-19.
- `US20250373432A1` — Federated Compliance-Token Inheritance / Digital Artifact Registry.
- `US20250244964A1` — Methods for Implementing AI Capabilities in Software Applications.
- `US20250259043A1` — Platform for Orchestrating Fault-Tolerant, Security-Enhanced Networks of Collaborative and Negotiating Agents.
- `US20250373451A1` — Trust-Enabled AI and Non-Human Identity Orchestrator Framework.
- `US20250315514A1` — Cross-Domain Authorization / Cross-Domain Call — prior art date 2021-08-27.
- `US20260252697A1` — Systems and Methods for Governed Execution of Assistant Mediated Systems Across Heterogeneous Nodes — PCT family shows priority 2025-01-09.
- `CN121997321A` — Authority-Boundary-Oriented Intelligent Agent Sensitive Operation Tracking — 2026-04-09.

Patent search roots: `https://patents.google.com/` and public family metadata.

---

## 22. Closure

This investigation has done what a novelty-falsification pass is supposed to do: it **made the claim smaller and stronger**.

The project is not unprecedented because it has multiple agents, specialists, memory, policy gates, human approval, identity, delegation, federation, or audit. Those ideas have deep prior art and, in several cases, very close patent overlap.

The unresolved technical question is whether the project's **full governance composition** — especially project-bound authority, fresh execution identity, non-escalating capabilities, explicit non-conveyance of authority across projects, target-side reacceptance, copy-by-value sanitized intelligence exchange, context evidence/authority separation, staged externally persisted learning, and reproducible role packaging — constitutes a materially distinctive system when compared element-by-element with the closest public references.

Until that is validated, the correct swarm posture is:

**component novelty rejected; combination distinctiveness plausible but unproven; legal novelty unknown.**
