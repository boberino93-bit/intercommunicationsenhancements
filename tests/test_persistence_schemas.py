import json
from pathlib import Path
import unittest
import jsonschema

from org_agent_mesh.dual_persistence import MaterialWorkRecord, SinkAck, DualPersistenceReceipt, SINK_ARTIFACTORY, SINK_GITHUB, build_persistence_health

ROOT=Path(__file__).resolve().parents[1]
NOW="2026-10-06T04:20:00+00:00"

def schema(name): return json.loads((ROOT/'schemas'/name).read_text())

class PersistenceSchemaTests(unittest.TestCase):
    def test_schemas_are_valid_draft_2020_12(self):
        for name in ['material_work_record.schema.json','dual_persistence_receipt.schema.json','persistence_health.schema.json','stage15_evidence.schema.json']:
            jsonschema.Draft202012Validator.check_schema(schema(name))

    def test_runtime_work_record_validates(self):
        r=MaterialWorkRecord('r1','duo-open','run','a','RESEARCH','w','FINDING',0,NOW,'x',{})
        jsonschema.validate(r.as_dict(),schema('material_work_record.schema.json'))

    def test_runtime_confirmed_receipt_validates(self):
        r=MaterialWorkRecord('r1','duo-open','run','a','RESEARCH','w','FINDING',0,NOW,'x',{})
        a=SinkAck(SINK_ARTIFACTORY,r.project_id,r.record_id,r.content_digest,'/forum/r1',NOW)
        g=SinkAck(SINK_GITHUB,r.project_id,r.record_id,r.content_digest,'agentbus-backup/coordination-messages/r1.json',NOW)
        p=DualPersistenceReceipt('p',r.project_id,r.record_id,r.content_digest,NOW,a,g)
        jsonschema.validate(p.as_dict(),schema('dual_persistence_receipt.schema.json'))

    def test_runtime_health_validates(self):
        d='sha256:'+'a'*64
        h=build_persistence_health(project_id='duo-open',reconciled_at_utc=NOW,artifactory_records={'r':d},github_records={'r':d},route_normalized=True,forum_verified=True,github_backup_verified=True)
        jsonschema.validate(h,schema('persistence_health.schema.json'))

if __name__=='__main__': unittest.main()
