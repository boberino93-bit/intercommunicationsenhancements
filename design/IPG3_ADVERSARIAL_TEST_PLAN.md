# IPG3 Adversarial Test Plan

Status: **NON-AUTHORITATIVE DESIGN**

IPG3 is not eligible for protocol promotion until the following attack classes have executable tests with attributable evidence.

## Identity and authority attacks

- forged logical agent ID;
- forged execution-instance ID;
- forged authenticated principal;
- project ID spoofing;
- destination-project confusion;
- stale execution instance after restart;
- child capability escalation;
- delegation contract expansion;
- caller-supplied project identity used as authority;
- confused-deputy operation through a higher-authority agent.

Expected invariant: identity claims never grant authority by themselves. Local destination-side validation derives authority from an active bound session, authenticated principal where available, capability policy, delegation ceiling and approval state.

## Messaging and causal attacks

- duplicate publication;
- replay with a new message ID but same effect identity;
- replay with altered payload;
- forged correlation or causation reference;
- cycle in causal ancestry;
- impossible event sequence;
- missing predecessor hash;
- altered historical event;
- expiry bypass;
- forged acknowledgement;
- terminal-state transition reversal.

Expected invariant: accepted history remains attributable, append/supersession oriented and tamper-evident; retry does not imply duplicate execution.

## Human approval attacks

- reuse after max uses;
- use after expiry;
- use after revocation;
- operation class mismatch;
- target resource mismatch;
- target scope-digest mismatch;
- use by a different project;
- use for a different effect;
- replay by a restarted execution instance;
- approval derived only from conversational summary rather than decision evidence.

Expected invariant: approval is a bounded consumable capability, not a reusable prose statement.

## Side-effect attacks

- same effect delivered twice;
- same idempotency key with different request digest;
- crash after external commit but before local receipt persistence;
- crash before external commit;
- conflicting external receipt;
- forged resulting version;
- duplicate no-op incorrectly claiming a second commit;
- effect committed by an unauthorized principal;
- effect target outside delegation/approval boundary.

Expected invariant: retry converges to one externally committed effect or a fail-closed/inconclusive state with evidence. Unknown commit state is never silently treated as success.

## Cross-project attacks

- source equals destination;
- source-session project mismatch;
- requester/session mismatch;
- missing CROSS_PROJECT_EXCHANGE capability;
- expired exchange;
- approval mismatch;
- artifact-count overrun;
- byte-scope overrun;
- path-scope overrun;
- unsanitized secret;
- personal data leakage;
- project-instance state leakage;
- source hash mismatch;
- sanitized hash mismatch;
- destination accepting before validation;
- replay of previously imported artifact;
- malicious destination attempting to expand source authority.

Expected invariant: cross-project exchange is a bounded export/import transaction between autonomous projects, never shared mutable state.

## Trust and memory attacks

- external untrusted content presented as authoritative configuration;
- agent reflection promoted directly to policy;
- peer-project pattern copied without provenance;
- provenance path altered after validation;
- trust promotion without decision record;
- revoked fact still consumed as current truth;
- quarantined content reintroduced through summary;
- malicious research artifact designed to alter bootstrap instructions.

Expected invariant: trust class and provenance govern how information can influence control state. Summarization does not erase provenance or upgrade trust.

## Recursive-evolution attacks

- candidate self-marks as benchmarked;
- candidate changes its own acceptance threshold;
- candidate removes tests that it fails;
- optimizer promotes its own successor without independent gate evidence;
- benchmark suite overfits to candidate;
- candidate improves target metric while weakening isolation;
- repeated failed idea rediscovered under different wording;
- endless research loop with no novel evidence;
- complexity growth without measurable benefit;
- incumbent removed before candidate proves non-inferiority.

Expected invariant: proposal authority and promotion authority remain separate. The incumbent remains available until a candidate passes explicit evidence gates.

## Supply-chain and deployment attacks

- draft design file accidentally enters production dependency closure;
- mixed G2/G3 role packages;
- stale schema in one role package;
- package source-revision mismatch;
- component hash drift;
- unsigned/unauthenticated external capability descriptor trusted as local policy;
- adapter dependency substitution;
- non-reproducible build;
- runtime claims G3 support while deployment manifest lacks required components.

Expected invariant: protocol promotion and deployment are synchronized, exact-revision and reproducible.

## Distributed-state failure injection

When durable adapters are introduced, inject failures around every critical boundary:

1. before write;
2. after local prepare;
3. after durable state commit;
4. after external effect commit;
5. before effect receipt persistence;
6. before acknowledgement;
7. after acknowledgement;
8. during lease renewal;
9. during project pause/drain;
10. during recovery by a fresh execution instance.

Test with duplicate workers, process death, delayed messages, reordered messages, network partitions and stale replicas.

## Initial executable coverage already added

The current design branch includes automated tests for:

- deterministic v2 -> v3 shadow projection;
- source-message non-mutation;
- cross-project ordinary Message v2 rejection;
- missing execution identity rejection;
- payload tamper detection;
- cross-project source/destination separation;
- requester/source-session agreement;
- artifact scope overrun rejection;
- mandatory sanitization;
- approval use exhaustion;
- approval consumed-state consistency;
- duplicate effect no-op semantics;
- effect prepare/commit ordering.

These are an initial subset, not evidence that IPG3 is production-ready.

## Promotion criterion

No attack class is considered mitigated merely because a document says so. A mitigation becomes a protocol claim only after an executable test demonstrates the enforcement behavior against the implementation that will actually ship.
