# Scheduled Swarm Checkpoint Bus Rollout Record

Date: 2026-10-05
Authorized by: Robert Leonard at 04:26 America/Vancouver
Branch: `fix/swarm-checkpoint-transport-v1`
Target: `main`

## Incident addressed

A scheduled Researcher completed useful read-only research but could not persist the required durable project checkpoint because the scheduled invocation lacked the project-native AgentBus/Library write surface. GitHub write-safety correctly prevented treating production/source mutation as an ad-hoc checkpoint fallback. The task therefore reported failure even though substantive research had succeeded.

## Implemented repair

1. Added `protocols/swarm_checkpoint_bus.md`.
2. Added machine-readable `research_swarm/checkpoint_envelope.schema.json`.
3. Added reference validation/fencing helpers in `org_agent_mesh/checkpoint_bus.py`.
4. Added unit tests in `tests/test_checkpoint_bus.py`.
5. Created append-only GitHub issue #25 as the scheduled serial-pipeline checkpoint transport.
6. Verified issue-comment append + independent readback using a non-checkpoint transport canary.
7. Updated `research_swarm/five_task_schedule.json` from v3 to v4 so Manager accepts either `RESEARCH_PROGRESS` or `RESEARCH_HANDOFF_READY`, and Primary accepts either `MANAGER_PROGRESS` or `MANAGER_HANDOFF_READY`.
8. Updated Researcher, Manager, and Primary canonical scheduled prompts to preflight checkpoint transport before expensive work, use append-only issue comments, externally verify readback, reject stale cross-cycle state, and preserve partial progress.
9. Preserved human-only schedule activation. No task enablement is authorized by this rollout record.
10. Preserved project evidence/source authority: issue #25 carries compact stage handoff state only and does not replace project-native technical evidence.

## Transport verification

A non-checkpoint issue comment was appended to issue #25 and fetched back successfully through the connected GitHub app. Downstream readers are explicitly instructed to ignore comments without the `SWARM_STAGE_CHECKPOINT` marker.

## Required deployment sequence

1. PR validation / complete test suite.
2. Merge to `main` only if validation passes.
3. Align saved scheduled-task prompts to the merged canonical prompts while preserving each task's current enabled/disabled state.
4. Confirm live task states remain unchanged by prompt alignment.
5. Perform a canary run only through explicit human task execution/enablement; this implementation authority does not itself authorize changing disabled tasks to enabled.

## Acceptance checks

- checkpoint comment append/readback works;
- partial Researcher progress is a valid Manager input;
- partial Manager progress is a valid Primary input;
- stale prior-cycle state is not selected;
- conflicting sequence reuse fails closed;
- checkpoint preflight happens before expensive work;
- scheduled prompts preserve human-only activation and no clone fallback;
- issue #25 is coordination transport only, not production authority.
