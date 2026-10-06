import json
from pathlib import Path
import unittest

from org_agent_mesh.dual_persistence import MaterialWorkRecord, SinkAck, DualPersistenceReceipt, SINK_ARTIFACTORY, SINK_GITHUB, build_persistence_health

ROOT=Path(__file__).resolve().parents[1]
NOW="2026-10-06T04:20:00+00:00"
NAMES=("material_work_record.schema.json","dual_persistence_receipt.schema.json","persistence_health.schema.json","stage15_evidence.schema.json")

def schema(name): return json.loads((ROOT/'schemas'/name).read_text())
def require_shape(doc):
    assert doc.get('$schema')=='https://json-schema.org/draft/2020-12/schema'
    assert doc.get('type')=='object'
    assert isinstance(doc.get('required'),list) and doc['required']
    assert isinstance(doc.get('properties'),dict)

def exact_required(instance, doc):
    missing=set(doc['required'])-set(instance)
    if missing: raise AssertionError(f'missing required fields: {sorted(missing)}')
    if doc.get('additionalProperties') is False:
        extra=set(instance)-set(doc['properties'])
        if extra: raise AssertionError(f'unexpected fields: {sorted(extra)}')

class PersistenceSchemaTests(unittest.TestCase):
    def test_schema_contracts_use_declared_draft_without_external_dependency(self):
        for name in NAMES: require_shape(schema(name))
    def test_runtime_work_record_shape(self):
        r=MaterialWorkRecord('r1','duo-open','run','a','RESEARCH','w','FINDING',0,NOW,'x',{}).as_dict()
        exact_required(r,schema('material_work_record.schema.json'))
    def test_runtime_confirmed_receipt_shape(self):
        d='sha256:'+'0'*64
        a=SinkAck(sink=SINK_ARTIFACTORY,project_id='duo-open',record_id='r1',content_digest=d,location='/forum/r1',acknowledged_at=NOW)
        g=SinkAck(sink=SINK_GITHUB,project_id='duo-open',record_id='r1',content_digest=d,location='agentbus-backup/coordination-messages/r1.json',acknowledged_at=NOW)
        p=DualPersistenceReceipt(receipt_id='receipt-r1',project_id='duo-open',record_id='r1',content_digest=d,prepared_at=NOW,artifactory_ack=a,github_ack=g).as_dict()
        exact_required(p,schema('dual_persistence_receipt.schema.json'))
    def test_runtime_health_shape(self):
        h=build_persistence_health(project_id='duo-open',reconciled_at_utc=NOW,artifactory_records={},github_records={},route_normalized=True,forum_verified=True,github_backup_verified=True)
        exact_required(h,schema('persistence_health.schema.json'))
    def test_stage15_nested_contracts_are_not_unconstrained_objects(self):
        s=schema('stage15_evidence.schema.json')
        p=s['properties']['projects']['items']['properties']
        self.assertIn('capacity',p); self.assertIn('operations',p); self.assertIn('persistence',p)
        self.assertIn('capacity_admission',p['capacity']['required'])
        self.assertIn('mesh_normalization_complete',p['operations']['required'])
        persistence=p['persistence']
        self.assertEqual(len(persistence['oneOf']),2)
        healthy,blocked=persistence['oneOf']
        self.assertIn('zero_loss',healthy['required'])
        self.assertIn('persistence_admission',healthy['required'])
        self.assertIn('error',blocked['required'])
        self.assertIn('persistence_admission',blocked['required'])

if __name__=='__main__': unittest.main()
