import unittest
from org_agent_mesh.checkpoint_bus import StageCheckpoint
from org_agent_mesh.checkpoint_persistence import PersistedCheckpoint, checkpoint_digest, latest_persisted_ready_for_cycle, CheckpointPersistenceError
from org_agent_mesh.dual_persistence import DualPersistenceReceipt, SinkAck, SINK_ARTIFACTORY, SINK_GITHUB

NOW="2026-10-06T04:20:00+00:00"

def cp(state="RESEARCH_HANDOFF_READY", project_id="duo-open", checkpoint_id="cp1", sequence=1):
    return StageCheckpoint(project_id=project_id,checkpoint_id=checkpoint_id,cycle_id="2026-10-05T21:00:00-07:00",stage="RESEARCHER_1",run_id="run1",sequence=sequence,state=state,phase="DONE",trigger="SCHEDULED",created_at="2026-10-05T21:20:00-07:00")

def receipt(c, both=True, digest=None, project_id=None):
    d=digest or checkpoint_digest(c); project=project_id or c.project_id
    a=SinkAck(SINK_ARTIFACTORY,project,c.checkpoint_id,d,"/DuoOpen-AgentBus/messages/cp1",NOW)
    g=SinkAck(SINK_GITHUB,project,c.checkpoint_id,d,"agentbus-backup/coordination-messages/cp1.json",NOW) if both else None
    return DualPersistenceReceipt("r",project,c.checkpoint_id,d,NOW,a,g)

class CheckpointPersistenceTests(unittest.TestCase):
    def test_ready_requires_confirmed_receipt(self):
        c=cp(); self.assertTrue(PersistedCheckpoint(c,receipt(c)).require_ready())
    def test_one_sided_not_selected(self):
        c=cp(); p=PersistedCheckpoint(c,receipt(c,False)); self.assertIsNone(latest_persisted_ready_for_cycle([p],project_id=c.project_id,cycle_id=c.cycle_id,stage=c.stage))
    def test_progress_not_ready(self):
        c=cp("RESEARCH_PROGRESS"); p=PersistedCheckpoint(c,receipt(c));
        with self.assertRaises(CheckpointPersistenceError): p.require_ready()
    def test_project_binding(self):
        c=cp()
        with self.assertRaises(CheckpointPersistenceError): PersistedCheckpoint(c,receipt(c,project_id="benefitflow"))
    def test_record_binding(self):
        c=cp(); other=cp(checkpoint_id="cp2")
        with self.assertRaises(CheckpointPersistenceError): PersistedCheckpoint(c,receipt(other))
    def test_digest_binding(self):
        c=cp(); bad="sha256:"+"0"*64
        with self.assertRaises(CheckpointPersistenceError): PersistedCheckpoint(c,receipt(c,digest=bad))
    def test_latest_ready_selects_highest_confirmed_sequence(self):
        a=cp(checkpoint_id="cp1",sequence=1); b=cp(checkpoint_id="cp2",sequence=2)
        result=latest_persisted_ready_for_cycle([PersistedCheckpoint(a,receipt(a)),PersistedCheckpoint(b,receipt(b))],project_id=a.project_id,cycle_id=a.cycle_id,stage=a.stage)
        self.assertEqual(result.checkpoint.checkpoint_id,"cp2")

if __name__=='__main__': unittest.main()
