#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.constants import DEPLOYMENT_ROLES
from org_agent_mesh.package_manifest import validate_agent_package_manifest

PROJECT = json.loads((ROOT / "PROJECT_MANIFEST.json").read_text(encoding="utf-8"))
IDENTITY = json.loads((ROOT / "PROJECT_IDENTITY_LOCK.json").read_text(encoding="utf-8"))
BOOTSTRAP = json.loads((ROOT / "BOOTSTRAP_ORDER.json").read_text(encoding="utf-8"))
errors = []
packages = sorted((ROOT / "dist").glob("*.zip"))
if not packages:
    errors.append("no deployment ZIP packages found")


def digest_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


def checked_out_revision():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip().lower()


EXPECTED_REVISION = checked_out_revision()
EXPECTED_PREFIX = [
    "validate_current_human_project_intent",
    "load_and_validate_project_identity_lock",
]
if [step.get("id") for step in BOOTSTRAP.get("steps", [])][:2] != EXPECTED_PREFIX:
    errors.append("repository bootstrap order is not identity-first")

seen_roles = set()
source_revisions = set()
for path in packages:
    try:
        with zipfile.ZipFile(path) as archive:
            raw_names = archive.namelist()
            names = set(raw_names)
            if len(raw_names) != len(names):
                raise ValueError("archive contains duplicate path entries")
            if "AGENT_PACKAGE_MANIFEST.json" not in names:
                raise ValueError("manifest missing")
            manifest = json.loads(archive.read("AGENT_PACKAGE_MANIFEST.json"))
            validate_agent_package_manifest(
                manifest,
                expected_project_id=PROJECT["project_id"],
                expected_repository_identity=PROJECT["repository_identity"],
                expected_coordination_root=IDENTITY["coordination_root"],
            )
            role = manifest["deployment_role"]
            if role in seen_roles:
                raise ValueError(f"duplicate deployment role package: {role}")
            seen_roles.add(role)
            source_revisions.add(manifest["source_revision"])

            if manifest["source_revision"] != EXPECTED_REVISION:
                raise ValueError("package source revision does not match checked-out revision")
            if manifest["identity_lock_path"] != "PROJECT_IDENTITY_LOCK.json":
                raise ValueError("unexpected project identity lock path")
            if manifest["bootstrap_order_path"] != "BOOTSTRAP_ORDER.json":
                raise ValueError("unexpected bootstrap order path")

            components = list(manifest["included_components"])
            if len(components) != len(set(components)):
                raise ValueError("manifest contains duplicate included components")
            expected_names = set(components) | {"AGENT_PACKAGE_MANIFEST.json"}
            if names != expected_names:
                missing = sorted(expected_names - names)
                extra = sorted(names - expected_names)
                raise ValueError(f"package file set mismatch; missing={missing} extra={extra}")
            if set(manifest["component_sha256"]) != set(components):
                raise ValueError("component hash index does not match included components")

            expected_role_files = {f"roles/{role}.md", f"bootstrap/{role}.md"}
            if not expected_role_files.issubset(names):
                raise ValueError(f"role bootstrap/instructions missing for {role}")
            foreign_role_files = {
                f"roles/{other}.md" for other in DEPLOYMENT_ROLES if other != role
            } | {
                f"bootstrap/{other}.md" for other in DEPLOYMENT_ROLES if other != role
            }
            leaked = foreign_role_files & names
            if leaked:
                raise ValueError(f"foreign role-specific instructions present: {sorted(leaked)}")

            for rel in components:
                actual_hash = digest_bytes(archive.read(rel))
                expected_hash = manifest["component_sha256"].get(rel)
                if actual_hash != expected_hash:
                    raise ValueError(f"component checksum mismatch: {rel}")

            packaged_identity = json.loads(archive.read(manifest["identity_lock_path"]))
            if packaged_identity["mode"] != "FAIL_CLOSED":
                raise ValueError("packaged identity lock is not FAIL_CLOSED")
            if packaged_identity["project_id"] != PROJECT["project_id"]:
                raise ValueError("packaged identity lock project mismatch")
            if packaged_identity["writable_repository"] != PROJECT["repository_identity"]:
                raise ValueError("packaged identity lock repository mismatch")
            if packaged_identity["coordination_root"] != IDENTITY["coordination_root"]:
                raise ValueError("packaged coordination root mismatch")

            packaged_bootstrap = json.loads(archive.read(manifest["bootstrap_order_path"]))
            prefix = [step.get("id") for step in packaged_bootstrap.get("steps", [])][:2]
            if prefix != EXPECTED_PREFIX:
                raise ValueError("packaged bootstrap order is not identity-first")

            identity_hashes = manifest["identity_artifact_sha256"]
            for rel in (manifest["identity_lock_path"], manifest["bootstrap_order_path"], manifest["coordination_snapshot_path"]):
                if identity_hashes.get(rel) != manifest["component_sha256"].get(rel):
                    raise ValueError(f"identity artifact hash mismatch: {rel}")

            expected_filename = f"{PROJECT['project_id']}-{role.lower()}-{PROJECT['framework_version']}.zip"
            if path.name != expected_filename:
                raise ValueError(f"unexpected package filename: {path.name!r} != {expected_filename!r}")
    except Exception as exc:
        errors.append(f"{path.name}: {exc}")

expected_roles = set(DEPLOYMENT_ROLES)
if seen_roles != expected_roles:
    errors.append(f"deployment role set mismatch: found {sorted(seen_roles)}, expected {sorted(expected_roles)}")
if len(packages) != len(expected_roles):
    errors.append(f"expected exactly {len(expected_roles)} deployment ZIPs, found {len(packages)}")
if len(source_revisions) > 1:
    errors.append(f"coordinated release packages disagree on source revision: {sorted(source_revisions)}")

if errors:
    print("\n".join(errors))
    raise SystemExit(1)
print("agent package verification PASS")
