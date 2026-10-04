"""Design-only validation harness for IPG3 artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def validate_json_schemas() -> list[str]:
    failures = []
    try:
        from jsonschema.validators import Draft202012Validator
    except ImportError as exc:
        return [f"jsonschema dependency unavailable: {exc}"]
    for path in sorted(ROOT.glob("*.draft.schema.json")):
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            failures.append(f"{path.name}: {exc}")
    return failures


def validate_isolation() -> list[str]:
    failures = []
    package_map = json.loads((REPO / "packaging" / "agent_package_dependencies.json").read_text(encoding="utf-8"))
    shared_patterns = set(package_map.get("shared_patterns", []))
    if "design/*" in shared_patterns or "design/**" in shared_patterns:
        failures.append("design/ is included in authoritative deployment dependency closure")
    for path in ROOT.glob("*"):
        if path.is_file() and path.name.startswith(("message-v3", "delegation-contract", "effect-receipt", "human-approval", "trust-provenance", "causal-event", "evolution-candidate", "benchmark-result", "progress-ledger", "cross-project-exchange")):
            if path.parent.name != "design":
                failures.append(f"draft artifact escaped design/: {path}")
    return failures


def run_unittests() -> list[str]:
    failures = []
    for name in ("test_shadow_projection.py", "test_ipg3_validators.py", "test_ipg3_reference_state.py"):
        completed = subprocess.run([sys.executable, name], cwd=ROOT, capture_output=True, text=True)
        if completed.returncode != 0:
            failures.append(f"{name} failed:\n{completed.stdout}\n{completed.stderr}")
    return failures


def main() -> int:
    failures = []
    failures.extend(validate_json_schemas())
    failures.extend(validate_isolation())
    failures.extend(run_unittests())
    if failures:
        print("IPG3 DESIGN VALIDATION: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("IPG3 DESIGN VALIDATION: PASS")
    print(f"Validated {len(list(ROOT.glob('*.draft.schema.json')))} draft schemas plus shadow, relational, and atomic-state tests.")
    print("Confirmed design/ remains outside authoritative deployment dependency closure.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
