# V25 R11 External Persistence and Message-Board Candidate Protocol

Status: `FORENSIC_IMPLEMENTATION_CANDIDATE`  
Canonical promotion: `FALSE`

## Purpose

This protocol adapts the repository's external persistence/message-board behavior to the V25 R11 bootstrap model without claiming that R11 is canonical.

## Bootstrap rule

The standalone bootstrap sequence is authoritative only for this candidate branch:

1. enter `UNBOUND_READ_ONLY`;
2. initialize and validate the embedded VMBUS;
3. require `VMBUS_READY`;
4. load the corrected R10 principal-context profile;
5. load the R11 synthesis extension as revisable `MODEL_SYNTHESIS_HYPOTHESIS` records;
6. require `PRINCIPAL_CONTEXT_READY`;
7. bind project and VMBUS project namespace;
8. load project-local policy and continuity;
9. discover runtime capabilities;
10. assess optional external mirrors;
11. only then interpret and execute the task under normal authority gates.

External GitHub or Artifactory/message-board availability is not a prerequisite for standalone readiness.

## Artifactory/message-board behavior

The registered Intercommunications Enhancements namespace remains:

- namespace: `intercommunicationsenhancements::messages`
- path: `/Intercommunication enhancements/AgentBus/messages`

Under this candidate, that surface is an optional post-readiness external coordination mirror. If the current runtime does not expose a real Artifactory/message-board connector, record `ARTIFACTORY_RUNTIME_UNAVAILABLE` and continue only work that does not require durable shared transport.

Do not claim an Artifactory publication occurred because a GitHub mirror exists. Do not invent a path, connector, write receipt, or readback.

## GitHub behavior

GitHub remains durable source/version control and may hold immutable coordination mirror records under `agentbus-backup/coordination-messages/`.

A GitHub mirror must not silently override a conflicting Artifactory record or embedded VMBUS state. Mirror equivalence requires the same logical record ID and payload digest.

## Conflict and outage rules

`EXTERNAL_UNAVAILABLE != BOOTSTRAP_FAILURE`

`GITHUB_WRITE != ARTIFACTORY_WRITE`

`MIRROR_PRESENT != MIRROR_EQUIVALENT`

`MIRROR_CONFLICT != PERMISSION_TO_SELECT_A_WINNER`

`PRINCIPAL_CONTEXT_READY != DURABLE_EXTERNAL_COMMIT`

Preserve conflicts and transport outages as explicit state.

## Scheduled swarm sequencing

Clock time is not a trustworthy serialization mechanism. Research, Manager, and Primary tasks may begin at the same scheduled time. Ordering must therefore be enforced by project-scoped checkpoint identity, upstream readiness, monotonic sequence/fencing checks, and explicit downstream consumption rules.

A downstream stage that has no valid upstream checkpoint may continue independent safe work or remain in a waiting/progress state, but must not infer readiness from schedule order.

## Scheduler posture for this migration

During this candidate migration, scheduled tasks are disabled by default except the explicitly retained `VMBUS Defrag` task. This protocol does not itself authorize creation, enablement, re-enablement, rescheduling, or deletion of scheduler tasks.

## Promotion boundary

This protocol is candidate-only. Promotion to main/canonical policy requires a separate governed authorization case and any stronger proof required by repository policy.
