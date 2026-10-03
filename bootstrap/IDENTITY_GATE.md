# Identity Gate

Before role-specific startup, execute `BOOTSTRAP_ORDER.json`.

The first two completed checks must be:

1. current project intent is explicit;
2. `PROJECT_IDENTITY_LOCK.json` matches that project and is `FAIL_CLOSED`.

Only then may package validation, execution binding, project policy loading, and continuation-state loading proceed. If the project is not explicit or the local lock disagrees, no project mutation is permitted.
