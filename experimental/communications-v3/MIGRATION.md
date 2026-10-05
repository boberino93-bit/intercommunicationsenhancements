# Communications v2 → v3 Experimental Migration Plan

Status: **DRAFT / NON-AUTHORITATIVE**

The migration is designed to prevent a security upgrade from destabilizing swarm behavior.

## Principle

Do not flip the swarm from v2 to v3.

Introduce v3 as an observable, reversible overlay and increase authority only after evidence supports each stage.

## Stage 0 — Baseline repair

Before v3 affects any runtime behavior:

- repair the current user-control semantic contract mismatch on a separate authorized path;
- establish a fully green exact-SHA integrated baseline;
- record current v2 behavioral tests;
- record current project/role/scheduling/lifecycle invariants.

v3 must not be used to hide or bypass an existing red baseline.

## Stage 1 — Parser/schema only

Add v3 schema and parser behind an experimental flag.

Allowed:
- construct test envelopes;
- parse/validate local fixtures;
- run adversarial tests.

Forbidden:
- production publication;
- lifecycle effects;
- replacing v2 storage;
- changing packages/bootstraps by default.

Exit evidence:
- schema conformance vectors;
- unknown-field rejection;
- canonicalization vectors;
- project-isolation tests.

## Stage 2 — Shadow envelope generation

For selected test/non-authoritative v2 CONTENT messages, generate a linked v3 shadow envelope.

The v2 message remains canonical for current runtime behavior.

Shadow envelope contains:
- v2 message ID/reference;
- normalized sender identity claims;
- canonical payload digest;
- logical clock/stream data;
- epistemic claim labels where available.

Do not sign with production authority keys yet unless the signing broker itself is under test.

Compare:
- semantic equivalence;
- serialization determinism;
- causal linkage;
- replay detection.

## Stage 3 — Session-attested v3 content

Enable authenticated/session-attested v3 `CONTENT` and `EVIDENCE` on an experimental path.

Requirements:
- principal/session attestation issued outside model-controlled construction;
- role binding checked against trusted routing/session state;
- same-project isolation retained;
- v2 path remains available for rollback.

No CONTROL authority yet.

## Stage 4 — Durable delivery ledger

Integrate v3 delivery/nonce/ACK state with a durable atomic backend.

Prove:
- replay rejection survives process restart;
- retry count survives restart;
- terminal ACK remains terminal;
- concurrent delivery has one effective result;
- quarantine state cannot be erased by restart.

Only after this stage may v3 be considered for mutation-relevant control traffic.

## Stage 5 — Proof-carrying handoffs

Introduce v3 HANDOFF in parallel with existing `MASTER_HANDOFF.json` behavior.

The existing master handoff remains the continuity index.

v3 adds:
- state capsule digest;
- sender principal/instance proof;
- intended receiver;
- assignment/source revision binding;
- explicit acceptance ACK.

Verify that receiver acceptance does not transfer leases/capabilities outside existing authority.

## Stage 6 — Typed lifecycle control in shadow mode

Translate existing valid supervisory decisions into v3 CONTROL envelopes **after** the decision has already been authorized by the current supervision path.

Purpose: compare representations and replayability.

The v3 control envelope is not yet the authority path.

Test:
- STOP;
- STOP_TREE;
- PAUSE;
- CONTINUE;
- REDIRECT;
- restart durability;
- stale assignment revision;
- foreign project control;
- subordinate forgery.

## Stage 7 — v3-native lifecycle control candidate

Only after independent review may v3 CONTROL become an accepted transport for already-defined supervisory authority.

It must not change who is allowed to control whom.

Requirements:
- authenticated supervisor principal;
- durable decision/STOP state;
- replay protection;
- exact target binding;
- policy revision binding;
- current authority revalidation at receive time.

Human-only schedule activation remains outside this privilege. A MASTER CONTROL message cannot enable a disabled schedule.

## Stage 8 — Tamper-evident checkpoints

Add per-stream digest chaining and periodic checkpoint roots.

Start with internal verification.

Later, if high assurance is required, anchor checkpoint digests in a location not writable by ordinary swarm identities.

Do not make the log a second accepted-state authority.

## Stage 9 — Cross-project approval profile

Upgrade the explicit cross-project exchange protocol to authenticated approvals.

Do not route cross-project exchange through the same-project bus.

Run negative tests for:
- forged approver;
- wrong exchange;
- changed artifact digest;
- expiry;
- replay;
- scope expansion.

## Stage 10 — Consequence-link profile

Allow messages to reference prepared-action/grant/receipt IDs while retaining the consequence gateway as the only effect-authority boundary.

Messages must never execute consequential actions merely because they are signed.

## Stage 11 — Candidate package integration

Only after the v3 experiment is stable:

- add v3 files to package dependency closure intentionally;
- verify semantic dependency closure;
- build role packages at exact SHA;
- reproduce independently;
- run old + new suites together.

## Stage 12 — Controlled promotion

Production default may change only after:

1. exact-SHA full suite green;
2. independent implementation review;
3. independent architecture/adversarial review;
4. behavior-preservation evidence;
5. human authorization for governance/promotion;
6. GitHub/server enforcement prevents bypass;
7. rollback is tested;
8. deployment postconditions are observed.

## Rollback contract

Every stage must support rollback to the prior stage without:

- invalidating historical v2 messages;
- silently re-enabling schedules;
- losing STOP state;
- changing role capability ceilings;
- replaying previously consumed controls/effects;
- transferring authority between projects.

If rollback would lose replay/STOP state, rollback is blocked until state is reconciled and migrated safely.
