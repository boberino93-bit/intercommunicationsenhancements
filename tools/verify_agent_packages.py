#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from org_agent_mesh.constants import DEPLOYMENT_ROLES
from org_agent_mesh.package_manifest import validate_agent_package_manifest

PROJECT=json.loads((ROOT/"PROJECT_MANIFEST.json").read_text(encoding="utf-8")); IDENTITY=json.loads((ROOT/"PROJECT_IDENTITY_LOCK.json").read_text(encoding="utf-8")); BOOTSTRAP=json.loads((ROOT/"BOOTSTRAP_ORDER.json").read_text(encoding="utf-8")); DEPENDENCY_MAP_PATH=ROOT/"packaging"/"agent_package_dependencies.json"; DEPENDENCY_MAP=json.loads(DEPENDENCY_MAP_PATH.read_text(encoding="utf-8")); V26_MANIFEST=json.loads((ROOT/"PROJECT_MANIFEST_V26.json").read_text(encoding="utf-8")); V26_ADAPTER=json.loads((ROOT/"bootstrap"/"V26_BOOTSTRAP_ADAPTER.json").read_text(encoding="utf-8")); errors=[]; packages=sorted((ROOT/"dist").glob("*.zip"))
if not packages: errors.append("no deployment ZIP packages found")

def digest_bytes(payload): return hashlib.sha256(payload).hexdigest()
def digest_file(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def checked_out_revision(): return subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip().lower()
def expand_patterns(patterns):
    components=set()
    for pattern in patterns:
        matches=sorted(path for path in ROOT.glob(pattern) if path.is_file())
        if not matches: raise ValueError(f"package dependency pattern matched no files: {pattern}")
        components.update(path.relative_to(ROOT).as_posix() for path in matches)
    return sorted(components)
def expected_components(role):
    components=set(expand_patterns(DEPENDENCY_MAP.get("shared_patterns",[]))); role_files=DEPENDENCY_MAP.get("role_components",{}).get(role)
    if not role_files: raise ValueError(f"package dependency map missing role components for {role}")
    for rel in role_files:
        if not (ROOT/rel).is_file(): raise ValueError(f"role component missing: {rel}")
        components.add(rel)
    required=set(DEPENDENCY_MAP.get("required_v26_components",[]))
    if required-components: raise ValueError(f"V26 dependency closure missing: {sorted(required-components)}")
    return sorted(components)

EXPECTED_REVISION=checked_out_revision(); EXPECTED_DEPENDENCY_HASH=digest_file(DEPENDENCY_MAP_PATH); EXPECTED_PREFIX=["load_v26_canonical_bootstrap_adapter","enter_unbound_read_only_and_initialize_validate_vmbus","require_vmbus_ready","load_principal_context_layers_build_indexes_and_require_principal_context_ready","bind_host_chat_project_context_after_v26_readiness"]
if [step.get("id") for step in BOOTSTRAP.get("steps",[])][:len(EXPECTED_PREFIX)] != EXPECTED_PREFIX: errors.append("repository bootstrap order is not V26 readiness-first")
if BOOTSTRAP.get("canonical_bootstrap_generation") != "V26": errors.append("repository bootstrap generation is not V26")
if PROJECT.get("canonical_bootstrap_generation") != "V26": errors.append("root project manifest does not declare V26")
if PROJECT.get("canonical_generation_manifest") != "PROJECT_MANIFEST_V26.json": errors.append("root project manifest V26 manifest pointer mismatch")
if PROJECT.get("canonical_bootstrap_adapter") != "bootstrap/V26_BOOTSTRAP_ADAPTER.json": errors.append("root project manifest V26 adapter pointer mismatch")
if V26_MANIFEST.get("version") != "V26" or V26_MANIFEST.get("status") != "CANONICAL_ACTIVE" or V26_MANIFEST.get("canonical_promotion") is not True: errors.append("V26 manifest is not canonical active")
if V26_ADAPTER.get("version") != "V26" or V26_ADAPTER.get("status") != "CANONICAL_ACTIVE_ON_MAIN": errors.append("V26 adapter is not canonical active")
if DEPENDENCY_MAP.get("schema") != "org-agent-mesh/package-dependency-map/v1": errors.append("unsupported package dependency map schema")
if DEPENDENCY_MAP.get("canonical_bootstrap_generation") != "V26": errors.append("package dependency map generation is not V26")
seen_roles=set(); source_revisions=set(); package_hashes={}
for path in packages:
    try:
        with zipfile.ZipFile(path) as archive:
            raw_names=archive.namelist(); names=set(raw_names)
            if len(raw_names)!=len(names): raise ValueError("archive contains duplicate path entries")
            if "AGENT_PACKAGE_MANIFEST.json" not in names: raise ValueError("manifest missing")
            manifest=json.loads(archive.read("AGENT_PACKAGE_MANIFEST.json")); validate_agent_package_manifest(manifest,expected_project_id=PROJECT["project_id"],expected_repository_identity=PROJECT["repository_identity"],expected_coordination_root=IDENTITY["coordination_root"])
            role=manifest["deployment_role"]
            if role in seen_roles: raise ValueError(f"duplicate deployment role package: {role}")
            seen_roles.add(role); source_revisions.add(manifest["source_revision"])
            if manifest["source_revision"] != EXPECTED_REVISION: raise ValueError("package source revision does not match checked-out revision")
            if manifest["identity_lock_path"] != "PROJECT_IDENTITY_LOCK.json": raise ValueError("unexpected project identity lock path")
            if manifest["bootstrap_order_path"] != "BOOTSTRAP_ORDER.json": raise ValueError("unexpected bootstrap order path")
            if manifest["dependency_map_path"] != "packaging/agent_package_dependencies.json": raise ValueError("unexpected package dependency map path")
            if manifest["dependency_map_sha256"] != EXPECTED_DEPENDENCY_HASH: raise ValueError("package dependency map hash mismatch")
            if manifest.get("canonical_bootstrap_generation") != "V26": raise ValueError("package manifest does not declare V26")
            if manifest.get("v26_manifest_path") != "PROJECT_MANIFEST_V26.json": raise ValueError("package V26 manifest pointer mismatch")
            if manifest.get("v26_adapter_path") != "bootstrap/V26_BOOTSTRAP_ADAPTER.json": raise ValueError("package V26 adapter pointer mismatch")
            components=list(manifest["included_components"])
            if len(components)!=len(set(components)): raise ValueError("manifest contains duplicate included components")
            expected_for_role=expected_components(role)
            if components != expected_for_role:
                missing=sorted(set(expected_for_role)-set(components)); extra=sorted(set(components)-set(expected_for_role)); raise ValueError(f"manifest dependency expansion mismatch; missing={missing} extra={extra}")
            expected_names=set(components)|{"AGENT_PACKAGE_MANIFEST.json"}
            if names != expected_names: raise ValueError(f"package file set mismatch; missing={sorted(expected_names-names)} extra={sorted(names-expected_names)}")
            if set(manifest["component_sha256"]) != set(components): raise ValueError("component hash index does not match included components")
            expected_role_files={f"roles/{role}.md",f"bootstrap/{role}.md"}
            if not expected_role_files.issubset(names): raise ValueError(f"role bootstrap/instructions missing for {role}")
            if not {"PROJECT_MANIFEST_V26.json","bootstrap/V26_BOOTSTRAP_ADAPTER.json"}.issubset(names): raise ValueError("V26 canonical components missing from package")
            foreign={f"roles/{other}.md" for other in DEPLOYMENT_ROLES if other!=role}|{f"bootstrap/{other}.md" for other in DEPLOYMENT_ROLES if other!=role}
            if foreign & names: raise ValueError(f"foreign role-specific instructions present: {sorted(foreign & names)}")
            expected_capabilities=sorted(set(IDENTITY["authority_model"]["role_capabilities"][role]))
            if manifest["capabilities"] != expected_capabilities: raise ValueError(f"role capability set mismatch for {role}")
            for rel in components:
                actual_hash=digest_bytes(archive.read(rel)); expected_hash=manifest["component_sha256"].get(rel)
                if actual_hash != expected_hash: raise ValueError(f"component checksum mismatch: {rel}")
                if actual_hash != digest_file(ROOT/rel): raise ValueError(f"packaged component drifts from repository source: {rel}")
            packaged_identity=json.loads(archive.read(manifest["identity_lock_path"]))
            if packaged_identity["mode"]!="FAIL_CLOSED" or packaged_identity["project_id"]!=PROJECT["project_id"] or packaged_identity["writable_repository"]!=PROJECT["repository_identity"] or packaged_identity["coordination_root"]!=IDENTITY["coordination_root"]: raise ValueError("packaged identity lock mismatch")
            packaged_bootstrap=json.loads(archive.read(manifest["bootstrap_order_path"])); prefix=[step.get("id") for step in packaged_bootstrap.get("steps",[])][:len(EXPECTED_PREFIX)]
            if prefix != EXPECTED_PREFIX: raise ValueError("packaged bootstrap order is not V26 readiness-first")
            if packaged_bootstrap.get("canonical_bootstrap_generation") != "V26": raise ValueError("packaged bootstrap generation is not V26")
            packaged_v26_manifest=json.loads(archive.read("PROJECT_MANIFEST_V26.json")); packaged_v26_adapter=json.loads(archive.read("bootstrap/V26_BOOTSTRAP_ADAPTER.json"))
            if packaged_v26_manifest.get("status") != "CANONICAL_ACTIVE": raise ValueError("packaged V26 manifest is not active")
            if packaged_v26_adapter.get("status") != "CANONICAL_ACTIVE_ON_MAIN": raise ValueError("packaged V26 adapter is not active")
            expected_filename=f"{PROJECT['project_id']}-{role.lower()}-{PROJECT['framework_version']}.zip"
            if path.name != expected_filename: raise ValueError(f"unexpected package filename: {path.name!r} != {expected_filename!r}")
            package_hashes[role]=digest_file(path)
    except Exception as exc: errors.append(f"{path.name}: {exc}")
expected_roles=set(DEPLOYMENT_ROLES)
if seen_roles != expected_roles: errors.append(f"deployment role set mismatch: found {sorted(seen_roles)}, expected {sorted(expected_roles)}")
if len(packages)!=len(expected_roles): errors.append(f"expected exactly {len(expected_roles)} deployment ZIPs, found {len(packages)}")
if len(source_revisions)>1: errors.append(f"coordinated release packages disagree on source revision: {sorted(source_revisions)}")
release_path=ROOT/"dist"/"release-set.json"
if not release_path.is_file(): errors.append("release-set.json missing")
else:
    try:
        release=json.loads(release_path.read_text(encoding="utf-8"))
        if release.get("schema")!="org-agent-mesh/release-set/v1": raise ValueError("unsupported release set schema")
        if release.get("project_id")!=PROJECT["project_id"]: raise ValueError("release set project mismatch")
        if release.get("source_revision")!=EXPECTED_REVISION: raise ValueError("release set source revision mismatch")
        if release.get("framework_version")!=PROJECT["framework_version"]: raise ValueError("release set framework version mismatch")
        if release.get("protocol_version")!=PROJECT["protocol_version"]: raise ValueError("release set protocol version mismatch")
        if release.get("canonical_bootstrap_generation")!="V26": raise ValueError("release set generation is not V26")
        if release.get("dependency_map_sha256")!=EXPECTED_DEPENDENCY_HASH: raise ValueError("release set dependency map hash mismatch")
        release_packages={item["deployment_role"]:item for item in release.get("packages",[])}
        if set(release_packages)!=expected_roles: raise ValueError("release set role set mismatch")
        for role in expected_roles:
            item=release_packages[role]; expected_name=f"{PROJECT['project_id']}-{role.lower()}-{PROJECT['framework_version']}.zip"
            if item.get("filename")!=expected_name: raise ValueError(f"release set filename mismatch for {role}")
            if item.get("sha256")!=package_hashes.get(role): raise ValueError(f"release set archive hash mismatch for {role}")
    except Exception as exc: errors.append(f"release-set.json: {exc}")
if errors:
    print("\n".join(errors)); raise SystemExit(1)
print("agent package verification PASS: V26 canonical alignment")
