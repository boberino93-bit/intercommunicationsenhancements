# Scheduler recovery qualification

A mapped frontend scheduler lane is not healthy merely because its task exists, is enabled, accepts a run request, or has one recent successful execution.

Health qualification requires the latest mature scheduled occurrence and the two immediately preceding mature occurrences to each have an exact verified execution receipt. A mature occurrence is one whose schedule time plus its configured grace window has elapsed.

States:

- `HEALTHY`: three consecutive mature occurrences are verified.
- `RECOVERING`: the latest mature occurrence is verified but fewer than three consecutive mature occurrences are verified.
- `DEGRADED_MISSING_EXECUTION_EVIDENCE`: the latest mature occurrence lacks exact verified execution evidence.
- `UNQUALIFIED`: required mapping or supported schedule information is missing.

The independent backend scheduler must report degraded health when evidence is absent. Zero rejected receipts is not equivalent to successful execution, and `FRONTEND_EXECUTION_EXPECTED` is not execution proof.
