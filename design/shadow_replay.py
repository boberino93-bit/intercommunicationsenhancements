"""Offline replay for sanitized Message v2 fixtures into the IPG3 shadow projector."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from shadow_projection import assert_semantic_projection, project_v2_to_v3


ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"


def replay_fixture_directory(path: Path = FIXTURES) -> dict:
    total = 0
    projected = 0
    failures = []
    classes = Counter()
    missing = Counter()
    fingerprints = set()

    for fixture in sorted(path.glob("v2_*.json")):
        total += 1
        try:
            source = json.loads(fixture.read_text(encoding="utf-8"))
            shadow = project_v2_to_v3(source)
            assert_semantic_projection(source, shadow)
            fingerprint = shadow["integrity"]["canonical_envelope_sha256"]
            if fingerprint in fingerprints:
                raise ValueError("duplicate shadow fingerprint across distinct fixtures")
            fingerprints.add(fingerprint)
            projected += 1
            classes[shadow["class"]] += 1
            if shadow["sender"]["principal_id"] is None:
                missing["principal_id"] += 1
            if shadow["task"]["delegation_contract_id"] is None:
                missing["delegation_contract_id"] += 1
            if shadow["task"]["approval_id"] is None:
                missing["approval_id"] += 1
            if shadow["causality"]["project_event_sequence"] is None:
                missing["project_event_sequence"] += 1
            if shadow["integrity"]["signature"] is None:
                missing["signature"] += 1
        except Exception as exc:
            failures.append({"fixture": fixture.name, "error": str(exc)})

    return {
        "total": total,
        "projected": projected,
        "failed": len(failures),
        "success_rate": 0.0 if total == 0 else projected / total,
        "classes": dict(sorted(classes.items())),
        "missing_g3_fields": dict(sorted(missing.items())),
        "failures": failures,
    }


def main() -> int:
    report = replay_fixture_directory()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["failed"] == 0 and report["total"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
