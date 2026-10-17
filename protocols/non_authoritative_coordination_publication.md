# Non-Authoritative Coordination Publication

Status: **ACTIVE HARD GATE**  
Version: **1.4.0**

The registered internal coordination surface is the **ChatGPT Library AgentBus**. Historical labels `INTERNAL_ARTIFACTORY` and `ARTIFACTORY` are compatibility aliases for that route and do not identify JFrog.

PRIMARY, MANAGER, RESEARCH, and registered research aliases may publish append-only project coordination messages through the narrow project-scoped capability. This capability conveys no protected mutation authority.

## Canonical order

1. Resolve the exact bound project, repository, and registered AgentBus namespace.
2. When the AgentBus surface is available, publish there and verify readback when supported.
3. When required by the governing checkpoint protocol, create an immutable same-project GitHub backup under `agentbus-backup/coordination-messages/`.

`GITHUB_WRITE != AGENTBUS_WRITE`. A GitHub backup never proves that AgentBus was written.

## Runtime-unavailable AgentBus

If the registered namespace is known but the current runtime does not expose the AgentBus surface, classify that as transport unavailability, not missing evidence. A same-project GitHub backup may be used only where the governing workflow explicitly permits degraded transport and the backup is read back successfully.

Use `AGENTBUS_RUNTIME_UNAVAILABLE`; legacy records containing `ARTIFACTORY_RUNTIME_UNAVAILABLE` remain interpretable as the same historical condition.

Do not invent an alternate namespace or repository. If neither required surface can be written/read back, block the affected persistence-dependent branch and continue unrelated safe work.

## V26 reconciliation

Corresponding records are equivalent only when both `logical_record_id` and `payload_sha256` match. Whole-store inequality is not itself a record conflict. The same logical record ID with a different payload digest is a conflict and must be preserved and surfaced.

## Boundaries

Coordination publication is create-new-message only. It does not include overwrite, deletion, rename, move, branch creation, workflow execution, deployment, schedule mutation, accepted-state mutation, or cross-project mutation. Those operations use their normal protected-mutation gates.

The current recovery procedure is defined by `governance/V26_AGENTBUS_LINKAGE_POLICY.json` and `docs/V26_AGENTBUS_RECOVERY_MIGRATION.md`.
