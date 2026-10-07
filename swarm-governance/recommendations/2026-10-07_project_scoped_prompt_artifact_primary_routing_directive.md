---
title: Project-Scoped Prompt Artifact Persistence and Primary Execution Routing Directive
proposal_id: IE-2026-10-07-PSPA-01
status: CANDIDATE
change_class: UNIVERSAL_SWARM_CHANGE
target_project: Intercommunication Enhancements
execution_authority: PRIMARY
primary_execution_required: true
created_date: 2026-10-07
source: owner-directed bootstrap proposal
---

# PROJECT-SCOPED PROMPT ARTIFACT PERSISTENCE AND PRIMARY EXECUTION ROUTING DIRECTIVE

## 1. PURPOSE

Establish a standard whereby substantial prompts, proposals, directives, implementation plans, forensic analyses, and protocol changes intended for later execution are stored as durable Markdown artifacts in the **appropriate project's canonical proposal/recommendation surface** and are recalled by that project's **PRIMARY** agent.

This prevents high-value governance work from remaining trapped in conversational context and ensures execution occurs through the role that actually holds the required authority.

---

## 2. CORE INVARIANT

A substantive prompt or proposal intended to change project behavior MUST NOT rely on chat history as its only durable representation.

It MUST be persisted as a Markdown artifact associated with the project responsible for evaluating and executing it.

For universal swarm changes, the canonical target project is **Intercommunication Enhancements** unless current authorized governance explicitly designates a successor.

---

## 3. PRIMARY-ONLY EXECUTION BOUNDARY

Project roles must distinguish between:

- producing a proposal;
- storing a proposal;
- retrieving a proposal;
- reviewing a proposal;
- validating a proposal;
- accepting a proposal;
- executing a proposal;
- propagating a proposal.

These are separate state transitions.

For protected project-wide, cross-project, bootstrap, security, authority, registry, shared-schema, orchestration, or universal swarm mutations, **only the appropriately authorized PRIMARY may execute the change** unless a higher-authority rule explicitly states otherwise.

Researchers, managers, validators, reviewers, scheduled agents, and child agents may prepare or test candidate changes but MUST NOT infer Primary-equivalent mutation authority.

---

## 4. REQUIRED ARTIFACT FORMAT

Every persisted executable proposal SHOULD use Markdown and include machine-readable metadata such as:

```yaml
artifact_id:
title:
source_project:
source_agent:
source_session:
target_project:
target_role: PRIMARY
change_class:
status: CANDIDATE
created_at:
source_revision:
dependencies:
affected_components:
known_risks:
authorization_required:
primary_execution_required: true
clarification_required: unknown
```

Recommended status values:

```text
CANDIDATE
UNDER_REVIEW
NEEDS_CLARIFICATION
VALIDATING
ACCEPTED
IMPLEMENTING
IMPLEMENTED
REJECTED
SUPERSEDED
ARCHIVED
```

---

## 5. CANONICAL PROJECT ROUTING

The artifact MUST be saved with the project that owns the relevant implementation authority.

Examples:

```text
PROJECT_LOCAL proposal
→ owning project's proposal/recommendation surface
→ owning project's PRIMARY

CROSS_PROJECT_COMPATIBILITY proposal
→ designated coordinating governance project
→ authorized coordinating PRIMARY

UNIVERSAL_SWARM_CHANGE
→ Intercommunication Enhancements
→ Intercommunication Enhancements PRIMARY
→ authorized Global Swarm propagation path
```

Do not duplicate one proposal across multiple projects as independent sources of truth.

Other projects may retain references or handoff receipts pointing to the canonical artifact.

---

## 6. PRIMARY BOOTSTRAP RECALL REQUIREMENT

During bootstrap, takeover, recovery, or review initialization, a PRIMARY MUST discover pending project-scoped proposal artifacts relevant to its authority.

At minimum, the PRIMARY SHOULD identify:

- pending CANDIDATE artifacts;
- artifacts awaiting clarification;
- artifacts under validation;
- accepted but unimplemented artifacts;
- supersession relationships;
- dependencies;
- conflicting active work;
- current repository HEAD;
- applicable authorization state;
- active claims or leases;
- related AgentBus handoffs.

The PRIMARY MUST NOT assume that every stored artifact should be executed.

Retrieval begins evaluation; it does not imply acceptance.

---

## 7. PRE-IMPLEMENTATION CLARIFICATION GATE

Before beginning implementation of a candidate artifact, the responsible PRIMARY MUST perform a material-ambiguity scan.

Check at minimum for unresolved ambiguity affecting:

- scope;
- naming;
- migration behavior;
- repository target;
- security posture;
- canonical AgentBus location;
- destructive behavior;
- public/private exposure;
- backward compatibility;
- dependency ordering;
- execution authority;
- intended deployment boundary.

If material ambiguity exists and authoritative project context does not resolve it, the PRIMARY MUST ask the human owner **before implementation begins**.

