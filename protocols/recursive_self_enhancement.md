# Recursive Self-Enhancement Protocol v1

## Purpose

Allow every packaged agent role to learn from reusable patterns found in peer project Artifactory/repository structures without granting any authority to mutate those peer projects.

The peer repository is evidence. This project is the only graft target.

## Non-mutation wall

Peer-project observation is strictly read-only. An enhancement cycle may list repository paths, read text/artifacts, inspect exact revisions, and calculate local digests. It MUST NOT write, update, delete, rename, commit, branch, tag, merge, open/modify issues or pull requests, dispatch workflows, alter settings, or publish artifacts in a peer repository.

No peer path is ever treated as a local filesystem path. Imported content is represented as an immutable snapshot with repository identity, exact revision, logical path, and SHA-256 digest.

All generated candidate/cycle state is written only below the bound local project root, by default `.interagent/self_enhancement/`.

## Recursive cycle

1. Bind to the current project and confirm repository identity.
2. Enumerate approved peer observation sources through a read-only adapter.
3. Pin each peer to an exact observed revision for the cycle.
4. Read bounded seed artifacts and extract reusable improvement signals.
5. Persist each signal locally as a deterministic candidate with provenance, risk, rationale, expected benefit, and proposed local targets.
6. A candidate may name bounded follow-up peer paths. Those paths form the next graph depth and are read only if the configured recursion depth/candidate limits allow it.
7. De-duplicate by repository + revision + path + content digest + pattern + proposed targets.
8. Stop at the configured recursion/candidate/artifact bounds even when more signals exist.
9. Manager reviews evidence, contradictions, compatibility, authority effects, and required regression tests.
10. Primary alone may accept a candidate for grafting into authoritative project state.
11. Grafting is a normal local project change: modify locally, test, rebuild all affected role packages from an exact source revision, and verify package synchronization.

The algorithm is recursive discovery, not autonomous self-modification.

## Candidate lifecycle

`DISCOVERED -> EVIDENCE_REVIEWED -> VALIDATED -> PRIMARY_ACCEPTED -> GRAFTED`

Terminal alternatives are `REJECTED`, `SUPERSEDED`, and `BLOCKED`.

History is append/supersession oriented. Do not erase prior evidence to make a newer conclusion look canonical.

## Evidence contract

Evidence outranks agent confidence. Every material candidate should preserve:

- peer repository identity;
- exact observed revision/HEAD;
- source artifact path;
- source content digest;
- reusable pattern, separated from project-specific/domain content;
- expected local benefit;
- risks and authority implications;
- contradictions/limitations;
- proposed local target components;
- validation/tests needed before promotion.

Project-specific secrets, credentials, private user data, and domain-instance state must not be copied into framework packages.

## Role responsibilities

### RESEARCH / SPECIALIST

Continuously look for reusable patterns during normal startup, assigned research, handoff, and explicit enhancement cycles. Use read-only peer access only. Produce provenance-rich candidates and follow-up probes. Research cannot promote or graft a candidate.

### MANAGER / REVIEWER

Review candidate quality, deduplicate overlapping proposals, reconcile contradictions, assess compatibility and regression risk, and define validation work. Manager may recommend disposition but cannot silently convert a peer pattern into accepted project state.

### PRIMARY / ORCHESTRATOR

Own the improvement graph and final promotion gate. Decide which validated patterns are grafted locally, preserve authority boundaries, require tests, and ensure PRIMARY/MANAGER/RESEARCH packages are rebuilt and verified after shared changes.

## Continuous operation

"Continuous" means the enhancement check is part of normal agent lifecycle checkpoints: startup, handoff, package/release review, and explicit enhancement work. The framework does not create an unbounded background daemon by default. A deployment may schedule repeated cycles externally if its own governance permits it.

## Initial reusable signals observed

The first peer scan identified useful classes of patterns worth local evaluation, including:

- accepted-state snapshots and revalidation-based controller succession;
- deployment-time coordination snapshots/checksum manifests;
- manager evidence disposition contracts and contradiction handling;
- cross-lane architecture gates;
- non-overwriting research/session history with explicit correction logs;
- exact-revision readback before claiming publication or handoff success.

These observations are candidate sources, not automatically accepted framework behavior.
