import unittest

from org_agent_mesh.dual_persistence import build_persistence_health
from org_agent_mesh.stage15_preflight import (
    EXPECTED_PROJECTS,
    Stage15PreflightError,
    Stage15ProjectEvidence,
    assemble_stage15_evidence,
    canonical_project_id,
    normalize_operations_observation,
    validate_capacity_signal,
    validate_persistence_health,
)

NOW = "2026-10-05T23:45:00Z"


def capacity(project_id, repo, *, state="GREEN", measured="2026-10-05T23:44:30Z"):
    return {
        "schema": "org-agent-mesh/capacity-signal/v1",
        "project_id": project_id,
        "repository_identity": repo,
        "observed_revision": "abc123",
        "measured_at_utc": measured,
        "overall_state": state,
        "resources": [],
        "high_level_needs": [],
        "pending_writes": {},
    }


def operations(project_id, *, observed="2026-10-05T23:44:30Z", normalized=True):
    return {"project_id": project_id, "observed_at_utc": observed, "normalized": normalized, "status": "READY"}


def healthy_persistence(project_id, *, reconciled="2026-10-05T23:44:30Z", normalized=True):
    digest = "sha256:" + "a" * 64
    return build_persistence_health(
        project_id=project_id,
        reconciled_at_utc=reconciled,
        artifactory_records={"r1": digest},
        github_records={"r1": digest},
        route_normalized=normalized,
        forum_verified=True,
        github_backup_verified=True,
    )


