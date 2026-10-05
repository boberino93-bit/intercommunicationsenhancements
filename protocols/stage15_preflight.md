# Stage 15 Preflight Protocol

Status: ACTIVE FAIL-CLOSED
Scope: evidence preparation before any separately authorized Stage-15 launch.

## Readiness states

Keep these states separate:

- `CONTRACT_READY`: seven-project launch contracts are aligned.
- `PREFLIGHT_READY`: fresh project-bound capacity, operations, and kernel-preflight evidence is complete for the intended run.
- `STAGE_PASSED`: a live stage completed and post-run convergence checks passed.

None of these states conveys execution authority or authorizes launch.

## Capacity evidence

For every participating project, resolve one `org-agent-mesh/capacity-signal/v1` record and verify:

- exact canonical project ID;
- exact repository identity;
- timezone-aware timestamp;
- age no greater than 900 seconds;
- not future-dated beyond configured skew;
- admissible state `GREEN`.

Missing, stale, future, `UNKNOWN`, non-GREEN, project-mismatched, or repository-mismatched capacity evidence blocks preflight.

Do not replace missing evidence with a caller-supplied boolean.

## Operations evidence

Require one fresh attributable operations observation per project. Canonical project accounting uses `xrp-thesis`. The legacy observed ID `xrpthesis` may be mapped only through the explicit registry alias and must remain visibly `normalized:false` until the source project completes normalization.

## Evidence envelope

Use `org_agent_mesh.stage15_preflight` and `schemas/stage15_evidence.schema.json` to assemble one deterministic envelope for exactly the seven registered projects and one global run ID.

The envelope binds project ID, repository, source revision, capacity evidence, operations evidence, and kernel preflight result. Its digest may be used as non-authoritative regression evidence.

`authority_conveyed=false` and `launch_authorized=false` are invariant.

## Launch boundary

Preflight completion does not launch Stage 15, does not pass Stage 15, does not activate the scaler, and does not raise any provider, specialist, schedule, or mutation limit. A live Stage-15 run requires a separate valid authorization case.
