#!/usr/bin/env python3
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ROLES = {"PRIMARY": "ORCHESTRATOR", "MANAGER": "REVIEWER", "RESEARCH": "SPECIALIST"}
IDENTITY_LOCK = "PROJECT_IDENTITY_LOCK.json"
BOOTSTRAP_ORDER = "BOOTSTRAP_ORDER.json"
COORDINATION_SNAPSHOT = ".interagent/directives/2026-10-03-project-identity-recovery.json"
SHARED = [
    IDENTITY_LOCK, BOOTSTRAP_ORDER, COORDINATION_SNAPSHOT, "bootstrap/IDENTITY_GATE.md", "bootstrap/RECOVERY.md",
    "PROJECT_MANIFEST.json", "PROJECT_CHARTER.md", "ARCHITECTURE.md", "START_HERE.md", "VERSION",
    "protocols/project_isolation.md", "protocols/cross_project_exchange.md", "protocols/deployment_package_sync.md",
    "protocols/recursive_self_enhancement.md", "protocols/slack_scheduled_tasks.md",
    "schemas/message.schema.json", "schemas/agent_record.schema.json", "schemas/presence_frame.schema.json",
    "schemas/agent_package_manifest.schema.json", "schemas/cross_project_exchange.schema.json",
    "schemas/enhancement_candidate.schema.json", "schemas/scheduled_task_route.schema.json",
    "org_agent_mesh/constants.py", "org_agent_mesh/project_scope.py", "org_agent_mesh/project_identity.py",
    "org_agent_mesh/message_bus.py", "org_agent_mesh/cross_project.py", "org_agent_mesh/package_manifest.py",
    "org_agent_mesh/self_enhancement.py", "org_agent_mesh/scheduled_tasks.py"
]


def sha256(path):
    digest = hashlib.sha256()
    digest.update(Path(path).read_bytes())
    return digest.hexdigest()


def checked_out_revision():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.STDOUT
        ).strip().lower()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("cannot determine checked-out source revision") from exc


def validate_source_revision(source_revision):
    revision = str(source_revision).strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("source_revision must be a full 40-character Git commit SHA")
    actual = checked_out_revision()
    if revision != actual:
        raise ValueError(f"declared source revision {revision} does not match checked-out revision {actual}")
    return revision


def load_control_state():
    project = json.loads((ROOT / "PROJECT_MANIFEST.json").read_text(encoding="utf-8"))
    identity = json.loads((ROOT / IDENTITY_LOCK).read_text(encoding="utf-8"))
    bootstrap = json.loads((ROOT / BOOTSTRAP_ORDER).read_text(encoding="utf-8"))
    if identity.get("mode") != "FAIL_CLOSED" or bootstrap.get("mode") != "FAIL_CLOSED":
        raise ValueError("identity controls must be FAIL_CLOSED")
    if project["project_id"] != identity["project_id"]:
        raise ValueError("project manifest and identity lock disagree on project_id")
    if project["repository_identity"] != identity["writable_repository"]:
        raise ValueError("project manifest and identity lock disagree on writable repository")
    steps = [item.get("id") for item in bootstrap.get("steps", [])]
    required_prefix = [
        "validate_current_human_project_intent",
        "load_and_validate_project_identity_lock",
    ]
    if steps[:2] != required_prefix:
        raise ValueError("bootstrap order does not establish project identity first")
    return project, identity


def build(out_dir, source_revision):
    source_revision = validate_source_revision(source_revision)
    project, identity = load_control_state()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for role, tier in ROLES.items():
        package_version = project["framework_version"]
        role_files = [f"roles/{role}.md", f"bootstrap/{role}.md"]
        components = SHARED + role_files
        component_sha256 = {rel: sha256(ROOT / rel) for rel in components}
        manifest = {
            "schema": "org-agent-mesh/agent-package-manifest/v2",
            "project_id": project["project_id"],
            "repository_identity": identity["writable_repository"],
            "canonical_branch": identity["canonical_branch"],
            "coordination_root": identity["coordination_root"],
            "artifact_root": identity["artifact_root"],
            "identity_lock_path": IDENTITY_LOCK,
            "bootstrap_order_path": BOOTSTRAP_ORDER,
            "coordination_snapshot_path": COORDINATION_SNAPSHOT,
            "agent_spawn_policy": identity["agent_spawn_policy"],
            "deployment_role": role,
            "authority_tier": tier,
            "framework_version": project["framework_version"],
            "protocol_version": project["protocol_version"],
            "package_version": package_version,
            "source_revision": source_revision,
            "identity_artifact_sha256": {
                IDENTITY_LOCK: component_sha256[IDENTITY_LOCK],
                BOOTSTRAP_ORDER: component_sha256[BOOTSTRAP_ORDER],
                COORDINATION_SNAPSHOT: component_sha256[COORDINATION_SNAPSHOT]
            },
            "component_sha256": component_sha256,
            "included_components": components
        }
        path = out / f"{project['project_id']}-{role.lower()}-{package_version}.zip"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("AGENT_PACKAGE_MANIFEST.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
            for rel in components:
                archive.write(ROOT / rel, rel)
        results.append({"path": str(path), "sha256": sha256(path), "manifest": manifest})
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(ROOT / "dist"))
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.out, args.source_revision), indent=2))
