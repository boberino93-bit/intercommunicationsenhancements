import unittest
from org_agent_mesh.dual_persistence import build_persistence_health
from org_agent_mesh.stage15_preflight import EXPECTED_PROJECTS,Stage15PreflightError,Stage15ProjectEvidence,assemble_stage15_evidence,canonical_project_id,normalize_operations_observation,validate_capacity_signal,validate_persistence_health
NOW="2026-10-05T23:45:00Z"
def capacity(project_id,repo,*,state="GREEN",measured="2026-10-05T23:44:30Z"):
    return {"schema":"org-agent-mesh/capacity-signal/v1","project_id":project_id,"repository_identity":repo,"observed_revision":"abc123","measured_at_utc":measured,"overall_state":state,"resources":[],"high_level_needs":[],"pending_writes":{}}
def operations(project_id,*,observed="2026-10-05T23:44:30Z",normalized=True): return {"project_id":project_id,"observed_at_utc":observed,"normalized":normalized,"status":"READY"}
def healthy_persistence(project_id,*,reconciled="2026-10-05T23:44:30Z",normalized=True):
    d="sha256:"+"a"*64; return build_persistence_health(project_id=project_id,reconciled_at_utc=reconciled,artifactory_records={"r1":d},github_records={"r1":d},route_normalized=normalized,forum_verified=True,github_backup_verified=True)
