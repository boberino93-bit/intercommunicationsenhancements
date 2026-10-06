import unittest
from org_agent_mesh.dual_persistence import *
NOW="2026-10-06T04:20:00+00:00"
def record(**kw):
 d=dict(record_id="r1",project_id="duo-open",run_id="run1",agent_id="a1",role="RESEARCH",work_id="w1",event_type="FINDING",sequence=0,created_at=NOW,summary="x",payload={"x":1}); d.update(kw); return MaterialWorkRecord(**d)
def ack(sink,digest,record_id="r1"): return SinkAck(sink,record_id,digest,"loc",NOW)
class DualPersistenceTests(unittest.TestCase):
 def test_stable_digest(self): self.assertEqual(record().content_digest,record().content_digest)
 def test_secret_guard(self):
  with self.assertRaises(Exception): record(payload={"ephemeral_value":"secret"})
 def test_both_confirm(self):
  r=record(); p=DualPersistenceReceipt("p",r.record_id,r.content_digest,r.project_id,NOW,ack(SINK_ARTIFACTORY,r.content_digest),ack(SINK_GITHUB,r.content_digest)); self.assertEqual(p.state,DUAL_PERSISTENCE_CONFIRMED); self.assertTrue(require_work_state_barrier("COMPLETE",p))
 def test_one_sided_blocks_ready(self):
  r=record(); p=DualPersistenceReceipt("p",r.record_id,r.content_digest,r.project_id,NOW,ack(SINK_ARTIFACTORY,r.content_digest),None); self.assertEqual(p.state,ARTIFACTORY_ONLY)
  with self.assertRaises(PersistenceBarrierError): require_work_state_barrier("READY",p)
 def test_mismatch_quarantine(self):
  r=record(); p=DualPersistenceReceipt("p",r.record_id,r.content_digest,r.project_id,NOW,ack(SINK_ARTIFACTORY,"sha256:"+"0"*64),ack(SINK_GITHUB,r.content_digest)); self.assertEqual(p.state,DIGEST_MISMATCH)
 def test_idempotent_retry(self):
  r=record(); i=PersistenceIndex(); a=ack(SINK_ARTIFACTORY,r.content_digest); i.observe(a); i.observe(a); self.assertEqual(i.observe(ack(SINK_GITHUB,r.content_digest)),DUAL_PERSISTENCE_CONFIRMED)
 def test_conflict(self):
  r=record(); i=PersistenceIndex(); i.observe(ack(SINK_ARTIFACTORY,r.content_digest))
  with self.assertRaises(PersistenceConflictError): i.observe(ack(SINK_GITHUB,"sha256:"+"f"*64))
 def test_reconcile(self): self.assertEqual([x.state for x in reconcile_digest_views({"a":"x","b":"y"},{"a":"x","c":"z"})],[DUAL_PERSISTENCE_CONFIRMED,ARTIFACTORY_ONLY,GITHUB_ONLY])
 def test_hash_chain(self):
  a=record(); b=record(record_id="r2",sequence=1,previous_record_digest=a.content_digest); self.assertTrue(validate_hash_chain([a,b]))
 def test_hash_break(self):
  a=record(); b=record(record_id="r2",sequence=1,previous_record_digest="sha256:"+"0"*64)
  with self.assertRaises(DualPersistenceError): validate_hash_chain([a,b])
 def test_no_receipt_terminal(self):
  with self.assertRaises(PersistenceBarrierError): require_work_state_barrier("READY",None)
if __name__=="__main__": unittest.main()
