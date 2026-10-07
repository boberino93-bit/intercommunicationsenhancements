# Scheduler health enforcement fix — 2026-10-07

This change closes the observability gap that allowed the independent backend scheduler to remain green while mapped ChatGPT Scheduled Tasks missed occurrences.

## Enforced behavior

1. Exact frontend execution receipts are still validated for identity and timing.
2. The health evaluator derives the latest mature occurrences from the canonical registry and configured grace windows.
3. A missing receipt for the latest mature occurrence is `DEGRADED_MISSING_EXECUTION_EVIDENCE`.
4. One successful occurrence is only `RECOVERING`.
5. Three consecutive mature verified occurrences are required for `HEALTHY`.
6. The independent scheduler workflow exits non-zero when mapped frontend health is not qualified, while still preserving the occurrence/health artifacts with `if: always()`.
7. Disabled standby lanes are excluded from active health.
8. The common-mode limitation is explicit: the Bootstrap Bridge and Slot 1 share the same frontend provider and cannot be represented as independent provider failover.

## Remaining external dependency

True automatic recovery from a common-mode ChatGPT Scheduled Tasks outage requires an out-of-band actuator/host adapter. The repository's independent GitHub clock can detect and prove missing execution evidence, but the currently exposed runtime does not provide GitHub with authority/API access to mutate ChatGPT Scheduled Tasks directly. This condition must report degraded/capability-blocked rather than healthy.
