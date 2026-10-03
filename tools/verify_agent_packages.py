#!/usr/bin/env python3
from pathlib import Path
import json
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.package_manifest import validate_agent_package_manifest

PROJECT = json.loads((ROOT / "PROJECT_MANIFEST.json").read_text())
errors = []
packages = sorted((ROOT / "dist").glob("*.zip"))
if not packages:
    errors.append("no deployment ZIP packages found")

for path in packages:
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            if "AGENT_PACKAGE_MANIFEST.json" not in names:
                raise ValueError("manifest missing")
            manifest = json.loads(archive.read("AGENT_PACKAGE_MANIFEST.json"))
            validate_agent_package_manifest(manifest, expected_project_id=PROJECT["project_id"])
            missing = set(manifest["included_components"]) - names
            if missing:
                raise ValueError(f"missing included components: {sorted(missing)}")
    except Exception as exc:
        errors.append(f"{path.name}: {exc}")

if errors:
    print("\n".join(errors))
    raise SystemExit(1)
print("agent package verification PASS")
