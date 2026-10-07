# Layered Context Resolution Protocol

Status: ACTIVE  
Policy: `governance/LAYERED_CONTEXT_POLICY.json` (`IEP-CTX-001`)

## Bootstrap directive

**Context is present in everything observable, and often at multiple layers.**

Every observable input may carry context: the current human message, the surrounding conversation, project binding, screenshots and attachments, tool results, scheduler launch data, bootstrap files, handoffs, AgentBus records, repository state, claims/leases/fences, UI state, and validated learning/governance records.

An agent must therefore not equate "not visible in this one layer" with "not present." Before declaring context missing, asking the human to repeat information, or treating a datum as new, scan the available authorized context layers that are relevant to the task.

## Layer separation

Context presence, evidence quality, and authority are separate properties.

A datum can be present in several layers but still be non-authoritative. A repeated datum is not independent corroboration merely because it appears multiple times. A current explicit human instruction may control task intent while an external project record controls accepted swarm state. A screenshot may carry temporal evidence without granting mutation authority.

For each material datum, preserve when practical:

- source layer;
- project identity;
- timestamp or temporal state such as BEFORE / AFTER / CURRENT / BASELINE;
- authority class;
- provenance or reference;
- whether another layer repeats, contradicts, supersedes, or merely contextualizes it.

## Reconciliation rules

1. Enumerate the context-bearing layers actually available to the current agent.
2. Extract material context without assuming one layer is complete.
3. Deduplicate repeated facts without converting repetition into extra evidence weight.
4. Reconcile conflicts using the applicable project-binding, authority, temporal, and provenance rules.
5. Preserve material contradictions when they cannot safely be resolved.
6. Only after this process may the agent conclude that context is genuinely missing and ask the minimum necessary question.

## Hidden-context boundary

The directive does not authorize an agent to invent inaccessible context or claim visibility it does not have. It says to reason across all context that is actually available, not to hallucinate undisclosed layers.

## Native ChatGPT memory boundary

This protocol does not weaken `IEP-MEM-001`.

Native ChatGPT memory is not an authorized swarm-state layer and must not be queried, ingested, or used as fallback for collective swarm state. Host-provided conversation/project context may be observed as ephemeral execution context, but any swarm-authority claim must still be grounded in the approved external persistence and authority chain.

## Completion rule

A response such as "I don't have that context" is only justified after checking the relevant available layers. If the information is present in another available layer, recover and reconcile it rather than asking the human to restate it.
