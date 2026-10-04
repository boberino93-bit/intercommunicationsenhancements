# `.swarm/` Project-Local Runtime Namespace

Reserved for Swarm Launch Kernel records. Use sharded immutable/per-task records, never one shared mutable state file. All records are scoped to this project and a `global_run_id`. Foreign projects may only read published health telemetry where policy permits. GitHub writers use create-if-absent and blob-SHA/expected-version updates; stale writes reread/reconcile/back off; never force-push.
