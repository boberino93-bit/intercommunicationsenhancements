from .constants import FRAMEWORK_VERSION, PROTOCOL_VERSION, DEPLOYMENT_ROLES
from .project_scope import ProjectScopeError, require_project_id

REQUIRED = {
    "schema", "project_id", "repository_identity", "canonical_branch", "coordination_root",
    "artifact_root", "identity_lock_path", "bootstrap_order_path", "coordination_snapshot_path",
    "agent_spawn_policy", "deployment_role", "authority_tier", "framework_version",
    "protocol_version", "package_version", "source_revision", "identity_artifact_sha256",
    "component_sha256", "included_components"
}


def validate_agent_package_manifest(
    manifest,
    *,
    expected_project_id=None,
    expected_repository_identity=None,
    expected_coordination_root=None,
    expected_protocol_version=PROTOCOL_VERSION,
):
    missing = sorted(REQUIRED - set(manifest))
    if missing:
        raise ValueError(f"Agent package manifest missing fields: {missing}")
    if manifest["schema"] != "org-agent-mesh/agent-package-manifest/v2":
        raise ValueError("Unsupported agent package manifest schema")
    project_id = require_project_id(manifest["project_id"])
    if expected_project_id is not None and project_id != expected_project_id:
        raise ProjectScopeError("Foreign deployment package")
    if expected_repository_identity is not None and manifest["repository_identity"] != expected_repository_identity:
        raise ProjectScopeError("Deployment package repository identity mismatch")
    if expected_coordination_root is not None and manifest["coordination_root"] != expected_coordination_root:
        raise ProjectScopeError("Deployment package coordination root mismatch")
    if manifest["deployment_role"] not in DEPLOYMENT_ROLES:
        raise ValueError("Unsupported deployment role")
    if manifest["protocol_version"] != expected_protocol_version:
        raise ValueError("Stale or incompatible deployment package protocol")
    if manifest["framework_version"] != FRAMEWORK_VERSION:
        raise ValueError("Deployment package framework version mismatch")
    if not isinstance(manifest["component_sha256"], dict) or not manifest["component_sha256"]:
        raise ValueError("Deployment package component hashes are required")
    if not isinstance(manifest["identity_artifact_sha256"], dict) or not manifest["identity_artifact_sha256"]:
        raise ValueError("Deployment package identity artifact hashes are required")
    if not isinstance(manifest["agent_spawn_policy"], dict):
        raise ValueError("Deployment package agent spawn policy is required")
    return True
