from datetime import datetime, timezone

from .control_plane import require_active_session
from .project_scope import ProjectScopeError, require_project_id, require_resource_id

REQUIRED_EXCHANGE_FIELDS = {
    "schema", "exchange_id", "source_project_id", "destination_project_id", "requesting_agent_id",
    "purpose", "data_classification", "requested_artifacts", "allowed_use", "created_at_utc",
    "expires_at_utc", "correlation_id", "approval"
}


def _parse_utc(value, field):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def validate_cross_project_exchange(exchange, *, requester_session, now=None):
    if not isinstance(exchange, dict):
        raise ValueError("cross-project exchange must be an object")
    missing = sorted(REQUIRED_EXCHANGE_FIELDS - set(exchange))
    if missing:
        raise ValueError(f"Cross-project exchange missing fields: {missing}")
    src = require_project_id(exchange["source_project_id"])
    dst = require_project_id(exchange["destination_project_id"])
    if src == dst:
        raise ValueError("Cross-project exchange requires distinct projects")

    binding = require_active_session(
        requester_session,
        src,
        operation="cross-project exchange request",
        capability="CROSS_PROJECT_EXCHANGE",
    )
    if exchange["requesting_agent_id"] != binding.agent_id:
        raise ProjectScopeError("cross-project requesting agent does not match bound session")

    require_resource_id(exchange["exchange_id"], field="exchange_id")
    require_resource_id(exchange["correlation_id"], field="correlation_id")
    if not isinstance(exchange["requested_artifacts"], list):
        raise ValueError("requested_artifacts must be a list")
    for artifact_id in exchange["requested_artifacts"]:
        require_resource_id(artifact_id, field="requested artifact id")

    created = _parse_utc(exchange["created_at_utc"], "created_at_utc")
    expires = _parse_utc(exchange["expires_at_utc"], "expires_at_utc")
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    current = current.astimezone(timezone.utc)
    if expires <= created:
        raise ValueError("cross-project exchange expiry must be after creation")
    if expires <= current:
        raise ProjectScopeError("cross-project exchange is expired")

    approval = exchange.get("approval") or {}
    if approval.get("status") != "APPROVED" or not approval.get("approved_by"):
        raise ProjectScopeError("Cross-project exchange requires explicit approval")
    return True
