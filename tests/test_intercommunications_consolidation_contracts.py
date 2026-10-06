import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p): return json.loads((ROOT/p).read_text())
class ConsolidationContractTests(unittest.TestCase):
    def test_xrp_route_is_internal_and_matches_live_registry(self):
        r=load('PROJECT_ROLE_ROUTING_REGISTRY.json')['projects']['xrp-thesis']; l=load('LIVE_OPERATIONS_REGISTRY.json')['projects']; x=next(v for v in l if v['project_id']=='xrp-thesis')
        self.assertEqual(r['forum_namespace'],'/XRPTHESIS-AgentBus/messages'); self.assertEqual(r['forum_locator']['authority'],'INTERNAL_ARTIFACTORY'); self.assertEqual(x['message_board'],r['forum_namespace'])
    def test_no_registered_project_single_sink_checkpoint_exception(self):
        text=(ROOT/'protocols/swarm_checkpoint_bus.md').read_text(); self.assertIn('There is no GitHub-only registered-project exception',text); self.assertNotIn('verified GitHub backup persistence is sufficient',text)
    def test_hybrid_and_scaler_are_non_activating(self):
        h=load('governance/HYBRID_ADMISSION_SHADOW_POLICY.json'); s=load('governance/SYSTEM_SCALER_POLICY.json'); q=load('research_swarm/hybrid_capacity_schedule.json')
        self.assertEqual(h['status'],'STAGED_DISABLED'); self.assertFalse(h['production_activation']); self.assertFalse(h['principles']['generic_primary_self_admission']); self.assertTrue(h['principles']['consequence_gateway_is_sole_protected_effect_boundary']); self.assertFalse(q['enabled']); self.assertFalse(q['primary_schedulable']); self.assertEqual(s['status'],'STAGED_NOT_ACTIVE'); self.assertFalse(s['authority_conveyed']); self.assertEqual(s['scale_up']['requires_dual_persistence_health'],'DUAL_PERSISTENCE_CONFIRMED')
    def test_old_hybrid_auth_artifacts_are_not_promoted(self):
        for p in ('governance/HYBRID_ADMISSION_CROSS_PROJECT_INTENT_20261005.json','governance/HYBRID_ADMISSION_PACKAGE_MANIFEST_20261005.json','governance/HYBRID_ADMISSION_SECURITY_RECEIPTS_20261005.json'): self.assertFalse((ROOT/p).exists())
    def test_stage15_requires_zero_loss_persistence(self):
        p=load('schemas/stage15_evidence.schema.json')['properties']['projects']['items']['properties']['persistence']; self.assertEqual(p['properties']['zero_loss']['const'],True); self.assertEqual(p['properties']['single_sink_count']['const'],0); self.assertEqual(p['properties']['digest_mismatch_count']['const'],0)
    def test_manifest_is_candidate_only(self):
        m=load('governance/INTERCOMMUNICATIONS_CONSOLIDATION_MANIFEST_20261006.json'); self.assertEqual(m['status'],'CANDIDATE_NON_ACTIVATING'); self.assertFalse(m['safety']['main_merge_authorized']); self.assertFalse(m['cleanup']['agentbus_mutated'])
if __name__=='__main__': unittest.main()
