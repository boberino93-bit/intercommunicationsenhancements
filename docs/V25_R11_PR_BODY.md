# V25 R11 Bootstrap Upgrade Candidate

## Scope

Reversible candidate-branch integration of V25 R11 bootstrap semantics. No merge and no canonical promotion.

## Changes

- Initialize embedded VMBUS before project binding.
- Require `VMBUS_READY` and `PRINCIPAL_CONTEXT_READY` before project binding/task interpretation.
- Keep corrected R10 user context distinct from revisable R11 model-synthesis hypotheses.
- Treat external GitHub and Artifactory/message-board services as optional post-readiness mirrors in the candidate.
- Preserve mirror conflicts and require logical-record plus payload-digest equality for equivalence claims.
- Make nightly Research/Manager/Primary sequencing checkpoint/readiness-gated rather than clock-trusted.
- Record scheduler-disabled-by-default migration posture, with `VMBUS Defrag` as the explicit enabled exception.

## Runtime limitation

No Artifactory/JFrog connector is exposed in the current runtime. No Artifactory write/readback is claimed. GitHub coordination records are mirror-only.

## Promotion boundary

`main` remains unchanged. Merge/canonical promotion requires a separate authorization case and any stronger proof required by active repository governance.
