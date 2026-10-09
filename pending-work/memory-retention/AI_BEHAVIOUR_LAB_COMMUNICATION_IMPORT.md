# AI Behaviour Control Lab Communication Hardening — Pending Import

**Source project:** `boberino93-bit/ai-behaviour-control-lab`  
**Source artifact:** `agentbus-backup/intercomm-optimization-v1/INTERCOMM_OPTIMIZATION_PROFILE_V1.md`  
**Status here:** CANDIDATE IMPORT / NON-CANONICAL / NOT DEPLOYED

## 1. Security review result

The source profile is suitable for **selective policy import** into Intercommunication Enhancements as pending work because the relevant controls are governance/transport controls rather than sensitive payloads.

The source explicitly prohibits cross-project export of:

- secrets;
- raw domain data;
- personal data;
- unredacted research payloads;
- credentials;
- unrestricted task content.

It also states that peer capacity signals are read-only/advisory and do not grant mutation authority.

This pending import does **not** copy any private research payload, credentials, domain-specific data, or active behavioral-control authorization.

## 2. Safe controls proposed for import

### 2.1 Authority/storage separation

Adopt the pattern:

```text
CANONICAL LIVE COORDINATION STORE
→ WRITE
→ READBACK / VALIDATE
→ ELIGIBLE BACKUP MIRROR
```

Backup mirrors must not silently overwrite newer canonical state or become authoritative merely because they are easier to access.

Recovery from mirror requires freshness/integrity validation.

### 2.2 Project identity and fail-closed routing

Before protected mutation, verify:

```text
project ID
canonical coordination root
target repository / branch or target service
active role
applicable approval gates
```

Recent conversation context alone is not project authority.

Cross-project ambiguity or namespace mismatch fails closed for the affected branch.

### 2.3 Split-plane communication

Separate:

**Ephemeral / cheap plane**
- heartbeat;
- liveness;
- presence;
- transient capacity;
- polling cadence.

**Durable truth plane**
- material claims;
- evidence-backed findings;
- blockers;
- contradictions;
- decisions;
- ownership changes;
- handoffs;
- supersessions;
- recovery checkpoints;
- approval/authority changes.

Invariant:

```text
NO_DELTA / UNCHANGED_HEARTBEAT
!=
REASON_FOR_NEW_DURABLE_RECORD
```

This reduces write pressure without sacrificing reconstructable project truth.

### 2.4 Capacity evidence and UNKNOWN semantics

Capacity is valid only when derived from a defensible source such as:

```text
EXPLICIT_CONFIG
PROVIDER_OBSERVED
ERROR_DERIVED
```

If the hard limit or current usage cannot be verified:

```text
CAPACITY = UNKNOWN
```

Never infer unlimited capacity from absence of an error.

### 2.5 Reserve-capacity pattern

The AI Behaviour Control Lab currently uses:

```text
reserve = 20%
safe ceiling = 80%
GREEN < 60%
AMBER 60–75%
PRESERVE 75–80%
RESERVE_ONLY 80%–hard limit
EXHAUSTED >= hard limit
UNKNOWN = insufficient/stale evidence
```

For Intercommunication Enhancements, preserve this as an **originating implementation and candidate default**, not a universal law.

Generalized invariant:

> Normal traffic must not consume the capacity required to preserve safety-, authority-, evidence-, and continuity-critical state.

Future global thresholds should be parameterized by measured limits and recovery budget rather than hard-coded solely because 80/20 worked for one interface.

### 2.6 Write classes

Adopt/normalize:

```text
ESSENTIAL_CANONICAL
COALESCED_CHECKPOINT
DISCRETIONARY
```

with Intercommunication extensions:

```text
SAFETY_CRITICAL
AUTHORITY_CRITICAL
EVIDENCE_CRITICAL
CONTINUITY_CRITICAL
```

At reserve pressure, suppress/coalesce discretionary writes first.

### 2.7 Digest deduplication

If normalized logical content has not changed:

```text
UNCHANGED_CONTENT
→ NO DUPLICATE DURABLE OBJECT
```

This should apply to repetitive status, heartbeats, generated role packages, semantic capsules, and bridge metadata where safe.

### 2.8 Coalescing

Related nonurgent changes should become one coherent checkpoint rather than many small durable messages.

Coalescing must not erase chronology or raw evidence.

### 2.9 Sanitized read-only cross-project signaling

Only a narrow high-level need signal should cross ordinary project boundaries, e.g.:

```text
REVIEW_REQUIRED
PRIMARY_DECISION
RELEASE_PENDING
CAPACITY_PRESSURE
BLOCKED
```

Requirements:

```text
READ_ONLY
SANITIZED
FRESHNESS-BOUNDED
NO SECRETS
NO PERSONAL DATA
NO RAW DOMAIN PAYLOAD
NO CREDENTIALS
NO AUTHORITY TRANSFER
```

Missing/stale peer signal degrades to `UNKNOWN`.

### 2.10 Causation, supersession, and lease semantics

Material work claims should use:

- project-scoped identifiers;
- idempotency keys where applicable;
- causal/parent links;
- supersession links;
- TTL/lease semantics for temporary claims/locks.

Append-only history is preserved.

```text
SUPERSESSION != ERASURE
```

### 2.11 Role/package drift detection

Generated agent/role packages should fail validation when they omit currently required governance references.

This is especially relevant after memory/continuity changes so older packages cannot silently omit the new restoration contract.

## 3. Controls intentionally NOT imported as-is

### 3.1 Project-specific behavioral-control authority

No AI Behaviour Control Lab approval, validator, quarantine, capability, or project-local role semantics become Intercommunication authority merely by being referenced here.

### 3.2 Canonical-path assumptions

`/AI-Behaviour-Control-Lab-AgentBus` is not imported as a root path for Intercommunication Enhancements.

### 3.3 Fixed 80/20 as universal constant

The number is retained as provenance and candidate default, but requires measured validation before globalizing across unrelated resources.

### 3.4 Cross-project payload transfer

No unrestricted task context or research payload is imported.

## 4. Security invariants

```text
CAPACITY_SIGNAL != AUTHORITY
BACKUP != CANONICAL_STATE
MIRROR_AVAILABILITY != FRESHNESS
CROSS_PROJECT_VISIBILITY != CROSS_PROJECT_WRITE
NO_DELTA != DURABLE_EVENT
UNKNOWN_CAPACITY != UNLIMITED_CAPACITY
SUPERSESSION != DELETION
```

## 5. Required tests

Before promotion:

- exact 80% boundary behavior for any deployment that elects to use 80/20;
- configurable threshold behavior;
- stale capacity -> `UNKNOWN`;
- deduplication;
- coalescing without evidence loss;
- no durable heartbeat-only records;
- canonical write/readback before backup claim;
- mirror cannot override newer canonical state;
- project/repository/root mismatch fail-closed;
- sanitized cross-project signal rejects secrets/private/raw payload;
- peer signal never grants mutation authority;
- append-only supersession history survives recovery.

## 6. Promotion recommendation

Suitable for herd review as **communication and continuity hardening**, subject to the same timelock, exact-change authorization, privacy review, read-only canary, and rollback requirements as the memory system.
