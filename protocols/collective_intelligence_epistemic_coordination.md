# Collective-Intelligence / Epistemic Coordination Protocol — Candidate v1

This protocol is subordinate to current project binding, PRIMARY/MANAGER/RESEARCH authority separation, claims/leases/fencing, work holds, durable-state CAS, coordination publication, mutation authorization, and consequence gateways. Epistemic confidence, consensus, model generation, or a research rendezvous never grants mutation authority.

Research and Manager executions publish compact, structured epistemic broadcasts only through the existing project-scoped coordination publication lane. A broadcast must be bound to a canonical `CoordinationPublicationPermit` already issued by `org_agent_mesh.coordination_publication`; this protocol creates no second transport and no new publication authority. Broadcasts are always `authority_conveyed=false`.

High-impact questions use blinded first pass followed by rendezvous. Before rendezvous opens, lanes receive the question, bounded scope, permitted evidence surfaces, constraints, and output contract but not peer conclusions. After threshold or bounded timeout, peer records become visible and are classified as SUPPORT, QUALIFY, CONTRADICT, DUPLICATE_ORIGIN, TEMPORAL_VARIANT, CONTEXT_VARIANT, or UNRELATED.

Source identity is distinct from source instance. Mirrors and derived copies collapse transitively to their root evidence origin for corroboration, while instances remain preserved as provenance. Reconciliation rewrites source references to canonical source identities and validates that source instances, evidence, claims, and hypotheses do not contain dangling references.

Negative evidence distinguishes `NOT_FOUND` from `ABSENT`. `NOT_FOUND` records an unsuccessful bounded search and is deliberately weaker than authoritative absence; it cannot by itself produce confirmed absence. `ABSENT` means an inspected authoritative surface supports absence and still carries its recorded scope, version context, date, and confidence.

Reconciliation merges evidence, collapses duplicate source origins, normalizes applicability, recalibrates claim confidence, classifies apparent contradictions, updates competing hypotheses, preserves minority findings and superseded provenance, records a monotonically increasing model generation, and recomputes the information-gain frontier. Contextual conflicts include temporal, version, environment, configuration, deployment, terminology, and workflow differences; unresolved evidence gaps remain explicit rather than being silently averaged away.

`conclusions_changed_after_peer_evidence` is counterfactual: peer evidence must be explicitly identified, carry originating-agent provenance, and change the synthesized conclusion versus the same reconciliation with that peer evidence removed. A caller-supplied boolean is not sufficient.

Accepted shared-model persistence reuses the existing durable backend and requires the canonical active-session authorization callback with `WRITE_ACCEPTED_STATE`; there is no local ActorContext fallback for durable accepted-state mutation. Idempotent event replays are recognized by event digest before stale-writer rejection, while conflicting reuse of an event ID fails closed.

Checkpoint v3 preserves the stage/state and interactive-recovery semantics of checkpoint v2 and adds only compact epistemic delta references. It never embeds the full evidence graph and does not alter v2 readers. A v2 producer may continue emitting v2 until v3 adoption is explicitly promoted.
