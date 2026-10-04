from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from org_agent_mesh.artifacts import ArtifactRegistry
from org_agent_mesh.audit import AuditLedger
from org_agent_mesh.constants import PROTOCOL_VERSION
from org_agent_mesh.control_plane import AgentSession, StaleVersion
from org_agent_mesh.project_scope import ProjectBinding, ProjectScopeError
from org_agent_mesh.tasks import TaskRegistry

def session(project,agent,instance,capabilities):
    binding=ProjectBinding(project,f"repo/{project}",f"/work/{project}",agent,instance,PROTOCOL_VERSION,tuple(capabilities))
    return AgentSession(agent).bind(binding).initialize().activate()

class TaskArtifactAuditTest(unittest.TestCase):
    def test_task_claim_and_stale_transition(self):
        primary=session("a","primary","a-primary-1",("CLAIM_TASK","APPROVE_CHANGE")); worker=session("a","worker","a-worker-1",("CLAIM_TASK",)); tasks=TaskRegistry(); task=tasks.create(primary,"a","task-001")
        claimed=tasks.claim(worker,"a","task-001",expected_version=task.version); active=tasks.transition(worker,"a","task-001",expected_version=claimed.version,status="ACTIVE"); self.assertEqual("ACTIVE",active.status)
        with self.assertRaises(StaleVersion): tasks.transition(worker,"a","task-001",expected_version=claimed.version,status="COMPLETED")
    def test_foreign_task_claim_denied(self):
        creator=session("a","primary","a-primary-1",("CLAIM_TASK",)); foreign=session("b","worker","b-worker-1",("CLAIM_TASK",)); tasks=TaskRegistry(); tasks.create(creator,"a","task-001")
        with self.assertRaises(ProjectScopeError): tasks.claim(foreign,"a","task-001",expected_version=1)
    def test_artifact_ownership_and_cas(self):
        writer=session("a","worker","a-worker-1",("WRITE_ARTIFACTS","READ_ARTIFACTS")); foreign=session("b","worker","b-worker-1",("READ_ARTIFACTS",)); artifacts=ArtifactRegistry(); created=artifacts.publish(writer,"a","analysis-001",b"v1",artifact_type="analysis",source="task-001",task_id="task-001"); updated=artifacts.replace(writer,"a","analysis-001",b"v2",expected_version=created.version,source="task-001"); self.assertEqual(2,updated.version)
        with self.assertRaises(StaleVersion): artifacts.replace(writer,"a","analysis-001",b"v3",expected_version=created.version,source="task-001")
        with self.assertRaises(ProjectScopeError): artifacts.read(foreign,"a","analysis-001")
    def test_audit_record_is_project_and_instance_attributable(self):
        actor=session("a","primary","a-primary-1",("READ_SOURCE",)); audit=AuditLedger(); record=audit.record(actor,"a",operation="release-gate",result="ACCEPTED",task_id="task-001",message_id="msg-001",resource_id="package-001",before_version=1,after_version=2,details={"reason":"verified"}); self.assertEqual("a",record.project_id); self.assertEqual("primary",record.agent_id); self.assertEqual("a-primary-1",record.agent_instance_id); self.assertEqual((record,),audit.read_project("a"))

if __name__=="__main__": unittest.main()
