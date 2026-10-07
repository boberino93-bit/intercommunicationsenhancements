# P1 External-Memory Path Audit — 2026-10-07

**Classification:** implementation audit  
**Applies to branch:** `p1-external-memory-layered-context-20261007`  
**Base:** `25b3010ab14da92766ca76b2af5e691e4efb274f`  
**First implementation commit:** `952fee799e3a689b9ebd9055cc603300c6a17751`

## Objective

Audit the swarm bootstrap, scheduler, handoff, synchronization, learning, recovery, cache/log, and forensic paths for reliance on native ChatGPT memory, then ensure the implementation has one explicit machine-readable external-only persistence invariant.

## Search result

A repository-wide code search of the base revision for the explicit identifiers `chatgpt_memory`, `saved_memory`, `memory_recall`, and `native_memory` returned no matches before the new policy implementation.

This means the defect was not an existing Python call site visibly invoking a native-memory API. The architectural gap was that the swarm contracts did not expose one explicit, enforceable prohibition against a host/model layer treating native ChatGPT memory as a recall/cache/fallback source.

## Existing external-state orientation confirmed

The existing framework already relies heavily on external project state:

- `AGENT_BOOTSTRAP.json` declares `INTERNAL_ARTIFACTORY` as forum authority and requires forum/master-handoff context before mutation.
- `GLOBAL_AGENT_ENTRYPOINT.json` loads the authoritative project forum, master handoff, and accepted state after project resolution.
- `protocols/agent_state_handoff.md` treats project handoff state as an explicit durable coordination surface.
- `protocols/internal_scheduler_service.md` is designed so continuity does not depend on an active model session remembering to continue.
- synchronization, task ownership, claims, leases, and accepted-state mechanisms are represented through explicit project/runtime records rather than assumed conversational recollection.

These properties reduce exposure but did not previously constitute a direct native-memory deny rule.

## Remediation introduced

The implementation branch adds:

1. `governance/SWARM_MEMORY_PERSISTENCE_POLICY.json` (`IEP-MEM-001`) as the machine-readable P1 invariant.
2. `protocols/external_swarm_memory.md` as the normative protocol.
3. `.interagent/directives/2026-10-07-p1-external-swarm-memory.json` as the packaged active directive.
4. `org_agent_mesh/swarm_memory_policy.py` as a reference runtime guard that rejects native-memory and unregistered collective-persistence sources and enforces verified external receipts.
5. `tests/test_swarm_memory_policy.py` as the negative/positive regression suite.
6. `AGENT_CONTEXT_REFERENCE.md` startup enforcement so fresh agents receive the rule before reconstructing swarm state.
7. `tools/build_agent_packages.py` package-build validation so role packages cannot build if the P1 policy is missing or weakened.
8. Artifactory/AgentBus and GitHub coordination-backup records for the directive and forensic finding.

## Layered-context interaction

The new `IEP-CTX-001` bootstrap directive states that context is pervasive and often present at multiple layers. That does **not** make every context layer authoritative.

The critical distinction is:

- host-provided current conversation/project/tool context may be observed as ephemeral context;
- native ChatGPT memory may not be queried or ingested as swarm state;
- collective swarm authority still requires the approved external state/provenance chain.

This prevents the layered-context directive from accidentally reopening the persistence fault it was added alongside.

## Remaining integration gates

At the time of this audit:

- implementation commit exists on the dedicated branch;
- canonical Artifactory/AgentBus directive publication exists;
- GitHub coordination backup exists in the implementation commit;
- direct `main` ref update was blocked by the platform safety gate;
- pull-request creation was also blocked by the platform safety gate;
- exact-revision GitHub Actions release validation has therefore not run.

**Completion state: NOT COMPLETE.** Main integration plus exact-revision CI/package validation remain required before claiming deployed closure.
