# Bootstrap Continuity Restoration and Speaker Claim Protocol

Status: ACTIVE PROJECT-LOCAL CONTROL
Project: `intercommunicationsenhancements`
Authorization case for first installation: `AUTH-IEP-20261010-2117-BOOTSTRAP-CONTINUITY-SPEAKER`

## Purpose

Immediately after `AGENT_BOOTSTRAP.json` loads, restore externally persisted project continuity before ordinary context/handoff recovery, then establish the current speaker as an explicit non-authoritative identity claim.

This protocol does not modify provider/model memory and does not grant restored context, a voice characteristic, a speaker claim, or an audit record mutation authority.

## Mandatory order

1. Load `AGENT_BOOTSTRAP.json`.
2. Execute continuity restoration from authorized external project records.
3. Emit a restoration attestation.
4. Ask the current person, without suggesting an answer: `What is your name?`
5. Record the supplied name as `CLAIMED_NOT_AUTHENTICATED` in the append-only speaker audit table.
6. Continue to the next normal bootstrap step only after the restoration phase and speaker-claim phase have completed or have failed closed for their affected branch.

This phase is logically between bootstrap order step 8 (`load_local_agent_bootstrap`) and step 9 (`load_fresh_agent_context_reference`).

## Continuity rules

- Native ChatGPT memory is never a swarm-state source or fallback.
- External records must carry a project identity and source class.
- A project mismatch returns `IDENTITY_CONFLICT` for the affected restoration branch.
- Missing required sources remain missing; they are not reconstructed from recollection.
- Host/session context may be orientation only.
- `RESTORED_CONTEXT != AUTHORIZATION`.
- Every restoration attestation reports `authority=NONE` and `mutation_authority=false`.

## Speaker claim rules

The active speaker claim is intentionally replaceable. Historical speaker-claim records are append-only.

At startup the system asks exactly or equivalently:

`What is your name?`

The prompt must not include a suspected or expected name. In particular, do not ask `Are you Robert?`, `Is this Robert Leonard?`, or any equivalent leading identity prompt.

A supplied name establishes only a claim:

- status: `CLAIMED_NOT_AUTHENTICATED`
- authentication effect: `NONE`
- authorization effect: `NONE`
- mutation authority: `false`

A correct registered name is still not authentication. Authority-sensitive work continues to use the independent authentication and single-use authorization controls already defined by the project.

## Vocal modulation / possible speaker change

The runtime in this repository does not claim to perform biometric speaker recognition. It accepts a host/runtime signal that vocal characteristics materially changed or that a speaker change is otherwise suspected.

When either signal is received:

1. mark the current active speaker claim uncertain by clearing the active binding;
2. pause only work whose safety depends on knowing the current speaker;
3. ask `What is your name?` without providing a candidate answer;
4. append the new supplied claim to the speaker audit table;
5. replace the active speaker binding with the new claim;
6. preserve all earlier speaker records unchanged.

Voice characteristics are a re-identification trigger only. They are never identity proof.

## Speaker audit table

Reference runtime: `org_agent_mesh.bootstrap_continuity.SpeakerClaimAuditTable`.

The reference table is hash-chained JSONL and appends one record per claim. Each record includes:

- event ID;
- project ID;
- session ID;
- UTC timestamp;
- claimed name;
- trigger reason;
- claim status;
- explicit `voice_signal_is_identity_proof=false`;
- authentication effect;
- authorization effect;
- mutation-authority flag;
- previous event hash;
- event hash.

The active speaker may change; prior audit rows may not be silently rewritten by this runtime.

The audit table itself is evidentiary/non-authoritative. The storage location supplied by a host does not become canonical swarm authority merely because this runtime can append to it. Existing persistence and mutation-authorization rules remain applicable to any external durable sink.

## Failure behavior

- Unknown/native memory source: deny affected restoration branch.
- Project identity conflict: return `IDENTITY_CONFLICT`; do not guess through it.
- Missing required source: return `CANONICAL_SOURCE_MISSING`.
- Empty speaker response: do not create a speaker claim.
- Voice-change signal with no new name yet: current speaker remains unbound/uncertain for identity-dependent work.
- Unrelated safe work may continue where existing continuation policy permits.

## Authority invariants

`VOICE_SIGNAL != IDENTITY_PROOF`

`NAME_CLAIM != AUTHENTICATION`

`AUTHENTICATION != AUTHORIZATION`

`PERSISTENCE_CAPABILITY != MUTATION_AUTHORITY`

`RESTORED_CONTEXT != AUTHORIZATION`
