#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
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
DEPENDENCY_MAP = "packaging/agent_package_dependencies.json"
SWARM_MEMORY_POLICY = "governance/SWARM_MEMORY_PERSISTENCE_POLICY.json"
AGENT_CONTEXT_REFERENCE = "AGENT_CONTEXT_REFERENCE.md"
V26_MANIFEST = "PROJECT_MANIFEST_V26.json"
V26_ADAPTER = "bootstrap/V26_BOOTSTRAP_ADAPTER.json"
V26_ARTIFACT_SHA256 = "122e73dc7ba01384d799fc508c337081948ae1714f869a318d2ab96cd142d778"
V26_PREFIX = [
    "load_v26_canonical_bootstrap_adapter",
    "enter_unbound_read_only_and_initialize_validate_vmbus",
    "require_vmbus_ready",
    "load_principal_context_layers_build_indexes_and_require_principal_context_ready",
    "bind_host_chat_project_context_after_v26_readiness",
]


def sha256(path):
    digest = hashlib.sha256(); digest.update(Path(path).read_bytes()); return digest.hexdigest()


def checked_out_revision():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip().lower()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("cannot determine checked-out source revision") from exc


def commit_timestamp():
    try:
        raw = subprocess.check_output(["git", "show", "-s", "--format=%cI", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        raise RuntimeError("cannot determine checked-out commit timestamp") from exc
    if parsed.tzinfo is None: raise RuntimeError("commit timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def validate_source_revision(source_revision):
    revision = str(source_revision).strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", revision): raise ValueError("source_revision must be a full 40-character Git commit SHA")
    actual = checked_out_revision()
    if revision != actual: raise ValueError(f"declared source revision {revision} does not match checked-out revision {actual}")
    return revision


def _contract_version(value):
    try:
        parts = tuple(int(part) for part in str(value).split("."))
    except ValueError as exc:
        raise ValueError("invalid bootstrap routing_contract_version") from exc
    if len(parts) != 3 or any(part < 0 for part in parts): raise ValueError("invalid bootstrap routing_contract_version")
    return parts


def _validate_bootstrap_safety_mode(bootstrap):
    mode = bootstrap.get("mode")
    if mode == "FAIL_CLOSED":
        return
    version = _contract_version(bootstrap.get("routing_contract_version", "0.0.0"))
    if mode != "FAIL_CLOSED_LOCAL_CONTINUE_GLOBAL" or version < (1, 5, 0):
        raise ValueError("bootstrap control mode is not fail-closed")
    continuation = bootstrap.get("continuation_contract")
    if not isinstance(continuation, dict): raise ValueError("routing 1.5 bootstrap missing continuation_contract")
    expected = {
        "routine_confirmation": "DENY",
        "fail_closed_scope": "AFFECTED_MUTATION_OR_BRANCH_ONLY",
        "continue_unaffected_safe_work": True,
        "human_escalation": "TRUE_HUMAN_GATE_ONLY",
    }
    for key, value in expected.items():
        if continuation.get(key) != value:
            raise ValueError(f"unsafe routing 1.5 bootstrap continuation setting: {key}")


def _validate_v26_generation(project, bootstrap, dependency_map, v26_manifest, v26_adapter):
    if project.get("canonical_bootstrap_generation") != "V26":
        raise ValueError("root project manifest does not declare V26 canonical bootstrap generation")
    if project.get("canonical_generation_manifest") != V26_MANIFEST:
        raise ValueError("root project manifest V26 generation manifest pointer mismatch")
    if project.get("canonical_bootstrap_adapter") != V26_ADAPTER:
        raise ValueError("root project manifest V26 adapter pointer mismatch")
    if bootstrap.get("canonical_bootstrap_generation") != "V26":
        raise ValueError("bootstrap order does not declare V26 canonical generation")
    steps = [item.get("id") for item in bootstrap.get("steps", [])]
    if steps[:len(V26_PREFIX)] != V26_PREFIX:
        raise ValueError("bootstrap order does not establish V26 VMBUS/principal-context readiness before project binding")
    contract = bootstrap.get("v26_canonical_contract", {})
    if not contract.get("vmbus_ready_before_project_bind") or not contract.get("principal_context_ready_before_project_bind"):
        raise ValueError("V26 bootstrap readiness barriers are incomplete")
    if contract.get("v25_r11_active_bootstrap") is not False:
        raise ValueError("V25 R11 must not remain active bootstrap after V26 promotion")
    if v26_manifest.get("version") != "V26" or v26_manifest.get("status") != "CANONICAL_ACTIVE" or not v26_manifest.get("canonical_promotion"):
        raise ValueError("V26 manifest is not canonical active")
    if v26_manifest.get("artifact", {}).get("sha256") != V26_ARTIFACT_SHA256:
        raise ValueError("V26 artifact digest mismatch")
    if v26_manifest.get("project_sharing_boundary", {}).get("cv_support_federated") is not False:
        raise ValueError("CV Support must remain non-federated")
    if v26_adapter.get("version") != "V26" or v26_adapter.get("status") != "CANONICAL_ACTIVE_ON_MAIN":
        raise ValueError("V26 bootstrap adapter is not canonical active")
    hard = set(v26_adapter.get("hard_invariants", []))
    for invariant in ("VMBUS_READY_BEFORE_PROJECT_BIND", "PRINCIPAL_CONTEXT_READY_BEFORE_PROJECT_BIND", "CV_SUPPORT != FEDERATED_PROJECT", "INTERCOMMUNICATION_ENHANCEMENTS = ONLY_SHARED_COORDINATION_PROJECT"):
        if invariant not in hard:
            raise ValueError(f"V26 bootstrap adapter missing invariant: {invariant}")
    if dependency_map.get("canonical_bootstrap_generation") != "V26":
        raise ValueError("package dependency map does not declare V26")
    required = set(dependency_map.get("required_v26_components", []))
    if {V26_MANIFEST, V26_ADAPTER} - required:
        raise ValueError("package dependency map does not require both V26 canonical components")


def _validate_swarm_memory_policy(policy):
    if policy.get("schema") != "org-agent-mesh/swarm-memory-persistence-policy/v1":
        raise ValueError("unsupported swarm memory persistence policy schema")
    if policy.get("policy_id") != "IEP-MEM-001":
        raise ValueError("unexpected swarm memory persistence policy id")
    if policy.get("status") != "ACTIVE" or policy.get("priority") != "P1":
        raise ValueError("swarm memory persistence policy must be ACTIVE P1")

    native = policy.get("native_chatgpt_memory")
    if not isinstance(native, dict):
        raise ValueError("swarm memory persistence policy missing native_chatgpt_memory controls")
    expected_native = {
        "swarm_authority": "DENY",
        "protocol_access": "MUST_NOT_CALL",
        "recall_ingestion": "DENY",
        "fallback": "DENY",
        "cache_source": "DENY",
        "log_source": "DENY",
        "collective_state_source": "DENY",
        "mutation_authority": "DENY",
    }
    for key, value in expected_native.items():
        if native.get(key) != value:
            raise ValueError(f"unsafe native ChatGPT memory policy setting: {key}")

    persistence = policy.get("canonical_persistence")
    if not isinstance(persistence, dict):
        raise ValueError("swarm memory persistence policy missing canonical_persistence")
    artifactory = persistence.get("artifactory", {})
    github = persistence.get("github", {})
    if artifactory.get("message_board") != "/Intercommunication enhancements/AgentBus/messages":
        raise ValueError("swarm memory policy canonical coordination board mismatch")
    if github.get("repository") != "boberino93-bit/intercommunicationsenhancements":
        raise ValueError("swarm memory policy GitHub repository mismatch")

    failure = policy.get("failure_policy", {})
    if failure.get("native_memory_fallback") != "DENY":
        raise ValueError("swarm memory policy must deny native-memory fallback")

    context = (ROOT / AGENT_CONTEXT_REFERENCE).read_text(encoding="utf-8")
    for marker in (
        "P1 external-only swarm memory",
        "MUST_NOT_CALL_NATIVE_CHATGPT_MEMORY",
        "DO_NOT_FALL_BACK_TO_NATIVE_MEMORY",
    ):
        if marker not in context:
            raise ValueError(f"fresh-agent context missing swarm memory P1 marker: {marker}")


def load_control_state():
    project = json.loads((ROOT / "PROJECT_MANIFEST.json").read_text(encoding="utf-8"))
    identity = json.loads((ROOT / IDENTITY_LOCK).read_text(encoding="utf-8"))
    bootstrap = json.loads((ROOT / BOOTSTRAP_ORDER).read_text(encoding="utf-8"))
    dependency_map = json.loads((ROOT / DEPENDENCY_MAP).read_text(encoding="utf-8"))
    memory_policy = json.loads((ROOT / SWARM_MEMORY_POLICY).read_text(encoding="utf-8"))
    v26_manifest = json.loads((ROOT / V26_MANIFEST).read_text(encoding="utf-8"))
    v26_adapter = json.loads((ROOT / V26_ADAPTER).read_text(encoding="utf-8"))
    if identity.get("mode") != "FAIL_CLOSED": raise ValueError("identity control must be FAIL_CLOSED")
    _validate_bootstrap_safety_mode(bootstrap)
    _validate_v26_generation(project, bootstrap, dependency_map, v26_manifest, v26_adapter)
    _validate_swarm_memory_policy(memory_policy)
    if project["project_id"] != identity["project_id"]: raise ValueError("project manifest and identity lock disagree on project_id")
    if project["repository_identity"] != identity["writable_repository"]: raise ValueError("project manifest and identity lock disagree on writable repository")
    if dependency_map.get("schema") != "org-agent-mesh/package-dependency-map/v1": raise ValueError("unsupported package dependency map schema")
    return project, identity, dependency_map


def expand_patterns(patterns):
    components = set()
    for pattern in patterns:
        matches = sorted(path for path in ROOT.glob(pattern) if path.is_file())
        if not matches: raise ValueError(f"package dependency pattern matched no files: {pattern}")
        components.update(path.relative_to(ROOT).as_posix() for path in matches)
    return sorted(components)


def components_for_role(dependency_map, role):
    role_components = dependency_map.get("role_components", {}).get(role)
    if not role_components: raise ValueError(f"package dependency map missing role components for {role}")
    components = set(expand_patterns(dependency_map.get("shared_patterns", [])))
    for rel in role_components:
        path = ROOT / rel
        if not path.is_file(): raise ValueError(f"role component missing: {rel}")
        components.add(rel)
    required_v26 = set(dependency_map.get("required_v26_components", []))
    if required_v26 - components:
        raise ValueError(f"role package dependency closure missing V26 components: {sorted(required_v26 - components)}")
    return sorted(components)


def _zip_timestamp(value):
    value = value.astimezone(timezone.utc); second = value.second - (value.second % 2)
    return (max(value.year, 1980), value.month, value.day, value.hour, value.minute, second)


def _write_zip_bytes(archive, name, payload, timestamp):
    info = zipfile.ZipInfo(name, date_time=_zip_timestamp(timestamp)); info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = (0o644 & 0xFFFF) << 16; info.create_system = 3
    archive.writestr(info, payload)


def _clean_output(out):
    out.mkdir(parents=True, exist_ok=True)
    for path in out.glob("*.zip"): path.unlink()
    release_set = out / "release-set.json"
    if release_set.exists(): release_set.unlink()


def build(out_dir, source_revision):
    source_revision = validate_source_revision(source_revision)
    project, identity, dependency_map = load_control_state(); out = Path(out_dir); _clean_output(out)
    built_at = commit_timestamp(); built_at_utc = built_at.isoformat().replace("+00:00", "Z"); dependency_hash = sha256(ROOT / DEPENDENCY_MAP)
    role_capabilities = identity.get("authority_model", {}).get("role_capabilities", {}); results = []
    for role, tier in ROLES.items():
        package_version = project["framework_version"]; components = components_for_role(dependency_map, role); component_sha256 = {rel: sha256(ROOT / rel) for rel in components}
        capabilities = role_capabilities.get(role)
        if not isinstance(capabilities, list): raise ValueError(f"identity lock missing role capabilities for {role}")
        manifest = {"schema":"org-agent-mesh/agent-package-manifest/v3","project_id":project["project_id"],"repository_identity":identity["writable_repository"],"canonical_branch":identity["canonical_branch"],"coordination_root":identity["coordination_root"],"artifact_root":identity["artifact_root"],"identity_lock_path":IDENTITY_LOCK,"bootstrap_order_path":BOOTSTRAP_ORDER,"dependency_map_path":DEPENDENCY_MAP,"dependency_map_sha256":dependency_hash,"canonical_bootstrap_generation":"V26","v26_manifest_path":V26_MANIFEST,"v26_adapter_path":V26_ADAPTER,"agent_spawn_policy":identity["agent_spawn_policy"],"deployment_role":role,"authority_tier":tier,"capabilities":sorted(set(capabilities)),"framework_version":project["framework_version"],"protocol_version":project["protocol_version"],"package_version":package_version,"built_at_utc":built_at_utc,"source_revision":source_revision,"component_sha256":component_sha256,"included_components":components}
        path = out / f"{project['project_id']}-{role.lower()}-{package_version}.zip"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            _write_zip_bytes(archive, "AGENT_PACKAGE_MANIFEST.json", (json.dumps(manifest, indent=2, sort_keys=True)+"\n").encode("utf-8"), built_at)
            for rel in components: _write_zip_bytes(archive, rel, (ROOT / rel).read_bytes(), built_at)
        results.append({"path":str(path),"sha256":sha256(path),"manifest":manifest})
    release_set = {"schema":"org-agent-mesh/release-set/v1","project_id":project["project_id"],"framework_version":project["framework_version"],"protocol_version":project["protocol_version"],"canonical_bootstrap_generation":"V26","source_revision":source_revision,"built_at_utc":built_at_utc,"dependency_map_sha256":dependency_hash,"packages":[{"deployment_role":item["manifest"]["deployment_role"],"filename":Path(item["path"]).name,"sha256":item["sha256"]} for item in sorted(results,key=lambda item:item["manifest"]["deployment_role"])]}
    (out / "release-set.json").write_text(json.dumps(release_set, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return results


if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--out",default=str(ROOT/"dist")); parser.add_argument("--source-revision",required=True); args=parser.parse_args(); print(json.dumps(build(args.out,args.source_revision),indent=2))
