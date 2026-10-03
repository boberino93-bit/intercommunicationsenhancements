#!/usr/bin/env python3
from pathlib import Path
import json
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.constants import DEPLOYMENT_ROLES
from org_agent_mesh.package_manifest import validate_agent_package_manifest

PROJECT = json.loads((ROOT / "PROJECT_MANIFEST.json").read_text())
errors = []
packages = sorted((ROOT / "dist").glob("*.zip"))
if not packages:
    errors.append("no deployment ZIP packages found")

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
            validate_agent_package_manifest(manifest, expected_project_id=PROJECT["project_id"])

            role = manifest["deployment_role"]
            if role in seen_roles:
                raise ValueError(f"duplicate deployment role package: {role}")
            seen_roles.add(role)
            source_revisions.add(manifest["source_revision"])

            included = manifest["included_components"]
            if len(included) != len(set(included)):
                raise ValueError("manifest contains duplicate included components")
            expected_names = set(included) | {"AGENT_PACKAGE_MANIFEST.json"}
            missing = expected_names - names
            extra = names - expected_names
            if missing:
                raise ValueError(f"missing included components: {sorted(missing)}")
            if extra:
                raise ValueError(f"undeclared/foreign package contents: {sorted(extra)}")

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
