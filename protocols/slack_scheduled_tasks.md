# Slack Scheduled-Task Transport Protocol v1

Slack is an optional transport for scheduled-task coordination and delivery. It is not canonical project state and it is not the scheduler for dynamic agent work.

## Two scheduling modes

1. **Dynamic scheduled work** — use the task scheduler/automation to invoke the agent at the requested cadence. The run performs its project work first, persists canonical evidence/state in the bound project, then may send a Slack summary or link.
2. **Static scheduled message** — when no computation or state inspection is required at delivery time, Slack's native scheduled-message capability may be used directly.

Do not use a pre-scheduled Slack message as a substitute for a dynamic task that must inspect current state at execution time.

## Canonical-state rule

- Artifactory/GitHub/project artifacts remain the durable source of truth.
- Slack messages are notifications, summaries, requests, or human-facing handoff surfaces.
- A Slack delivery failure does not erase or roll back a successfully persisted task result. Record delivery failure separately and retry only under the task's retry policy.
- Material decisions received in Slack must be folded back into canonical project state before they are treated as accepted project truth.

## Destination binding

Every Slack-enabled scheduled task must bind an explicit destination before outbound delivery:
- workspace identity when available;
- channel/conversation ID, not an inferred channel name;
- optional thread timestamp;
- allowed event types (`START`, `BLOCKER`, `COMPLETE`, `FAILURE`, `DIGEST`);
- whether Slack input is read-only context or may contain explicit human approval.

Never guess a channel from project semantics. Never redirect to a different Slack destination because a name appears similar.

## External-communication boundary

Slack posting is an external communication action. Agents may post only when the scheduled task configuration explicitly enables Slack delivery and the agent/package has the required external-communication capability.

Default behavior is no Slack post when the destination is absent or ambiguous. Escalate to Primary/Manager rather than choosing a destination.

## Message discipline

For routine scheduled tasks, prefer a compact lifecycle:
- optional start message only for long-running/high-value jobs;
- blocker/failure messages when human action is needed;
- one completion/digest message containing result, canonical artifact/message reference, exact project identity, and next action if any.

Avoid flooding channels with per-step operational chatter.

## Privacy and sensitive data

Do not place secrets, credentials, MFA data, private keys, tokens, or unnecessary sensitive project/user data in Slack. Prefer links/references to canonical restricted artifacts when the Slack audience already has access.

## Role behavior

### PRIMARY
- approves or configures Slack destinations for recurring project workflows;
- ensures scheduled tasks preserve canonical-state-before-notification ordering;
- owns changes that alter external-communication policy or package capabilities.

### MANAGER
- may coordinate configured scheduled-task deliveries and surface blockers;
- verifies destination, task identity, and project binding before posting;
- folds material Slack decisions back into project state for Primary disposition.

### RESEARCH
- may publish scheduled research summaries only to preconfigured destinations;
- does not infer destinations or treat Slack reactions/messages as accepted project state without the normal review path.

## Recommended dynamic-run sequence

`SCHEDULE TRIGGER -> PROJECT BINDING -> READ CANONICAL STATE -> EXECUTE TASK -> VALIDATE -> PERSIST CANONICAL RESULT -> SLACK DELIVERY -> RECORD DELIVERY STATUS`

## Failure handling

- Scheduler failure: no Slack success message.
- Project persistence failure: do not announce the result as completed; post a blocker/failure only if configured.
- Slack failure after successful persistence: retain canonical success, record `DELIVERY_FAILED`, and retry/notify according to policy.
- Duplicate invocation: use task/idempotency identity to avoid duplicate canonical results and duplicate Slack completion posts.