class Stage15PreflightTests(unittest.TestCase):
    def test_canonical_xrp_alias(self):
        self.assertEqual(canonical_project_id("xrpthesis"), "xrp-thesis")
        self.assertEqual(canonical_project_id("xrp-thesis"), "xrp-thesis")

    def test_fresh_green_capacity_admits(self):
        result = validate_capacity_signal(capacity("benefitflow", "boberino93-bit/benefitflow"), expected_project_id="benefitflow", expected_repository_identity="boberino93-bit/benefitflow", now_utc=NOW)
        self.assertTrue(result["capacity_admission"])

    def test_unknown_capacity_blocks(self):
        with self.assertRaisesRegex(Stage15PreflightError, "CAPACITY_NOT_ADMISSIBLE:UNKNOWN"):
            validate_capacity_signal(capacity("benefitflow", "boberino93-bit/benefitflow", state="UNKNOWN"), expected_project_id="benefitflow", expected_repository_identity="boberino93-bit/benefitflow", now_utc=NOW)

    def test_stale_capacity_blocks(self):
        with self.assertRaisesRegex(Stage15PreflightError, "CAPACITY_SIGNAL_STALE"):
            validate_capacity_signal(capacity("benefitflow", "boberino93-bit/benefitflow", measured="2026-10-05T23:00:00Z"), expected_project_id="benefitflow", expected_repository_identity="boberino93-bit/benefitflow", now_utc=NOW)

    def test_future_capacity_blocks(self):
        with self.assertRaisesRegex(Stage15PreflightError, "CAPACITY_SIGNAL_FROM_FUTURE"):
            validate_capacity_signal(capacity("benefitflow", "boberino93-bit/benefitflow", measured="2026-10-05T23:46:00Z"), expected_project_id="benefitflow", expected_repository_identity="boberino93-bit/benefitflow", now_utc=NOW)

    def test_wrong_capacity_project_blocks(self):
        with self.assertRaisesRegex(Stage15PreflightError, "CAPACITY_PROJECT_MISMATCH"):
            validate_capacity_signal(capacity("duo-open", "boberino93-bit/benefitflow"), expected_project_id="benefitflow", expected_repository_identity="boberino93-bit/benefitflow", now_utc=NOW)

    def test_wrong_capacity_repository_blocks(self):
        with self.assertRaisesRegex(Stage15PreflightError, "CAPACITY_REPOSITORY_MISMATCH"):
            validate_capacity_signal(capacity("benefitflow", "boberino93-bit/not-benefitflow"), expected_project_id="benefitflow", expected_repository_identity="boberino93-bit/benefitflow", now_utc=NOW)

    def test_xrp_legacy_operations_alias_is_visible_not_normalized(self):
        result = normalize_operations_observation(operations("xrpthesis", normalized=False), expected_project_id="xrp-thesis", now_utc=NOW)
        self.assertEqual(result["project_id"], "xrp-thesis")
        self.assertTrue(result["legacy_alias_used"])
        self.assertFalse(result["mesh_normalization_complete"])

    def test_stale_operations_blocks(self):
        with self.assertRaisesRegex(Stage15PreflightError, "OPERATIONS_OBSERVATION_STALE"):
            normalize_operations_observation(operations("benefitflow", observed="2026-10-05T22:00:00Z"), expected_project_id="benefitflow", now_utc=NOW)

    def test_future_operations_blocks(self):
        with self.assertRaisesRegex(Stage15PreflightError, "OPERATIONS_OBSERVATION_FROM_FUTURE"):
            normalize_operations_observation(operations("benefitflow", observed="2026-10-05T23:46:00Z"), expected_project_id="benefitflow", now_utc=NOW)

    def test_healthy_persistence_admits(self):
        result = validate_persistence_health(healthy_persistence("duo-open"), expected_project_id="duo-open", now_utc=NOW)
        self.assertTrue(result["persistence_admission"])

    def test_stale_persistence_blocks(self):
        with self.assertRaisesRegex(Stage15PreflightError, "PERSISTENCE_HEALTH_STALE"):
            validate_persistence_health(healthy_persistence("duo-open", reconciled="2026-10-05T22:00:00Z"), expected_project_id="duo-open", now_utc=NOW)

    def _evidence(self, *, legacy_xrp=False, degraded_project=None):
        repo_map = {
            "ai-behaviour-control-lab": "boberino93-bit/ai-behaviour-control-lab",
            "benefitflow": "boberino93-bit/benefitflow",
            "duo-open": "boberino93-bit/duo-open",
            "fold7-power-lab": "boberino93-bit/samsungpowerbootstrap",
            "intercommunicationsenhancements": "boberino93-bit/intercommunicationsenhancements",
            "warp-propulsion-lab": "boberino93-bit/warp-propulsion-lab",
            "xrp-thesis": "boberino93-bit/XRPTHESIS",
        }
        items = []
        for project_id in EXPECTED_PROJECTS:
            raw_ops = "xrpthesis" if legacy_xrp and project_id == "xrp-thesis" else project_id
            persistence = healthy_persistence(project_id)
            if project_id == degraded_project:
                persistence = dict(persistence)
                persistence["single_sink_count"] = 1
                persistence["zero_loss"] = False
            items.append(Stage15ProjectEvidence(
                project_id=project_id,
                repository_identity=repo_map[project_id],
                source_revision="rev-" + project_id,
                capacity=capacity(project_id, repo_map[project_id]),
                operations=operations(raw_ops, normalized=not (legacy_xrp and project_id == "xrp-thesis")),
                kernel_preflight_pass=True,
                persistence=persistence,
            ))
        return items

    def test_exact_project_set_required(self):
        with self.assertRaisesRegex(Stage15PreflightError, "PROJECT_EVIDENCE_SET_MISMATCH"):
            assemble_stage15_evidence(global_run_id="run-15", now_utc=NOW, project_evidence=self._evidence()[:-1])

    def test_kernel_preflight_failure_blocks_readiness_not_authority(self):
        items = self._evidence(); first = items[0]
        items[0] = Stage15ProjectEvidence(first.project_id, first.repository_identity, first.source_revision, first.capacity, first.operations, False, first.persistence)
        envelope = assemble_stage15_evidence(global_run_id="run-15", now_utc=NOW, project_evidence=items)
        self.assertFalse(envelope.preflight_ready); self.assertFalse(envelope.stage_passed); self.assertFalse(envelope.authority_conveyed); self.assertFalse(envelope.launch_authorized)

    def test_clean_evidence_is_preflight_ready_but_not_stage_passed_or_authorized(self):
        envelope = assemble_stage15_evidence(global_run_id="run-15", now_utc=NOW, project_evidence=self._evidence())
        self.assertTrue(envelope.contract_ready); self.assertTrue(envelope.preflight_ready)
        self.assertFalse(envelope.stage_passed); self.assertFalse(envelope.authority_conveyed); self.assertFalse(envelope.launch_authorized)

    def test_legacy_xrp_route_blocks_preflight(self):
        envelope = assemble_stage15_evidence(global_run_id="run-15", now_utc=NOW, project_evidence=self._evidence(legacy_xrp=True))
        self.assertFalse(envelope.preflight_ready)
        self.assertIn("xrp-thesis:MESH_NORMALIZATION_INCOMPLETE", envelope.blockers)

    def test_degraded_persistence_blocks_preflight(self):
        envelope = assemble_stage15_evidence(global_run_id="run-15", now_utc=NOW, project_evidence=self._evidence(degraded_project="duo-open"))
        self.assertFalse(envelope.preflight_ready)
        self.assertTrue(any(b.startswith("duo-open:PERSISTENCE_") for b in envelope.blockers))

    def test_missing_persistence_blocks_preflight(self):
        items = self._evidence(); first=items[0]
        items[0] = Stage15ProjectEvidence(first.project_id, first.repository_identity, first.source_revision, first.capacity, first.operations, True, {})
        envelope = assemble_stage15_evidence(global_run_id="run-15", now_utc=NOW, project_evidence=items)
        self.assertFalse(envelope.preflight_ready)
        self.assertTrue(any("PERSISTENCE_HEALTH_MISSING" in b for b in envelope.blockers))

    def test_evidence_digest_is_deterministic(self):
        a=assemble_stage15_evidence(global_run_id="run-15",now_utc=NOW,project_evidence=self._evidence())
        b=assemble_stage15_evidence(global_run_id="run-15",now_utc=NOW,project_evidence=list(reversed(self._evidence())))
        self.assertEqual(a.evidence_digest,b.evidence_digest)

    def test_evidence_digest_changes_with_persistence_telemetry(self):
        a=assemble_stage15_evidence(global_run_id="run-15",now_utc=NOW,project_evidence=self._evidence())
        items=self._evidence(); target=items[1]; changed=dict(target.persistence); changed["record_count"]=2; changed["confirmed_count"]=2
        items[1]=Stage15ProjectEvidence(target.project_id,target.repository_identity,target.source_revision,target.capacity,target.operations,True,changed)
        b=assemble_stage15_evidence(global_run_id="run-15",now_utc=NOW,project_evidence=items)
        self.assertNotEqual(a.evidence_digest,b.evidence_digest)


if __name__ == "__main__":
    unittest.main()
