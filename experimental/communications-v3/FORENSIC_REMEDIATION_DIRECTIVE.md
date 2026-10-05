# Behavior-Preserving Forensic Remediation Directive

Status: **DRAFT / EXPERIMENTAL / DO NOT EXECUTE AGAINST MAIN WITHOUT SEPARATE AUTHORIZATION**

## Mission

Strengthen the assurance substrate of the Organization Agent Mesh without weakening or rewriting legitimate swarm behavior.

The target chain is:

`human intent → requirement → invariant → implementation → test → adversarial validation → independent review → authorization → preventive enforcement → controlled execution → observed postcondition → durable audit / rollback`

The implementation principle is:

> **Patch the holes without poisoning the swarm. Move enforcement outward before moving intelligence inward.**

## Evidence discipline

Every remediation decision must label its basis as `OBSERVED`, `INFERRED`, `CLAIMED`, or `UNKNOWN`.

Do not convert another reviewer's tooling limitation into a system defect. In particular, an independent reviewer that could not access live GitHub metadata correctly downgraded its own conclusions; that limitation should not be treated as evidence that repositories or controls do not exist.

Likewise, communication-hardening recommendations written before direct AgentBus inspection are design leads, not proof of current absence.

The current bus has now been directly inspected and already provides:

- active `AgentSession` requirement for publication;
- `PUBLISH_MESSAGE` capability checking;
- sender logical-agent and execution-instance binding;
- same-project-only internal delivery;
- explicit cross-project exclusion;
- idempotency identity;
- correlation and causation IDs;
- expiry;
- append-only atomic file creation;
- quarantine behavior;
- bounded delivery retry states.

Preserve those controls.

## Non-negotiable swarm compatibility

A remediation MUST NOT, unless a separately demonstrated defect demands it:

1. change the USER > MASTER > PRIMARY > SUBORDINATE lifecycle hierarchy;
2. convert MASTER lifecycle control into source-write authority;
3. reduce PRIMARY's legitimate in-project execution authority;
4. grant MANAGER or RESEARCH new mutation authority;
5. weaken project isolation;
6. route cross-project writes through the internal message bus;
7. let learning, consensus, telemetry, evidence status, or messages mint authority;
8. let automation enable a disabled swarm schedule;
9. treat human status/progress questions as cancellation;
10. permit STOP to be silently undone by scheduler/liveness recovery;
11. turn `UNKNOWN_EFFECT` into automatic retry;
12. replace authoritative project state with a communication log;
13. require agents to disclose private chain-of-thought.

## Solution plan

### R1 — Restore semantic contract coherence before hardening promotion

The current central exact-SHA suite is red because the user-control entrypoint now expresses a stronger lifecycle-aware resume rule while a validator/test still expects the older exact token.

Do not revert the stronger behavior just to make a literal string assertion green.

Normalize the invariant as:

> A status/progress/explanation message receives an immediate response, preserves the active assignment, and automatically resumes work unless the message itself validly changes supervisory control state.

Then align protocol, machine entrypoint, validator, and tests semantically.

Acceptance:
- complete suite green at one exact SHA;
- status/progress request resumes;
- STOP/PAUSE/REDIRECT still override continuation when valid;
- no routine continue reprompt is introduced.

### R2 — Close the canonical promotion boundary externally

After a green baseline exists, require the appropriate exact-SHA integrated checks through GitHub rulesets/branch protection on each repository.

This is an external enforcement task, not a reason to restrict swarm reasoning.

Require repo-specific checks rather than copying one universal status-check list blindly.

Negative tests must prove:
- direct unauthorized push denied;
- red required check cannot promote;
- skipped required check cannot promote;
- force-push/delete denied unless a documented emergency path applies;
- automation/bot bypass matches explicit policy.

### R3 — Separate human root identity from automation identity

Keep human root authority intact.

Use distinct automation principals for routine bots/agents. Automation credentials should be repo-scoped, least-privilege, and unable to alter/bypass their own governing rules.

A GitHub username equality check is useful attribution, but it is not by itself fresh human-presence proof when automation can act under the same principal.

### R4 — Authenticate authority issuance without changing role semantics

The current control plane correctly requires an active bound session and prevents child capability expansion, but `ProjectBinding` remains an ordinary trusted-process object.

Do not redesign the role model.

Instead, make the minting boundary explicit:
- trusted broker/control-plane service issues bindings or session attestations;
- model/agent code requests authority but cannot construct authoritative credentials itself;
- child authority remains a strict subset;
- project/repository identity remains exact.

Apply the same principle to supervisory identity.

### R5 — Strengthen messages by extending v2, not replacing it

Introduce communications v3 as an experimental overlay with:

- authenticated sender principal attestation;
- explicit role binding to the authenticated principal;
- canonical payload digest;
- asymmetric signature support where trust separation requires it;
- message class separation: `CONTENT`, `CONTROL`, `ACK`, `HANDOFF`, `EVIDENCE`;
- explicit epistemic status: `OBSERVED`, `INFERRED`, `CLAIMED`, `UNKNOWN`;
- governance/policy revision binding;
- lease/fence context when a message claims mutation-relevant state;
- Lamport/logical clock in addition to UTC timestamp;
- per-stream hash linking plus externally anchored checkpoints;
- durable replay/ack bookkeeping;
- content-addressed handoff state plus receiver acknowledgement.

