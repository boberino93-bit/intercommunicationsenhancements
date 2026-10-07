# Project Glance Protocol v1

## Purpose
Provide a fast, compact, evidence-backed operational view across registered projects without replacing project-local AgentBus/durable state.

## Core rule
`PROJECT_GLANCE.json` and `PROJECT_GLANCE_INDEX.json` are read-only derived observability surfaces. They never grant role, claim, lease, fencing, mutation, scheduling, or cross-project authority.

## Local project snapshot
Each registered project may maintain a root `PROJECT_GLANCE.json`. Update it only on a material transition: meaningful work begins or ends, the current focus changes, a blocker appears or clears, the next action changes materially, or project control enters/leaves pause/hold/stop. Do not rewrite it for heartbeat-only noise.

Required fields:
- `project_id`
- `repository`
- `observed_at_utc`
- `status`
- `current_focus`
- `blockers`
- `next_action`
- `last_material_change`
- `evidence_refs`

Allowed status values: `EXECUTING`, `WAITING`, `BLOCKED`, `IDLE_READY`, `PAUSED`, `STALE`, `UNKNOWN`.

## Central glance cache
`PROJECT_GLANCE_INDEX.json` is a sanitized aggregation of the registered local snapshots. It is optimized for a one-read human status query. Project-local state remains canonical. The aggregator may copy observability metadata; it may not mutate project domain state or convey authority.

If a local snapshot is missing, contradictory, or older than the configured stale threshold, the central entry must report `STALE` or `UNKNOWN` and retain the evidence pointer needed for refresh. Repository commit activity alone must never be interpreted as proof that an agent is executing.

## Fast-path behavior
For ordinary questions such as `project status`, `what is going on with the projects`, or `how are the projects doing`, read the central glance first. If entries are fresh, answer directly without re-crawling every repository. Deep-read only stale/conflicting entries or when the human explicitly asks for a forensic audit.

## Update responsibility
A worker already bound to a project should refresh that project's local glance as part of the same material checkpoint/handoff when permitted. The synchronized scheduler bridge may aggregate the sanitized local snapshots into the central cache. No worker may infer cross-project write authority from this protocol.

## Safety
Unknown is not idle. Stale is not current. A cached summary is not authorization. A glance record may summarize a blocker but must not expose secrets, protected evidence, credentials, or confidential payloads.
