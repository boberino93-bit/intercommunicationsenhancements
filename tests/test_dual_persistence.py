import unittest
from org_agent_mesh.dual_persistence import *

NOW="2026-10-06T04:20:00+00:00"
D0="sha256:"+"0"*64
D1="sha256:"+"1"*64

def record(record_id="r1", **kw):
    d=dict(record_id=record_id,project_id="duo-open",run_id="run1",agent_id="a1",role="RESEARCH",work_id="w1",event_type="FINDING",sequence=0,created_at=NOW,summary="x",payload={"x":1})
    d.update(kw); return MaterialWorkRecord(**d)

def ack(sink, rec, digest=None):
    return SinkAck(sink=sink,project_id=rec.project_id,record_id=rec.record_id,content_digest=digest or rec.content_digest,location="/forum/r1" if sink==SINK_ARTIFACTORY else "agentbus-backup/coordination-messages/r1.json",acknowledged_at=NOW)

def receipt(rec, *, art=True, github=True, art_digest=None, github_digest=None):
    return DualPersistenceReceipt(
        receipt_id="p", project_id=rec.project_id, record_id=rec.record_id,
        content_digest=rec.content_digest, prepared_at=NOW,
        artifactory_ack=ack(SINK_ARTIFACTORY,rec,art_digest) if art else None,
        github_ack=ack(SINK_GITHUB,rec,github_digest) if github else None,
    )

class DualPersistenceTests(unittest.TestCase):
    def test_prepared_not_ready(self):
        r=record(); p=DualPersistenceReceipt("p",r.project_id,r.record_id,r.content_digest,NOW)
        self.assertEqual(p.state,PERSISTENCE_PREPARED)
        with self.assertRaises(PersistenceBarrierError): require_work_state_barrier("READY",record=r,receipt=p)

    def test_both_confirm(self):
        r=record(); p=receipt(r)
        self.assertEqual(p.state,DUAL_PERSISTENCE_CONFIRMED)
        self.assertTrue(require_work_state_barrier("COMPLETE",record=r,receipt=p))

    def test_one_sided_degraded(self):
        r=record(); p=receipt(r,github=False)
        self.assertEqual(p.state,ARTIFACTORY_ONLY)
        with self.assertRaises(PersistenceBarrierError): require_work_state_barrier("HANDOFF_READY",record=r,receipt=p)

    def test_mismatch_quarantine(self):
        r=record(); p=receipt(r,art_digest=D0)
        self.assertEqual(p.state,DIGEST_MISMATCH)

    def test_idempotent_retry(self):
        r=record(); i=PersistenceIndex(); a=ack(SINK_ARTIFACTORY,r)
        i.observe(a); self.assertEqual(i.observe(a),ARTIFACTORY_ONLY)
        self.assertEqual(i.observe(ack(SINK_GITHUB,r)),DUAL_PERSISTENCE_CONFIRMED)

    def test_same_id_different_digest_conflict(self):
        r=record(); i=PersistenceIndex(); i.observe(ack(SINK_ARTIFACTORY,r))
        with self.assertRaises(PersistenceConflictError): i.observe(ack(SINK_GITHUB,r,D0))

    def test_reconcile(self):
        f=reconcile_digest_views(project_id="duo-open",artifactory_records={"a":D0,"b":D1},github_records={"a":D0,"c":D1})
        self.assertEqual([x.state for x in f],[DUAL_PERSISTENCE_CONFIRMED,ARTIFACTORY_ONLY,GITHUB_ONLY])

    def test_record_stable_digest(self):
        self.assertEqual(record().content_digest,record().content_digest)

    def test_secret_guard(self):
        with self.assertRaises(Exception): record(payload={"ephemeral_value":"secret"})

    def test_hash_chain(self):
        a=record("a",sequence=0); b=record("b",sequence=1,previous_record_digest=a.content_digest)
        self.assertTrue(validate_hash_chain([a,b]))

    def test_hash_chain_break(self):
        a=record("a"); b=record("b",sequence=1,previous_record_digest=D0)
        with self.assertRaises(DualPersistenceError): validate_hash_chain([a,b])

    def test_progress_not_blocked(self):
        self.assertTrue(require_work_state_barrier("PROGRESS"))

    def test_no_receipt_terminal_blocked(self):
        with self.assertRaises(PersistenceBarrierError): require_work_state_barrier("READY",record=record(),receipt=None)

if __name__=='__main__': unittest.main()