class Stage15PreflightTests(unittest.TestCase):
    def test_canonical_xrp_alias(self): self.assertEqual(canonical_project_id("xrpthesis"),"xrp-thesis"); self.assertEqual(canonical_project_id("xrp-thesis"),"xrp-thesis")
    def test_fresh_green_capacity_admits(self): self.assertTrue(validate_capacity_signal(capacity("benefitflow","boberino93-bit/benefitflow"),expected_project_id="benefitflow",expected_repository_identity="boberino93-bit/benefitflow",now_utc=NOW)["capacity_admission"])
    def test_unknown_capacity_blocks(self):
        with self.assertRaisesRegex(Stage15PreflightError,"CAPACITY_NOT_ADMISSIBLE:UNKNOWN"): validate_capacity_signal(capacity("benefitflow","boberino93-bit/benefitflow",state="UNKNOWN"),expected_project_id="benefitflow",expected_repository_identity="boberino93-bit/benefitflow",now_utc=NOW)
    def test_stale_capacity_blocks(self):
        with self.assertRaisesRegex(Stage15PreflightError,"CAPACITY_SIGNAL_STALE"): validate_capacity_signal(capacity("benefitflow","boberino93-bit/benefitflow",measured="2026-10-05T23:00:00Z"),expected_project_id="benefitflow",expected_repository_identity="boberino93-bit/benefitflow",now_utc=NOW)
    def test_future_capacity_blocks(self):
        with self.assertRaisesRegex(Stage15PreflightError,"CAPACITY_SIGNAL_FROM_FUTURE"): validate_capacity_signal(capacity("benefitflow","boberino93-bit/benefitflow",measured="2026-10-05T23:46:00Z"),expected_project_id="benefitflow",expected_repository_identity="boberino93-bit/benefitflow",now_utc=NOW)
    def test_wrong_capacity_project_blocks(self):
        with self.assertRaisesRegex(Stage15PreflightError,"CAPACITY_PROJECT_MISMATCH"): validate_capacity_signal(capacity("duo-open","boberino93-bit/benefitflow"),expected_project_id="benefitflow",expected_repository_identity="boberino93-bit/benefitflow",now_utc=NOW)
    def test_wrong_capacity_repository_blocks(self):
        with self.assertRaisesRegex(Stage15PreflightError,"CAPACITY_REPOSITORY_MISMATCH"): validate_capacity_signal(capacity("benefitflow","boberino93-bit/not-benefitflow"),expected_project_id="benefitflow",expected_repository_identity="boberino93-bit/benefitflow",now_utc=NOW)
    def test_xrp_legacy_operations_alias_is_visible_not_normalized(self):
        r=normalize_operations_observation(operations("xrpthesis",normalized=False),expected_project_id="xrp-thesis",now_utc=NOW); self.assertEqual(r["project_id"],"xrp-thesis"); self.assertEqual(r["observed_project_id"],"xrpthesis"); self.assertTrue(r["legacy_alias_used"]); self.assertFalse(r["mesh_normalization_complete"])
    def test_stale_operations_blocks(self):
        with self.assertRaisesRegex(Stage15PreflightError,"OPERATIONS_OBSERVATION_STALE"): normalize_operations_observation(operations("benefitflow",observed="2026-10-05T22:00:00Z"),expected_project_id="benefitflow",now_utc=NOW)
    def test_future_operations_blocks(self):
        with self.assertRaisesRegex(Stage15PreflightError,"OPERATIONS_OBSERVATION_FROM_FUTURE"): normalize_operations_observation(operations("benefitflow",observed="2026-10-05T23:46:00Z"),expected_project_id="benefitflow",now_utc=NOW)
    def test_healthy_persistence_admits(self): self.assertTrue(validate_persistence_health(healthy_persistence("duo-open"),expected_project_id="duo-open",now_utc=NOW)["persistence_admission"])
    def test_stale_persistence_blocks(self):
        with self.assertRaisesRegex(Stage15PreflightError,"PERSISTENCE_HEALTH_STALE"): validate_persistence_health(healthy_persistence("duo-open",reconciled="2026-10-05T22:00:00Z"),expected_project_id="duo-open",now_utc=NOW)
    def _evidence(self,*,legacy_xrp=False,degraded_project=None):
        repos={"ai-behaviour-control-lab":"boberino93-bit/ai-behaviour-control-lab","benefitflow":"boberino93-bit/benefitflow","duo-open":"boberino93-bit/duo-open","fold7-power-lab":"boberino93-bit/samsungpowerbootstrap","intercommunicationsenhancements":"boberino93-bit/intercommunicationsenhancements","warp-propulsion-lab":"boberino93-bit/warp-propulsion-lab","xrp-thesis":"boberino93-bit/XRPTHESIS"}; out=[]
        for p in EXPECTED_PROJECTS:
            raw="xrpthesis" if legacy_xrp and p=="xrp-thesis" else p; ph=healthy_persistence(p)
            if p==degraded_project: ph=dict(ph); ph["single_sink_count"]=1; ph["zero_loss"]=False
            out.append(Stage15ProjectEvidence(p,repos[p],"rev-"+p,capacity(p,repos[p]),operations(raw,normalized=not(legacy_xrp and p=="xrp-thesis")),True,ph))
        return out
    def test_exact_project_set_required(self):
        with self.assertRaisesRegex(Stage15PreflightError,"PROJECT_EVIDENCE_SET_MISMATCH"): assemble_stage15_evidence(global_run_id="run-15",now_utc=NOW,project_evidence=self._evidence()[:-1])
    def test_kernel_preflight_failure_blocks_readiness_not_authority(self):
        i=self._evidence(); f=i[0]; i[0]=Stage15ProjectEvidence(f.project_id,f.repository_identity,f.source_revision,f.capacity,f.operations,False,f.persistence); e=assemble_stage15_evidence(global_run_id="run-15",now_utc=NOW,project_evidence=i); self.assertFalse(e.preflight_ready); self.assertFalse(e.stage_passed); self.assertFalse(e.authority_conveyed); self.assertFalse(e.launch_authorized)
    def test_clean_evidence_is_preflight_ready_but_not_stage_passed_or_authorized(self):
        e=assemble_stage15_evidence(global_run_id="run-15",now_utc=NOW,project_evidence=self._evidence()); self.assertTrue(e.contract_ready); self.assertTrue(e.preflight_ready); self.assertFalse(e.stage_passed); self.assertFalse(e.authority_conveyed); self.assertFalse(e.launch_authorized)
    def test_legacy_xrp_route_blocks_preflight(self):
        e=assemble_stage15_evidence(global_run_id="run-15",now_utc=NOW,project_evidence=self._evidence(legacy_xrp=True)); self.assertFalse(e.preflight_ready); self.assertIn("xrp-thesis:MESH_NORMALIZATION_INCOMPLETE",e.blockers); x=next(p for p in e.projects if p["project_id"]=="xrp-thesis"); self.assertEqual(x["operations"]["observed_project_id"],"xrpthesis")
    def test_degraded_persistence_blocks_preflight(self):
        e=assemble_stage15_evidence(global_run_id="run-15",now_utc=NOW,project_evidence=self._evidence(degraded_project="duo-open")); self.assertFalse(e.preflight_ready); self.assertTrue(any(b.startswith("duo-open:PERSISTENCE_") for b in e.blockers))
    def test_missing_persistence_blocks_preflight(self):
        i=self._evidence(); f=i[0]; i[0]=Stage15ProjectEvidence(f.project_id,f.repository_identity,f.source_revision,f.capacity,f.operations,True,{}); e=assemble_stage15_evidence(global_run_id="run-15",now_utc=NOW,project_evidence=i); self.assertFalse(e.preflight_ready); self.assertTrue(any("PERSISTENCE_HEALTH_MISSING" in b for b in e.blockers))
    def test_evidence_digest_is_deterministic(self): self.assertEqual(assemble_stage15_evidence(global_run_id="run-15",now_utc=NOW,project_evidence=self._evidence()).evidence_digest,assemble_stage15_evidence(global_run_id="run-15",now_utc=NOW,project_evidence=list(reversed(self._evidence()))).evidence_digest)
    def test_evidence_digest_changes_with_capacity_telemetry(self):
        a=assemble_stage15_evidence(global_run_id="run-15",now_utc=NOW,project_evidence=self._evidence()); i=self._evidence(); t=i[1]; c=dict(t.capacity); c["observed_revision"]="changed"; i[1]=Stage15ProjectEvidence(t.project_id,t.repository_identity,t.source_revision,c,t.operations,True,t.persistence); b=assemble_stage15_evidence(global_run_id="run-15",now_utc=NOW,project_evidence=i); self.assertNotEqual(a.evidence_digest,b.evidence_digest)
    def test_evidence_digest_changes_with_persistence_telemetry(self):
        a=assemble_stage15_evidence(global_run_id="run-15",now_utc=NOW,project_evidence=self._evidence()); i=self._evidence(); t=i[1]; p=dict(t.persistence); p["record_count"]=2; p["confirmed_count"]=2; i[1]=Stage15ProjectEvidence(t.project_id,t.repository_identity,t.source_revision,t.capacity,t.operations,True,p); b=assemble_stage15_evidence(global_run_id="run-15",now_utc=NOW,project_evidence=i); self.assertNotEqual(a.evidence_digest,b.evidence_digest)
if __name__=="__main__": unittest.main()