Important: a signature proves origin/integrity. It does **not** create authority. Receivers must still evaluate role/capability/project/lifecycle policy.

### R6 — Bind claimed role to authenticated session

Current v2 publication validates the claimed logical agent and execution-instance ID against the active session. It does not independently bind the free-form `from_role` field to that session.

v3 should make role a broker-attested principal claim, not merely message content.

During compatibility mode, reject role claims that disagree with the project routing/role registry for the authenticated session where that mapping is available.

### R7 — Make delivery state durable

Current `DeliveryLedger` is process-local.

Do not change delivery semantics; preserve existing states and bounded retry behavior.

Back the ledger with the existing durable-state substrate or an equivalent atomic backend so these survive restart:
- registration/idempotency;
- acknowledgement state;
- attempt count;
- replay/nonce consumption;
- rejection/quarantine state;
- terminal completion.

### R8 — Separate lifecycle commands from arbitrary content

Peer/research content must remain data, not executable authority.

Lifecycle commands (`CONTINUE`, `REDIRECT`, `PAUSE`, `STOP`, `STOP_TREE`) should use a typed control envelope verified against supervisory authority.

Do not parse ordinary research prose for executable control instructions.

Human messages are still interpreted through the existing user-control semantics; v3 only makes the resulting lifecycle command explicit and attributable.

### R9 — Authenticate cross-project approvals without weakening the boundary

Keep the internal bus same-project-only.

For explicit cross-project exchange, replace/augment free-form approver attribution with an authenticated approval object bound to:
- exchange ID;
- source/destination project;
- artifacts/digests;
- permitted use;
- expiry;
- approver principal;
- applicable policy revision.

Cross-project exchange remains copy/reference by explicit protocol. It must not become ambient cross-project write authority.

### R10 — Improve consequence authorization at the substrate

Preserve the existing exact-action, fence, epoch, precondition, quarantine and `UNKNOWN_EFFECT` semantics.

Strengthen them by:
- asymmetric signer/verifier separation where required;
- durable atomic grant consumption/revocation/cancellation;
- binding authorization to the exact immutable serialized outbound payload;
- independent target postcondition observation for consequential effects where feasible.

Sequence:

`PREPARE → AUTHORIZE → REVALIDATE → TRANSMIT EXACT AUTHORIZED PAYLOAD → OBSERVE TARGET → VERIFY POSTCONDITION → RECEIPT`

### R11 — Make communication history tamper-evident without creating a new source of truth

Do not replace the canonical forum, accepted state, task registry, or source repository with a blockchain-like log.

Instead:
- hash-link messages within deterministic writer/stream partitions;
- create periodic checkpoint roots over accepted message digests;
- anchor those checkpoints in a protected, independently verifiable location;
- preserve correlation/causation and add logical ordering;
- allow forensic replay to verify history consistency.

The log proves history integrity; it does not decide project truth or authority.

### R12 — Require evidence labels in communication, but never treat them as authority

v3 evidence-bearing messages should label statements as:
- `OBSERVED`;
- `INFERRED`;
- `CLAIMED`;
- `UNKNOWN`.

Evidence pointers may reference commit SHA, CI run, artifact digest, message ID, test output, or other authorized evidence.

Repeated forwarding does not increase epistemic status.

### R13 — Make handoffs proof-carrying

Extend existing handoff behavior rather than replacing `MASTER_HANDOFF.json`.

A v3 handoff should bind:
- exact project;
- sender instance;
- receiver or receiver role;
- state capsule digest;
- source revision;
- assignment revision;
- lease/fence context where relevant;
- unresolved blockers;
- evidence references;
- expiry;
- acknowledgement requirement.

Receiver acknowledgement confirms receipt/acceptance only; it cannot expand the receiver's authority.

### R14 — Preserve backward compatibility

Migration must be staged:

1. v3 parser/verifier in shadow mode;
2. dual-write optional v2 + v3 envelopes for selected non-authoritative traffic;
3. forensic comparison/replay;
4. v3-native acknowledgements;
5. v3 control messages only after authority tests pass;
6. no production default change until independent review and explicit promotion.

No existing v2 message should become invalid solely because v3 exists.

## Required adversarial tests

At minimum:

- forged sender instance;
- correct instance with forged role;
- forged/unknown signing key;
- valid signature but wrong project;
- valid signature but insufficient capability;
- valid signature but stale lease/fence;
- replay before and after process restart;
- duplicate delivery during scheduler retry;
- message payload altered after signing;
- evidence label upgraded without new evidence;
- peer content attempting lifecycle command injection;
- STOP then process restart;
- STOP then scheduler restart;
- handoff state digest mismatch;
- acknowledgement by wrong instance;
- cross-project approval forged or replayed;
- stale policy revision;
- rollback to weaker protocol;
- log-chain deletion/reordering;
- checkpoint mismatch;
- compatibility read of existing v2 messages.

## Promotion rule

Nothing in communications v3 becomes authoritative because it is sophisticated, signed, tested, or agreed upon by multiple agents.

Promotion requires the normal chain:

`intent → requirement → tests → independent review → human authorization where required → server/host enforcement → controlled rollout → observed postconditions`.
