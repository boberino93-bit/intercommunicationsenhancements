# Slack Scheduled-Task Transport Protocol v1

Slack is an optional transport for scheduled-task coordination and delivery. It is not canonical project state and it is not the scheduler for dynamic agent work. Dynamic launches also follow `protocols/scheduled_agent_launch.md`.

## Two scheduling modes

1. **Dynamic scheduled work** — use the task scheduler/automation to invoke the agent at the requested cadence. At configuration time, capture the exact project-bound launch context from the local `AGENT_BOOTSTRAP.json`; at execution time the run verifies that context, completes bootstrap, performs its project work, persists canonical evidence/state in the bound project, then may send a Slack summary or link.
2. **Static scheduled message** — when no computation or state inspection is required at delivery time, Slack's native scheduled-message capability may be used directly. Static messages do not launch an agent and therefore use `STATIC_MESSAGE_ONLY` context binding.

Do not use a pre-scheduled Slack message as a substitute for a dynamic task that must inspect current state at execution time.

## Project-context and provider-admission boundary

Dynamic scheduled work must not rely on the chat title, recent conversation topic, or semantic similarity to recover its project. The scheduled instruction carries the machine-readable project launch context generated from `ScheduledTaskRoute` and the future run validates it against the project's local contract before mutation.

Provider admission happens before the model run when the hosting scheduler/dispatcher supports it. Use bounded concurrency, start spacing, deterministic staggering and bounded exponential backoff for retryable pre-bootstrap failures. A `TOO_MANY_REQUESTS`/rate-limit rejection is a launch failure, not a project task failure; the logical occurrence remains pending and retains the same idempotency identity across retry.

If the host cannot run admission logic before model invocation, configure deterministic schedule staggering and a retry/reconciliation path. An agent that never started cannot self-retry a provider rejection.

## Canonical-state rule

- Artifactory/GitHub/project artifacts remain the durable source of truth.
- Slack messages are notifications, summaries, requests, or human-facing handoff surfaces.
- A Slack delivery failure does not erase or roll back a successfully persisted task result. Record delivery failure separately and retry only under the task's retry policy.
- Material decisions received in Slack must be folded back into canonical project state before they are treated as accepted project truth.
- A scheduler firing does not advance project task state. Scheduled task execution state may advance only after the project-bound run reaches `BOOTSTRAP_READY`.

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
- ensures dynamic scheduled tasks capture exact project launch context and preserve canonical-state-before-notification ordering;
- owns changes that alter external-communication policy or package capabilities.

### MANAGER
- may coordinate configured scheduled-task deliveries and surface blockers;
- verifies destination, task identity, project launch context and project binding before posting;
- folds material Slack decisions back into project state for Primary disposition.

### RESEARCH
- may publish scheduled research summaries only to preconfigured destinations;
- does not infer destinations or treat Slack reactions/messages as accepted project state without the normal review path.

## Recommended dynamic-run sequence

`SCHEDULE TRIGGER -> PROVIDER ADMISSION -> PROVIDER ACCEPTED -> VERIFY PROJECT LAUNCH CONTEXT -> PROJECT BOOTSTRAP -> BOOTSTRAP_READY -> READ CANONICAL STATE -> EXECUTE TASK -> VALIDATE -> PERSIST CANONICAL RESULT -> SLACK DELIVERY -> RECORD DELIVERY STATUS`

## Failure handling

- Provider admission/backpressure wait: do not start another model run yet; retain pending occurrence.
- `TOO_MANY_REQUESTS`, rate limit, temporary provider unavailability, or timeout before bootstrap: retry under bounded backoff; do not mark project work failed or completed.
- Launch-context mismatch: stop before project mutation and surface a launch failure; never infer a replacement project.
- Scheduler failure: no Slack success message.
- Project persistence failure: do not announce the result as completed; post a blocker/failure only if configured.
- Slack failure after successful persistence: retain canonical success, record `DELIVERY_FAILED`, and retry/notify according to policy.
- Duplicate invocation: use occurrence/task/idempotency identity to avoid duplicate canonical results and duplicate Slack completion posts.
