from datetime import datetime
import re

from .constants import CAPABILITIES, FRAMEWORK_VERSION, PROTOCOL_VERSION, DEPLOYMENT_ROLES
from .project_scope import ProjectScopeError, require_project_id, require_repository_identity

REQUIRED = {
    "schema", "project_id", "repository_identity", "canonical_branch", "coordination_root",
    "artifact_root", "identity_lock_path", "bootstrap_order_path", "dependency_map_path",
    "dependency_map_sha256", "agent_spawn_policy", "deployment_role", "authority_tier",
    "capabilities", "framework_version", "protocol_version", "package_version",
    "built_at_utc", "source_revision", "component_sha256", "included_components"
}

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def validate_agent_package_manifest(manifest, *, expected_project_id=None, expected_repository_identity=None, expected_coordination_root=None, expected_protocol_version=PROTOCOL_VERSION):
    missing = sorted(REQUIRED - set(manifest))
    if missing:
        raise ValueError(f"Agent package manifest missing fields: {missing}")
    if manifest["schema"] != "org-agent-mesh/agent-package-manifest/v3":
        raise ValueError("Unsupported agent package manifest schema")
    project_id = require_project_id(manifest["project_id"])
    repository_identity = require_repository_identity(manifest["repository_identity"])
    if expected_project_id is not None and project_id != expected_project_id:
        raise ProjectScopeError("Foreign deployment package")
    if expected_repository_identity is not None and repository_identity != expected_repository_identity:
        raise ProjectScopeError("Deployment package repository identity mismatch")
    if expected_coordination_root is not None and manifest["coordination_root"] != expected_coordination_root:
        raise ProjectScopeError("Deployment package coordination root mismatch")
    if manifest["deployment_role"] not in DEPLOYMENT_ROLES:
        raise ValueError("Unsupported deployment role")
    if manifest["protocol_version"] != expected_protocol_version:
        raise ValueError("Stale or incompatible deployment package protocol")
    if manifest["framework_version"] != FRAMEWORK_VERSION:
        raise ValueError("Deployment package framework version mismatch")
    if manifest["package_version"] != manifest["framework_version"]:
        raise ValueError("Deployment package version must match framework release version")
    if not _COMMIT_RE.fullmatch(str(manifest["source_revision"]).lower()):
        raise ValueError("Deployment package source revision must be a full Git SHA")
    if not _SHA256_RE.fullmatch(str(manifest["dependency_map_sha256"]).lower()):
        raise ValueError("Deployment package dependency map hash is invalid")
    try:
        built_at = datetime.fromisoformat(str(manifest["built_at_utc"]).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Deployment package built_at_utc is invalid") from exc
    if built_at.tzinfo is None:
        raise ValueError("Deployment package built_at_utc must be timezone-aware")
    capabilities = manifest["capabilities"]
    if not isinstance(capabilities, list) or len(capabilities) != len(set(capabilities)):
        raise ValueError("Deployment package capabilities must be a unique list")
    unknown = set(capabilities) - set(CAPABILITIES)
    if unknown:
        raise ValueError(f"Deployment package contains unknown capabilities: {sorted(unknown)}")
    component_hashes = manifest["component_sha256"]
    if not isinstance(component_hashes, dict) or not component_hashes:
        raise ValueError("Deployment package component hashes are required")
    if any(not _SHA256_RE.fullmatch(str(value).lower()) for value in component_hashes.values()):
        raise ValueError("Deployment package component hash is invalid")
    if not isinstance(manifest["agent_spawn_policy"], dict):
        raise ValueError("Deployment package agent spawn policy is required")
    if not isinstance(manifest["included_components"], list) or not manifest["included_components"]:
        raise ValueError("Deployment package included_components are required")
    return True
