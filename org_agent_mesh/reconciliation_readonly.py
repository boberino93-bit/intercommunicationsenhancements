from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

@dataclass(frozen=True)
class Finding:
    code: str
    project_id: str
    detail: str
    severity: str


def reconcile_project(*, project_id: str, expected_repo: str, observed_repo: str | None, expected_forum: str, observed_forum: str | None, bootstrap_version: str | None, expected_bootstrap_version: str, artifactory_manifest_digest: str | None, github_manifest_digest: str | None) -> tuple[Finding, ...]:
    findings: list[Finding] = []
    if observed_repo != expected_repo:
        findings.append(Finding("REPOSITORY_MAPPING_DRIFT", project_id, f"expected={expected_repo};observed={observed_repo}", "HIGH"))
    if observed_forum != expected_forum:
        findings.append(Finding("FORUM_MAPPING_DRIFT", project_id, f"expected={expected_forum};observed={observed_forum}", "HIGH"))
    if bootstrap_version != expected_bootstrap_version:
        findings.append(Finding("BOOTSTRAP_VERSION_DRIFT", project_id, f"expected={expected_bootstrap_version};observed={bootstrap_version}", "MEDIUM"))
    if artifactory_manifest_digest is not None and github_manifest_digest is not None and artifactory_manifest_digest != github_manifest_digest:
        findings.append(Finding("STATE_DIVERGENCE_DETECTED", project_id, "latest sealed manifest digests differ", "CRITICAL"))
    return tuple(findings)


def reconcile_registry(*, expected: Mapping[str, tuple[str, str]], observed: Mapping[str, tuple[str | None, str | None]], expected_bootstrap_version: str, bootstrap_versions: Mapping[str, str | None]) -> tuple[Finding, ...]:
    findings: list[Finding] = []
    for project_id, (repo, forum) in expected.items():
        o_repo, o_forum = observed.get(project_id, (None, None))
        findings.extend(reconcile_project(project_id=project_id, expected_repo=repo, observed_repo=o_repo, expected_forum=forum, observed_forum=o_forum, bootstrap_version=bootstrap_versions.get(project_id), expected_bootstrap_version=expected_bootstrap_version, artifactory_manifest_digest=None, github_manifest_digest=None))
    for project_id in sorted(set(observed) - set(expected)):
        findings.append(Finding("UNREGISTERED_PROJECT_STATE", project_id, "observed project is absent from authoritative registry", "HIGH"))
    return tuple(findings)
