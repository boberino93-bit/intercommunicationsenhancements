from .constants import FRAMEWORK_VERSION, PROTOCOL_VERSION, DEPLOYMENT_ROLES
from .project_scope import ProjectScopeError, require_project_id

REQUIRED = {
    "schema", "project_id", "deployment_role", "authority_tier", "framework_version",
    "protocol_version", "package_version", "source_revision", "included_components"
}


def validate_agent_package_manifest(manifest, *, expected_project_id=None, expected_protocol_version=PROTOCOL_VERSION):
    missing = sorted(REQUIRED - set(manifest))
    if missing:
        raise ValueError(f"Agent package manifest missing fields: {missing}")
    project_id = require_project_id(manifest["project_id"])
    if expected_project_id is not None and project_id != expected_project_id:
        raise ProjectScopeError("Foreign deployment package")
    if manifest["deployment_role"] not in DEPLOYMENT_ROLES:
        raise ValueError("Unsupported deployment role")
    if manifest["protocol_version"] != expected_protocol_version:
        raise ValueError("Stale or incompatible deployment package protocol")
    if manifest["framework_version"] != FRAMEWORK_VERSION:
        raise ValueError("Deployment package framework version mismatch")
    return True
