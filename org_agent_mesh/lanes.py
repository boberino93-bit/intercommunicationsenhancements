from .project_scope import require_project_id


def claim_lane(existing_claims, claim, allow_replication=False):
    required = {
        "project_id", "lane_id", "assignment", "scope", "starting_project_state",
        "expected_output", "dependencies", "possible_overlap", "current_status",
        "agent_id", "agent_instance_id"
    }
    missing = required - set(claim)
    if missing:
        raise ValueError(f"Lane claim missing: {sorted(missing)}")

    project_id = require_project_id(claim["project_id"])
    active = {"OPEN", "ACTIVE", "BLOCKED"}
    conflicts = [
        existing for existing in existing_claims
        if existing.get("project_id") == project_id
        and existing.get("lane_id") == claim["lane_id"]
        and existing.get("current_status") in active
        and existing.get("agent_instance_id") != claim["agent_instance_id"]
    ]

    if conflicts and not allow_replication:
        raise RuntimeError(
            "Active lane already claimed in this project; reconcile overlap or explicitly authorize independent replication"
        )

    result = dict(claim)
    result["replication_mode"] = bool(allow_replication and conflicts)
    return result
