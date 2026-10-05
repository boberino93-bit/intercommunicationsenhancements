# Communications v3 — Experimental Design Branch

Status: **EXPERIMENTAL / NON-AUTHORITATIVE**

Base revision: `1eb8e32b936d0fe534f68e26dc2af71f845df1ba`

This directory explores the next generation of Organization Agent Mesh communication without changing the active v2 runtime, project authority model, swarm roles, scheduling semantics, or production bootstrap.

## Preservation contract

The experiment MUST preserve these existing invariants:

1. Project identity is resolved before mutation.
2. Internal message traffic remains project-scoped; cross-project exchange continues through an explicit exchange protocol.
3. Messages do not create authority.
4. MASTER lifecycle authority does not imply cross-project source-write authority.
5. PRIMARY remains the project-local execution authority defined by existing governance.
6. MANAGER and RESEARCH retain their current role ceilings.
7. Human-only schedule activation remains human-only.
8. A status/progress/explanation request is not cancellation; work resumes unless valid lifecycle control changes state.
9. STOP remains distinct from DELETE and must not be silently undone by liveness/scheduler recovery.
10. `UNKNOWN_EFFECT` must never become blind retry.
11. Learning, observations, evidence labels, consensus, and message repetition cannot mint authority.
12. Existing v2 messages remain readable during migration.

## Why v3

The current v2 bus already provides valuable controls: active-session publication authority, project isolation, agent-instance matching, idempotency identity, correlation/causation identifiers, expiry, append-only atomic file creation, and explicit delivery acknowledgement states.

The next generation should strengthen the trust substrate around those controls rather than replace them.

Primary design goals:

- bind sender role/principal claims to authenticated session authority;
- make message integrity and provenance independently verifiable;
- separate control commands from peer/research content;
- make delivery/replay/revocation bookkeeping durable;
- carry explicit `OBSERVED` / `INFERRED` / `CLAIMED` / `UNKNOWN` epistemic labels;
- content-address handoffs and acknowledgements;
- preserve causal order without relying exclusively on wall-clock timestamps;
- support forensic replay and externally anchored checkpoints;
- provide a backward-compatible v2 → v3 migration path.

## Non-goals

This experiment does **not**:

- change production `main`;
- enable schedules;
- create new authority roles;
- allow cross-project writes through the internal bus;
- alter current role capabilities;
- require agents to expose private chain-of-thought;
- treat signatures as permission by themselves;
- replace source-of-truth project state with the message log;
- use company/employer data.

## Files

- `FORENSIC_REMEDIATION_DIRECTIVE.md` — behavior-preserving remediation message for a future implementation master.
- `PROTOCOL.md` — v3 protocol design.
- `message_v3.schema.json` — initial experimental schema.
- `TEST_PLAN.md` — adversarial and compatibility acceptance plan.
- `MIGRATION.md` — staged v2 → v3 migration approach.

Nothing in this directory is production authority until separately reviewed, tested, authorized, and promoted through the normal governance chain.
