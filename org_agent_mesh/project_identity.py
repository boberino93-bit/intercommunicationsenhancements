from pathlib import Path
import json

from .project_scope import ProjectScopeError, require_project_id, require_project_path

IDENTITY_LOCK_FILENAME = "PROJECT_IDENTITY_LOCK.json"


def load_identity_lock(project_root):
    root = Path(project_root).resolve()
    path = require_project_path(root, root / IDENTITY_LOCK_FILENAME)
    if not path.is_file():
        raise ProjectScopeError("project identity lock missing")
    lock = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "schema", "mode", "project_id", "project_name", "writable_repository",
        "coordination_root", "identity_lock_path", "bootstrap_order_path"
    }
    missing = sorted(required - set(lock))
    if missing:
        raise ProjectScopeError(f"project identity lock missing fields: {missing}")
    if lock["mode"] != "FAIL_CLOSED":
        raise ProjectScopeError("project identity lock must be FAIL_CLOSED")
    require_project_id(lock["project_id"])
    return lock


def validate_current_project(project_root, current_project_id, expected_repository_identity=None):
    selected = require_project_id(current_project_id)
    lock = load_identity_lock(project_root)
    if selected != lock["project_id"]:
        raise ProjectScopeError("current project does not match local identity lock")
    if expected_repository_identity is not None and lock["writable_repository"] != expected_repository_identity:
        raise ProjectScopeError("writable repository does not match local identity lock")
    return lock
