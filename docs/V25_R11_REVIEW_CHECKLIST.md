# V25 R11 Candidate Review Checklist

Before any merge or canonical promotion:

- [ ] Confirm `VMBUS_READY` occurs before project binding.
- [ ] Confirm `PRINCIPAL_CONTEXT_READY` occurs before project binding and task interpretation.
- [ ] Confirm R10 user-context and R11 model-synthesis remain distinct epistemic classes.
- [ ] Confirm R11 synthesis remains revisable and non-authoritative.
- [ ] Confirm unavailable external services do not block standalone bootstrap.
- [ ] Confirm mirror equivalence requires logical-record and payload-digest equality.
- [ ] Confirm conflicts are preserved and surfaced rather than silently overwritten.
- [ ] Confirm no GitHub record is represented as proof of an Artifactory write.
- [ ] Confirm no Artifactory write/readback is claimed while runtime connector is unavailable.
- [ ] Confirm scheduled pipeline ordering is checkpoint/readiness gated rather than clock-trusted.
- [ ] Confirm all exposed scheduled tasks remain disabled except `VMBUS Defrag`.
- [ ] Confirm `main` is unchanged until a separate promotion case is authorized.
- [ ] Run repository tests and any new candidate-specific validation before promotion.
