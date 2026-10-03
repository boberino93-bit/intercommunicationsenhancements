#!/usr/bin/env python3
from pathlib import Path
import argparse
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ROLES = {"PRIMARY": "ORCHESTRATOR", "MANAGER": "REVIEWER", "RESEARCH": "SPECIALIST"}
SHARED = [
    "PROJECT_MANIFEST.json", "PROJECT_CHARTER.md", "START_HERE.md", "VERSION",
    "protocols/project_isolation.md", "protocols/cross_project_exchange.md", "protocols/deployment_package_sync.md",
    "schemas/message.schema.json", "schemas/agent_record.schema.json", "schemas/presence_frame.schema.json",
    "schemas/agent_package_manifest.schema.json", "schemas/cross_project_exchange.schema.json",
    "org_agent_mesh/constants.py", "org_agent_mesh/project_scope.py", "org_agent_mesh/message_bus.py",
    "org_agent_mesh/cross_project.py", "org_agent_mesh/package_manifest.py"
]


def sha256(path):
    digest = hashlib.sha256()
    digest.update(Path(path).read_bytes())
    return digest.hexdigest()


def build(out_dir, source_revision):
    project = json.loads((ROOT / "PROJECT_MANIFEST.json").read_text())
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for role, tier in ROLES.items():
        package_version = project["framework_version"]
        manifest = {
            "schema": "org-agent-mesh/agent-package-manifest/v1",
            "project_id": project["project_id"],
            "deployment_role": role,
            "authority_tier": tier,
            "framework_version": project["framework_version"],
            "protocol_version": project["protocol_version"],
            "package_version": package_version,
            "source_revision": source_revision,
            "included_components": SHARED + [f"roles/{role}.md"]
        }
        path = out / f"{project['project_id']}-{role.lower()}-{package_version}.zip"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("AGENT_PACKAGE_MANIFEST.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
            for rel in manifest["included_components"]:
                archive.write(ROOT / rel, rel)
        results.append({"path": str(path), "sha256": sha256(path), "manifest": manifest})
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(ROOT / "dist"))
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.out, args.source_revision), indent=2))