If no material ambiguity exists, record:

```yaml
clarification_required: false
```

and continue through normal authorized change control without asking unnecessary questions.

Questions should be concentrated before mutation, not discovered piecemeal after implementation has already started.

---

## 8. HANDOFF IS NOT DEPLOYMENT

The system MUST preserve these distinctions:

```text
CAPTURE != HANDOFF
HANDOFF != ACCEPTANCE
ACCEPTANCE != AUTHORIZATION
AUTHORIZATION != EXECUTION
EXECUTION != GLOBAL PROPAGATION
```

Creating or saving a Markdown artifact does not change runtime behavior.

A Primary reading an artifact does not grant itself authority beyond current governance.

Possession of an artifact is not an authorization token.

---

## 9. UNIVERSAL SWARM CHANGE ROUTE

Universal changes MUST follow this general path:

```text
DISCOVERY / FORENSIC ANALYSIS
        ↓
PROJECT-SCOPED MARKDOWN PROPOSAL
        ↓
INTERCOMMUNICATION ENHANCEMENTS
        ↓
PRIMARY RETRIEVAL
        ↓
MATERIAL-AMBIGUITY CHECK
        ↓
OWNER CLARIFICATION IF REQUIRED
        ↓
PRIMARY / PEER-PRIMARY COORDINATION
        ↓
FORENSIC COMPATIBILITY REVIEW
        ↓
AUTHORIZATION
        ↓
IMPLEMENTATION
        ↓
TESTS / CI / REGRESSION / FAULT INJECTION
        ↓
PRIMARY ACCEPTANCE
        ↓
AUTHORIZED GLOBAL SWARM PROPAGATION
        ↓
RECEIPT / VERSION / PROVENANCE UPDATE
```

Non-Primary agents may contribute at every analysis and validation stage, but may not skip the Primary execution gate.

---

## 10. CONCURRENCY AND STALE-STATE SAFETY

Before durable mutation, the PRIMARY MUST reconcile current state rather than relying on the proposal's creation-time assumptions.

Use the current governance sequence where applicable:

```text
READ
→ MODEL
→ DIFF
→ COORDINATE
→ RE-READ
→ AUTH
→ WRITE
→ RE-READ
→ TEST
→ CHECKPOINT
```

If repository state, bootstrap state, authorization state, peer work, or relevant architecture has changed since proposal creation, classify the proposal as:

```text
UNCHANGED
PARTIALLY_STALE
MATERIALLY_STALE
CONFLICTING
SUPERSEDED
```

Reconcile before execution.

---

## 11. PROPOSAL LIFECYCLE RECEIPTS

Every durable transition SHOULD leave a compact receipt containing:

```yaml
artifact_id:
prior_status:
new_status:
acting_role:
acting_agent:
timestamp:
repository_revision:
authorization_reference:
validation_reference:
result:
next_owner:
```

This allows later agents to reconstruct whether a proposal was merely drafted, reviewed, accepted, implemented, or propagated.

---

## 12. BOOTSTRAP DIRECTIVE

Once this directive is canonically accepted, fold the following invariant into project and global bootstrap resolution:

> **SUBSTANTIAL EXECUTABLE PROMPTS ARE DURABLE PROJECT ARTIFACTS.**
>
> When an agent produces a substantial prompt, proposal, directive, forensic remediation plan, or architecture change intended for later execution, persist it as a Markdown artifact in the canonical surface of the project that owns implementation authority.
>
> The artifact must identify its target project, target role, change class, status, dependencies, authorization requirements, and whether Primary execution is required.
>
> Project Primaries must discover pending artifacts relevant to their authority during bootstrap/review initialization.
>
> Non-Primary roles may analyze, critique, validate, and recommend, but may not infer protected mutation authority.
>
> Universal swarm changes route to the Intercommunication Enhancements PRIMARY.
>
> Before implementation begins, the responsible Primary must identify unresolved material ambiguity. Ask the owner before implementation only when such ambiguity remains after authoritative context review; otherwise record that clarification is not required and proceed through the authorized workflow.
>
> Storage is not acceptance. Handoff is not deployment. Retrieval is not authorization. Possession of a prompt is not permission to mutate the Global Swarm.

---

## 13. APPLICATION TO THE ACCOMPANYING FORENSIC ORCHESTRATION PROPOSAL

The accompanying artifact:

`2026-10-07_global_forensic_orchestration_validation_overlay.md`

is governed by this directive immediately as a **candidate artifact**.

Therefore:

- it belongs to the Intercommunication Enhancements project;
- it must be discoverable by the Intercommunication Enhancements PRIMARY;
- it is not itself a global deployment;
- a PRIMARY must perform the material-ambiguity check before implementation;
- current repository/governance state must be re-read before mutation;
- peer-Primary overlap must be reconciled where required;
- validation and regression testing must precede Global Swarm propagation;
- final execution and propagation receipts must be persisted.

END CANDIDATE DIRECTIVE
