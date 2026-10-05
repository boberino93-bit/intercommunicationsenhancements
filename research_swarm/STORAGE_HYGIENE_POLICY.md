# Research Swarm Storage Hygiene Policy

Status: ACTIVE
Effective date: 2026-10-05
Scope: all registered projects participating in the recurring research swarm
Physical Artifactory/account quota: 20 GiB combined
Swarm operating cap: 16 GiB combined
Reserved headroom: 4 GiB (20% of physical quota)

## Objective

Keep the combined internal Artifactory/message-board/cache working set at or below 16 GiB so at least 20% of the 20 GiB quota remains unused for performance headroom, emergency recovery, and transient operations. GitHub is the durable historical backup surface where project contracts permit repository backup/mirroring. Internal Artifactory is the active working set, not an infinite archive.

The 16 GiB operating cap is a hard swarm planning limit. The swarm must not intentionally grow the combined working set above it. If usage reaches the cap, nonessential writes stop and cleanup/compaction becomes the immediate operational priority.

This policy does not create new authority. Destructive cleanup requires the same project-local write/delete authority and consequence controls as any other mutation. If direct internal Artifactory visibility or delete capability is unavailable, agents must not claim cleanup occurred; they may inventory, compact supported surfaces, reduce new output, verify GitHub backups, and publish a cleanup blocker.

## Portfolio watermarks

Watermarks are measured against the 16 GiB swarm operating cap, not the 20 GiB physical quota.

- NORMAL: < 12.8 GiB (<80% of operating cap). Continue research while avoiding redundant artifacts.
- ELEVATED: 12.8-14.4 GiB (80-90%). Manager begins routine compaction/pruning and suppresses low-information artifact generation.
- HIGH: 14.4-15.2 GiB (90-95%). Storage cleanup becomes a top operational priority. New bulky artifacts require clear material value.
- CRITICAL: 15.2-16.0 GiB (95-100%). Suspend nonessential cache/artifact growth. Preserve only safety-critical/current-state outputs while reducing the working set.
- OPERATING CAP: >=16 GiB. Enter storage-protection mode: no intentional nonessential growth. Perform read/verify/compact/prune work until measured usage is below 15.2 GiB, preferably below 14.4 GiB.
- PHYSICAL QUOTA: 20 GiB. The 4 GiB gap is reserved headroom and is not normal usable capacity.

If exact aggregate size is unavailable, report `STORAGE_USAGE_UNKNOWN` and act conservatively: minimize new large artifacts and attempt to obtain authoritative measurements before destructive cleanup.

## What must be preserved internally

Do not delete solely for space pressure when the record is still needed for current correctness:

- current project identity/bootstrap/governance contracts;
- current `MASTER_HANDOFF` or canonical equivalent;
- active task/claim/lease/fencing state;
- current frontier, blockers, pending human decisions, and unresolved contradictions;
- latest material evidence needed to support active decisions;
- current release/build/package manifests required for reproduction;
- authorization/approval/audit receipts that are still operative;
- latest recovery checkpoints for active or unexpectedly interrupted work;
- anything whose durable backup has not been verified.

## Preferred cleanup order

Clean the cheapest, lowest-risk waste first:

1. exact duplicate cache entries and duplicate packaged artifacts;
2. superseded generated packages whose replacements are verified;
3. temporary/failed build bundles and abandoned scratch exports with no active reference;
4. obsolete caches reproducible from canonical source;
5. redundant liveness/heartbeat/service-checkpoint history after retaining current state and enough evidence for incident/recovery analysis;
6. superseded message-board entries after a compact current-state summary/handoff preserves still-material facts and provenance;
7. old snapshot/archive payloads after a verified GitHub backup exists and the snapshot is not required for active recovery/audit;
8. other stale evidence only after confirming it is not referenced by an active task, decision, handoff, release, or recovery path.

## Backup-before-prune rule

Before deleting historical material from internal Artifactory:

1. identify the exact prune set;
2. verify it is not current/active/required state;
3. verify a durable GitHub backup, repository snapshot, or equivalent approved historical copy exists for material worth retaining;
4. where practical, record manifest/hash/count/size and source cutoff for the prune set;
5. compact still-material facts into canonical current state rather than retaining raw noise indefinitely;
6. perform deletion only with valid project-local authority;
7. read back/re-measure storage and record reclaimed space or `UNKNOWN` if measurement is unavailable.

Never delete first and hope a backup exists later.

## Swarm role responsibilities

### MASTER

Maintain portfolio-level storage awareness across registered projects. Detect which projects drive growth, identify duplicate cross-project caches or obsolete rollout artifacts, and include storage pressure in portfolio prioritization. Do not override project-local delete authority.

### MANAGER

Own project-level hygiene orchestration. Reconcile current working set vs stale/superseded material, prepare safe prune sets, ensure backup-before-prune, coordinate compaction, and prevent researchers from producing redundant large artifacts. At ELEVATED/HIGH/CRITICAL, storage hygiene consumes progressively more of the frontier. At the 16 GiB cap, cleanup takes precedence over nonessential research writes.

### RESEARCHERS

Remove waste they create or encounter within authority: reuse existing evidence, do not republish identical findings, prefer references/hashes over copying large payloads, compact experiments, remove reproducible scratch caches when safe, and mark superseded outputs. Researchers may propose prune candidates but must not bypass project-local destructive-action controls.

## Hourly-run behavior

Every hourly invocation performs a lightweight storage-hygiene check as part of orientation and closeout. Do not rescan every byte each run when fresh authoritative size/inventory data exists. Refresh measurement when stale, at a watermark transition, after a large write, or after cleanup.

If there is no meaningful new research lane, do not generate filler. Useful work may be dedupe, compaction, stale-cache removal, backup verification, checkpoint cleanup, evidence indexing, or recording `NO_MATERIAL_DELTA` without bulky new artifacts.

## Cross-project cache rule

The 16 GiB operating cap applies across all registered projects combined. Prefer one canonical copy plus references over project-by-project duplication when project isolation and authority rules permit. Cross-project telemetry/inventory may remain read-only; data or authority must not cross project boundaries merely to save space.

Where identical content must remain project-local for authority/isolation reasons, preserve the minimum required authoritative copies and eliminate only non-authoritative duplicates/caches.

## Safe deletion boundary

Delete/compact only when all are true:

- exact project-bound target scope;
- stale/superseded/reproducible or otherwise nonessential;
- no active task/decision/handoff/release/recovery dependency;
- historical retention requirements satisfied;
- backup verified when required;
- valid mutation/destructive authority exists;
- effect can be verified after deletion.

If any condition is unknown, defer deletion and reduce new storage growth instead.

## Success metrics

Track when available: combined GiB; per-project GiB; 24h growth; redundant bytes; bytes reclaimed; backup coverage; stale message count; cache reuse rate; new-artifact bytes per material finding; blocked cleanups; and any storage-driven research suspension.

Target state: a small current recoverable working set, durable history in GitHub where applicable, and at least 4 GiB / 20% physical-quota headroom.
