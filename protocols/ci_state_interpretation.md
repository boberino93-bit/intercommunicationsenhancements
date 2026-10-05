# CI State Interpretation Protocol

Status: ACTIVE
Scope: Universal validation/reporting
Regression family: CI_STATE_INTERPRETATION

## Invariant

Workflow state is evidence about execution state, not a substitute for test results.

Agents MUST distinguish:

- `queued`: validation has not started; no pass/fail conclusion exists.
- `in_progress`: validation is executing; no final conclusion exists.
- `cancelled`: execution stopped; cancelled jobs are not test failures and are not passes.
- `skipped`: the job did not execute; no pass/fail result may be inferred for its checks.
- `failure`: inspect the job and step results before attributing the failure to tests, policy, infrastructure, packaging, or another cause.
- `success`: only checks that actually executed and completed successfully may be represented as passing.

A workflow-level `failure` caused by cancelled prerequisites or skipped dependent jobs MUST NOT be described as a failing test suite unless an executed test step actually failed.

Before using CI as a promotion decision, inspect the exact commit SHA, workflow attempt, jobs, and—when needed—step/log evidence. Independent validation may supplement hosted CI but must be described separately and may not be silently presented as hosted-CI success.

This protocol does not weaken any policy that explicitly requires hosted CI success. It improves evidence classification only and grants no merge, mutation, or bypass authority.
