# Portable Agent Recovery BIOS — Candidate

**Working name:** `AI Agent BIOS`  
**Technical name:** `Portable Agent Recovery Kernel`  
**Status:** CANDIDATE / DECLARATIVE / NON-EXECUTING / NOT AUTHORITY

## 1. Why "BIOS" is a useful analogy

The analogy is useful if kept precise.

A conventional BIOS/firmware layer provides enough deterministic startup structure for a machine to identify itself, initialize essential interfaces, perform basic checks, and locate the next stage of boot.

The proposed AI Agent BIOS serves a similar **recovery/bootstrap** role for an otherwise context-poor agent:

```text
IDENTIFY PROJECT
→ VERIFY ARTIFACT / VERSION
→ LOAD ROOT INVARIANTS
→ LOAD TRUST / AUTHORITY BOUNDARIES
→ LOCATE DURABLE CONTEXT
→ RECONSTRUCT CURRENT STATE
→ IDENTIFY GAPS / HOLDS
→ IDENTIFY NEXT SAFE ACTION
→ HAND OFF TO NORMAL BOOTSTRAP
```

It is not analogous to hardware firmware in the sense of privileged machine-code execution.

The Markdown/file representation is inert data until an authorized runtime parses it.

## 2. Fundamental distinctions

```text
EMBEDDED_KERNEL != EXECUTING_KERNEL
DOCUMENT_POSSESSION != AUTHORITY
RESTORED_CONTEXT != MUTATION_PERMISSION
PORTABLE_CONTEXT != PORTABLE_IDENTITY
PORTABLE_IDENTITY_CLAIM != AUTHENTICATION
AUTHENTICATION != AUTHORIZATION
OLD_BOOT_RECORD != CURRENT_AUTHORIZATION
```

## 3. Minimal recovery kernel contents

A portable recovery artifact should carry or point to:

```yaml
kernel_id:
schema_version:
project_id:
artifact_id:
created_at:
source_revision:
payload_digest:
status:
root_invariants:
canonical_state_locator:
backup_state_locators:
context_restore_order:
bridge_registry_ref:
authority_policy_ref:
privacy_policy_ref:
current_handoff_ref:
current_hold_ref:
source_coverage:
known_gaps:
next_stage:
authority_conveyed: false
```

## 4. Cold-start behavior

A reviewing/recovery agent receiving only the BIOS artifact should:

1. verify artifact digest/signature when available;
2. bind to the declared project only after project identity validation;
3. read status and source-coverage labels;
4. load root invariants;
5. locate current external canonical state;
6. compare the artifact revision to current durable state;
7. treat stale material as historical evidence rather than current control state;
8. reconstruct objective, evidence, contradictions, authorship, open work and next safe action;
9. refuse to reuse historical authorization;
10. disclose unresolved gaps;
11. continue into the normal project bootstrap only when allowed.

## 5. What the BIOS may preserve

Suitable portable content:

- project identity and schema;
- public-safe root invariants;
- bridge topology;
- source manifests;
- current non-sensitive handoff summaries;
- content hashes;
- recovery algorithms;
- context coverage state;
- compatibility/migration instructions;
- public-safe concept pointers;
- test and validation requirements.

## 6. What the BIOS should not contain in a public artifact

- passwords;
- API keys;
- session tokens;
- authentication secrets;
- raw medical/financial/intimate context;
- employer/customer restricted data;
- unrestricted cross-project private payload;
- reusable authorization proof that could cause a mutation;
- executable commands whose mere presence is treated as current authority.

Private recovery artifacts may contain additional private continuity material only under a separately governed private store and access boundary.

## 7. Instruction-injection resistance

Historical evidence inside a portable recovery package must default to **DATA**, not executable instruction.

Every embedded section should have a trust class such as:

```text
CURRENT_POLICY_REFERENCE
HISTORICAL_EVIDENCE
UNTRUSTED_EXTERNAL_TEXT
PRIVATE_DATA
CANDIDATE_INSTRUCTION
```

Only instructions verified against the current authority/control plane may become actionable.

## 8. Freshness / replay protection

A BIOS package must never assume it is current merely because it is internally consistent.

Required checks:

```text
artifact digest valid?
schema supported?
project matches?
source revision current?
canonical state newer?
active hold changed?
authority case expired/revoked?
bridge contract changed?
```

Stale BIOS behavior:

```text
RESTORE ORIENTATION / PROVENANCE
BUT
DO NOT RESTORE OLD AUTHORITY
```

## 9. Single-file forensic backup

A Markdown file can contain:

- this recovery kernel;
- complete bridge registry;
- source manifests;
- human-readable architecture;
- machine-readable JSON/YAML blocks;
- and Base64-encoded immutable archive payloads.

This creates a useful **cold-storage recovery capsule**.

However:

```text
DURABLE_FILE != ACTIVE_CONTEXT
```

If the file is larger than a model context window, it must remain searchable/range-addressable through stable section IDs and manifests.

## 10. Relationship to memory retention

The BIOS is not the memory database.

It is the **locator and reconstruction contract** for the memory system.

```text
AI AGENT BIOS
→ LOCATES / VALIDATES CONTINUITY STORES
→ LOADS MINIMUM SAFE CONTEXT
→ RECONSTRUCTS PROJECT STATE
→ HANDS OFF TO NORMAL RUNTIME
```

This separation reduces the risk that a huge memory archive itself becomes the bootstrap protocol.

## 11. Recovery priority

The BIOS should be small enough to load first, while heavier evidence remains externally addressable.

Suggested tiers:

```text
TIER 0 — BIOS / identity / invariants / locators
TIER 1 — current semantic continuity capsule
TIER 2 — current handoff / evidence / contradictions
TIER 3 — federated discovery pointers
TIER 4 — raw event / visible-turn history
TIER 5 — cold forensic archives
```

## 12. Required tests

- valid current BIOS -> correct project and state locators;
- stale BIOS -> orientation only, no authority replay;
- tampered BIOS -> digest/signature failure;
- wrong-project BIOS -> fail closed;
- embedded malicious historical instruction -> treated as data;
- unavailable canonical store -> explicit degraded/blocked status;
- large single-file backup -> kernel remains retrievable without loading full archive;
- schema mismatch -> explicit compatibility path or stop;
- private pointer -> no payload disclosure without authorization;
- recovery -> exact source coverage disclosed.

## 13. Candidate conclusion

"AI Agent BIOS" is a strong communication label for the concept as long as the technical documentation keeps the stricter term **Portable Agent Recovery Kernel** and preserves the distinction between declarative recovery metadata and privileged execution.
