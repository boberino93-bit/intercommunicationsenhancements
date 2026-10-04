import hmac
import json

from .scheduled_tasks import LAUNCH_CONTEXT_SCHEMA, ScheduledLaunchContext, ScheduledTaskRouteError


BEGIN_MARKER = "ORG_AGENT_MESH_PROJECT_LAUNCH_CONTEXT"
END_MARKER = "END_ORG_AGENT_MESH_PROJECT_LAUNCH_CONTEXT"

_ALLOWED_KEYS = frozenset({
    "schema",
    "mode",
    "project_id",
    "task_id",
    "role_id",
    "repository_identity",
    "repository_id",
    "forum_namespace",
    "artifact_namespace",
    "routing_contract_version",
    "local_contract_path",
    "bootstrap_order_path",
    "launch_source",
    "occurrence_id",
    "route_id",
    "context_fingerprint",
})


class ScheduledLaunchContextParseError(ScheduledTaskRouteError):
    pass


def _extract_single_block(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        raise ScheduledLaunchContextParseError("scheduled launch text is required")

    lines = text.splitlines()
    begin_indexes = [index for index, line in enumerate(lines) if line.strip() == BEGIN_MARKER]
    end_indexes = [index for index, line in enumerate(lines) if line.strip() == END_MARKER]
    if len(begin_indexes) != 1 or len(end_indexes) != 1:
        raise ScheduledLaunchContextParseError(
            "scheduled launch text must contain exactly one project launch context block"
        )

    begin_index = begin_indexes[0]
    end_index = end_indexes[0]
    if end_index <= begin_index + 1:
        raise ScheduledLaunchContextParseError("scheduled launch context markers are malformed")

    payload = "\n".join(lines[begin_index + 1:end_index]).strip()
    if not payload:
        raise ScheduledLaunchContextParseError("scheduled launch context payload is empty")
    return payload


def parse_project_launch_context(text: str) -> ScheduledLaunchContext:
    """
    Parse and integrity-check the machine-readable context embedded in a
    scheduled agent instruction.

    Fingerprint validation detects accidental/tampered payload drift. It is not
    an authorization signature; callers must still validate the resulting
    context against the target project's local bootstrap contract.
    """
    raw = _extract_single_block(text)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ScheduledLaunchContextParseError("scheduled launch context is not valid JSON") from exc

    if not isinstance(payload, dict):
        raise ScheduledLaunchContextParseError("scheduled launch context must be a JSON object")
    unknown = set(payload) - _ALLOWED_KEYS
    if unknown:
        raise ScheduledLaunchContextParseError(
            f"scheduled launch context contains unsupported fields: {sorted(unknown)}"
        )
    if payload.get("schema") != LAUNCH_CONTEXT_SCHEMA:
        raise ScheduledLaunchContextParseError("unsupported scheduled launch context schema")
    if payload.get("mode") != "PROJECT_BOUND":
        raise ScheduledLaunchContextParseError("scheduled launch context must be PROJECT_BOUND")

    claimed_fingerprint = payload.get("context_fingerprint")
    if not isinstance(claimed_fingerprint, str) or len(claimed_fingerprint) != 64:
        raise ScheduledLaunchContextParseError("scheduled launch context fingerprint is required")

    required = (
        "project_id",
        "task_id",
        "role_id",
        "forum_namespace",
        "artifact_namespace",
        "routing_contract_version",
        "local_contract_path",
        "bootstrap_order_path",
        "launch_source",
    )
    missing = [name for name in required if name not in payload]
    if missing:
        raise ScheduledLaunchContextParseError(
            f"scheduled launch context is missing required fields: {missing}"
        )

    try:
        context = ScheduledLaunchContext(
            project_id=payload["project_id"],
            task_id=payload["task_id"],
            role_id=payload["role_id"],
            repository_identity=payload.get("repository_identity"),
            repository_id=payload.get("repository_id"),
            forum_namespace=payload["forum_namespace"],
            artifact_namespace=payload["artifact_namespace"],
            routing_contract_version=payload["routing_contract_version"],
            local_contract_path=payload["local_contract_path"],
            bootstrap_order_path=payload["bootstrap_order_path"],
            launch_source=payload["launch_source"],
            occurrence_id=payload.get("occurrence_id"),
            route_id=payload.get("route_id"),
        )
    except (TypeError, ValueError, PermissionError) as exc:
        raise ScheduledLaunchContextParseError("scheduled launch context failed structural validation") from exc

    if not hmac.compare_digest(context.fingerprint, claimed_fingerprint):
        raise ScheduledLaunchContextParseError("scheduled launch context fingerprint mismatch")
    return context
