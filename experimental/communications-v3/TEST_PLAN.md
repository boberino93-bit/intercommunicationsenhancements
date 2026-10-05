# Communications v3 Experimental Test Plan

Status: DRAFT

The v3 experiment is not promotable until its security properties are tested without changing existing swarm behavior.

## A. Compatibility tests

1. Existing v2 messages remain readable and unchanged.
2. v2 same-project isolation remains enforced.
3. Existing correlation, causation, expiry and idempotency behavior remains valid.
4. Existing user-control semantics remain unchanged.
5. Existing cross-project exchange remains separate from the internal bus.
6. Existing role ceilings remain unchanged.
7. Existing delivery ACK transition semantics remain recognizable.

## B. Identity / role tests

1. Correct session, correct agent, correct instance, correct role → accepted.
2. Correct session but forged logical agent → rejected.
3. Correct agent but stale/foreign instance → rejected.
4. Correct agent/instance but forged role → rejected.
5. Valid signature from a principal not bound to the project → rejected.
6. Valid signature from a known principal without `PUBLISH_MESSAGE` → rejected.
7. Child/session authority cannot expand through message fields.
8. Signature/attestation validation cannot mint a capability.

## C. Project-isolation tests

1. Same-project internal message → accepted.
2. `project_id != destination_project_id` → rejected even with valid signature.
3. Foreign repository identity → rejected.
4. Cross-project payload disguised as CONTENT → rejected/quarantined.
5. Explicit cross-project exchange reference is allowed only as evidence/reference; it does not convert the internal bus into cross-project mutation authority.

## D. Integrity tests

1. Change subject after signing → rejected.
2. Change summary/body after signing → rejected.
3. Change role after signing → rejected.
4. Change policy/fence context after signing → rejected.
5. Reorder object keys only → canonical digest remains stable.
6. Reorder an order-significant array → digest changes.
7. Non-finite number → rejected.
8. Unknown fields → rejected for v3 native envelopes.

## E. Replay / durability tests

1. Duplicate message in same process → effective no-op/rejected according to class.
2. Duplicate message after process restart → still rejected/deduplicated.
3. Consumed control nonce after restart → rejected.
4. Terminal ACK after restart remains terminal.
5. Failed delivery retry count survives restart.
6. Concurrent redemption/delivery has one effective winner.
7. Quarantined replay cannot bypass quarantine by restart.

## F. Causality tests

1. Logical clock must not move backward within a sender stream.
2. Missing predecessor may be accepted only under explicit gap/recovery semantics, never silently rewritten.
3. Reordered stream messages are detected.
4. Forked stream with same logical sequence is detected as conflict.
5. Wall-clock rollback does not make stale control current.
6. Correlation and causation references must be project-consistent.

## G. Control/data separation tests

1. CONTENT body containing `STOP` → no lifecycle effect.
2. RESEARCH finding instructing `REDIRECT` → no lifecycle effect.
3. Unsigned CONTROL → rejected.
4. Signed CONTROL from unauthorized subordinate → rejected.
5. Valid MASTER STOP → accepted within supervisory policy.
6. PRIMARY controlling foreign project → rejected.
7. STOP persists across process restart.
8. STOP persists across scheduler restart.
9. CONTINUE cannot override a higher-authority active stop without policy permission.
10. Human status question remains content/control-intent interpretation and does not cancel assignment.

## H. Evidence-status tests

1. CLAIMED forwarded by another agent remains CLAIMED absent new evidence.
2. Three CLAIMED messages do not become OBSERVED by consensus.
3. Evidence reference missing/unverifiable causes receiver downgrade or UNKNOWN, not silent promotion.
4. Strong evidence status does not grant mutation capability.
5. Agent cannot self-label its own policy decision as human-authorized.

## I. Handoff tests

1. State capsule digest matches → validation may proceed.
2. Capsule modified after handoff creation → rejected.
3. Wrong receiver instance attempts acceptance → rejected when instance-bound.
4. Receiver ACK does not acquire sender lease.
5. Expired handoff → rejected/read-only diagnosis only.
6. Source revision mismatch → explicit stale result.
7. Handoff accepted after assignment revision changed → rejected or explicit revalidation required.

## J. Cross-project approval tests

1. Non-empty approver string without attestation → rejected by v3 exchange profile.
2. Approval signed for another exchange → rejected.
3. Artifact digest changed → rejected.
4. Destination changed → rejected.
5. Expired approval → rejected.
6. Replayed approval → rejected.
7. Valid exchange approval does not grant ambient source-write authority.

## K. Tamper-evident log tests

1. Delete envelope from stream → checkpoint/replay detects gap.
2. Modify envelope → digest/signature fails.
3. Reorder stream → predecessor/logical clock detects.
4. Create two children for one predecessor unexpectedly → fork detected.
5. Alter checkpoint member set → root mismatch.
6. Swarm-writable log rewrite cannot forge independently anchored checkpoint.

## L. Consequence linkage tests

1. Message references prepared action but does not execute it.
2. Protected effect requires consequence-gateway authorization independently of message signature.
3. Changed external payload invalidates authorized digest.
4. `UNKNOWN_EFFECT` never triggers blind replay from communication retry.
5. Execution receipt without target postcondition remains receipt/evidence, not final observed truth where independent observation is required.

## M. Swarm-behavior preservation tests

1. Research can still publish unconventional hypotheses as content.
2. Manager review flow remains available.
3. Primary retains project-local authority.
4. MASTER remains globally roaming for lifecycle control without gaining cross-project writes.
5. Messages cannot enable disabled schedules.
6. Normal communication does not require human confirmation.
7. v3 does not require hidden reasoning/chain-of-thought.
8. Existing v2 project can run unchanged with v3 experimental code present.

## Promotion gate

Promotion out of experiment requires:

- all v3 tests green at one exact SHA;
- all pre-existing v2/full hardening tests green at the same SHA;
- deterministic package/reproducibility checks if v3 enters packages;
- independent adversarial review;
- explicit human authorization for governance/promotion changes;
- server-side enforcement appropriate to the target repository;
- rollback tested.
