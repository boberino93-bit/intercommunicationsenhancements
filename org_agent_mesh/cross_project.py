from .project_scope import ProjectScopeError, require_project_id

REQUIRED_EXCHANGE_FIELDS = {
    "schema", "exchange_id", "source_project_id", "destination_project_id", "requesting_agent_id",
    "purpose", "data_classification", "requested_artifacts", "allowed_use", "created_at_utc",
    "expires_at_utc", "correlation_id", "approval"
}


def validate_cross_project_exchange(exchange, *, has_cross_project_capability=False):
    missing = sorted(REQUIRED_EXCHANGE_FIELDS - set(exchange))
    if missing:
        raise ValueError(f"Cross-project exchange missing fields: {missing}")
    src = require_project_id(exchange["source_project_id"])
    dst = require_project_id(exchange["destination_project_id"])
    if src == dst:
        raise ValueError("Cross-project exchange requires distinct projects")
    if not has_cross_project_capability:
        raise ProjectScopeError("Cross-project exchange denied by default")
    approval = exchange.get("approval") or {}
    if approval.get("status") != "APPROVED":
        raise ProjectScopeError("Cross-project exchange requires explicit approval")
    return True
