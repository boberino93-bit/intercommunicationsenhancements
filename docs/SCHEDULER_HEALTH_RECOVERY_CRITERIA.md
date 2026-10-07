# Scheduler recovery qualification

A mapped frontend scheduler lane is not healthy merely because its task exists, is enabled, accepts a run request, or has one recent successful execution.

Health qualification requires the latest health-mature scheduled occurrence and the two immediately preceding health-mature occurrences to each have an exact verified execution receipt.

An occurrence is **not** health-mature merely when the job's normal scheduler grace expires. Health maturity must allow the full valid evidence path to complete. The current contract uses:

- frontend receipt maximum start delay: 30 minutes;
- receipt persistence grace: 5 minutes;
- health evidence deadline: 35 minutes;
- job scheduler grace: still enforced independently for scheduling, but it cannot shorten the health evidence deadline.

Therefore absence of a receipt before the 35-minute evidence deadline is pending evidence, not a missing-execution failure. Once that deadline passes, an absent exact receipt is degraded.

States:

- `HEALTHY`: three consecutive health-mature occurrences are verified.
- `RECOVERING`: the latest health-mature occurrence is verified but fewer than three consecutive health-mature occurrences are verified.
- `DEGRADED_MISSING_EXECUTION_EVIDENCE`: the latest health-mature occurrence lacks exact verified execution evidence.
- `UNQUALIFIED`: required mapping, supported schedule information, or coherent health/receipt timing policy is missing.

The independent backend scheduler must report degraded health when mature evidence is absent. Zero rejected receipts is not equivalent to successful execution, and `FRONTEND_EXECUTION_EXPECTED` is not execution proof.

Scheduler health is also an additional work-admission restriction. `RECOVERING`, `DEGRADED_MISSING_EXECUTION_EVIDENCE`, and `UNQUALIFIED` lanes may perform read-only diagnostics/research and append-only observability or checkpoint persistence, but may not perform reversible or protected project mutation. `HEALTHY` only allows progression to the normal project/role/claim/consequence/mutation gates; it does not grant mutation authority itself.
