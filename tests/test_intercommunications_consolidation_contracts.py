import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(p): return json.loads((ROOT/p).read_text())
class ConsolidationContractTests(unittest.TestCase):
    def test_registry_preserves_mature_top_level_controls(self):
        r=load('PROJECT_ROLE_ROUTING_REGISTRY.json')
        for key in ('resolution_key','user_control_messages','communication_awareness','supervisory_governance','scheduled_task_activation','global_intake','autonomous_continuation','fresh_agent_context','rules'): self.assertIn(key,r)
        self.assertEqual(r['rules']['cross_project_write_default'],'DENY'); self.assertEqual(r['communication_awareness']['default_visibility_claim'],'PARTIAL_UNLESS_PROVEN')
    def test_registry_preserves_warp_overlay_and_project_metadata(self):
        r=load('PROJECT_ROLE_ROUTING_REGISTRY.json'); w=r['projects']['warp-propulsion-lab']; self.assertEqual(w['routing_contract_version'],'1.3.0'); self.assertTrue(w['continuation_overlay_authority']); self.assertIn('agentbus-backup/intercomm-optimization-v1/ACTIVE_INTERCOMM_PROFILE.json',w['handoff_paths'])
    def test_xrp_route_is_internal_and_matches_live_registry(self):
        r=load('PROJECT_ROLE_ROUTING_REGISTRY.json')['projects']['xrp-thesis']; l=load('LIVE_OPERATIONS_REGISTRY.json')['projects']; x=next(v for v in l if v['project_id']=='xrp-thesis'); self.assertEqual(r['forum_namespace'],'/XRPTHESIS-AgentBus/messages'); self.assertEqual(r['forum_locator']['authority'],'INTERNAL_ARTIFACTORY'); self.assertEqual(x['message_board'],r['forum_namespace'])
    def test_master_handoff_preserves_history(self):
        h=load('MASTER_HANDOFF.json'); ids={x['agent_id'] for x in h['expired_agents']}; self.assertTrue({'primary-remediation','primary-scale100','primary-scale100-continuity','primary-stage15-preflight'}.issubset(ids)); self.assertTrue(any(w['id']=='stage15-preflight' for w in h['workstreams'])); self.assertTrue(any(w['id']=='dual-persistence-hardening' for w in h['workstreams']))
    def test_no_registered_project_single_sink_checkpoint_exception(self):
        t=(ROOT/'protocols/swarm_checkpoint_bus.md').read_text(); self.assertIn('There is no registered-project single-sink exception',t); self.assertNotIn('verified GitHub backup persistence is sufficient',t); self.assertIn('DUAL_PERSISTENCE_CONFIRMED',t)
    def test_hybrid_and_scaler_are_non_activating(self):
        h=load('governance/HYBRID_ADMISSION_SHADOW_POLICY.json'); s=load('governance/SYSTEM_SCALER_POLICY.json'); q=load('research_swarm/hybrid_capacity_schedule.json'); self.assertEqual(h['status'],'STAGED_DISABLED'); self.assertFalse(h['production_activation']); self.assertFalse(q['enabled']); self.assertFalse(q['primary_schedulable']); self.assertEqual(s['status'],'STAGED_NOT_ACTIVE'); self.assertFalse(s['authority_conveyed']); self.assertEqual(s['scale_up']['requires_dual_persistence_health'],'DUAL_PERSISTENCE_CONFIRMED')
    def test_old_hybrid_auth_artifacts_are_not_promoted(self):
        for p in ('governance/HYBRID_ADMISSION_CROSS_PROJECT_INTENT_20261005.json','governance/HYBRID_ADMISSION_PACKAGE_MANIFEST_20261005.json','governance/HYBRID_ADMISSION_SECURITY_RECEIPTS_20261005.json'): self.assertFalse((ROOT/p).exists())
    def test_stage15_schema_can_represent_blocked_persistence(self):
        p=load('schemas/stage15_evidence.schema.json')['properties']['projects']['items']['properties']['persistence']; self.assertIn('oneOf',p); self.assertEqual(p['oneOf'][1]['properties']['persistence_admission']['const'],False)
    def test_manifest_is_candidate_only(self):
        m=load('governance/INTERCOMMUNICATIONS_CONSOLIDATION_MANIFEST_20261006.json'); self.assertEqual(m['status'],'CANDIDATE_NON_ACTIVATING'); self.assertFalse(m['safety']['main_merge_authorized']); self.assertFalse(m['cleanup']['agentbus_mutated'])
if __name__=='__main__': unittest.main()
