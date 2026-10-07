# Scheduler common-mode recovery boundary

The Bootstrap Spawn Bridge and Swarm Capacity Slot 1 are separate ChatGPT Scheduled Task identities but share the same ChatGPT scheduling and execution provider. They are therefore redundant identities, not independent failure domains.

If one task identity fails while the provider remains healthy, the other declared repair actor may restore exact mapped enablement under the scoped human repair grant. If the provider stops dispatching both tasks, neither task can autonomously repair the other because neither receives execution time.

The independent GitHub Internal Spawn Scheduler is a separate clock and detection surface. It can prove canonical occurrences are due and detect missing frontend execution evidence. It must not claim that a frontend task executed merely because execution was expected.

A genuinely independent automatic recovery path requires an out-of-band actuation interface or host adapter capable of starting the bounded worker without relying on ChatGPT Scheduled Tasks. The current deployment does not have such an actuator configured. Until one exists, common-mode frontend provider outages are `CAPABILITY_BLOCKED` for automatic recovery and must remain visibly degraded rather than being reported healthy.
