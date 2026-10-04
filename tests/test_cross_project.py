from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from org_agent_mesh.constants import PROTOCOL_VERSION
from org_agent_mesh.control_plane import AgentSession
from org_agent_mesh.cross_project import validate_cross_project_exchange
from org_agent_mesh.project_scope import ProjectBinding, ProjectScopeError

BASE={"schema":"org-agent-mesh/cross-project-exchange/v1","exchange_id":"x1","source_project_id":"a","destination_project_id":"b","requesting_agent_id":"primary","purpose":"share bounded result","data_classification":"INTERNAL","requested_artifacts":["artifact-1"],"allowed_use":"evaluation","created_at_utc":"2026-10-03T00:00:00Z","expires_at_utc":"2026-10-04T00:00:00Z","correlation_id":"c1","approval":{"status":"APPROVED","approved_by":"human"}}
NOW=datetime(2026,10,3,12,0,tzinfo=timezone.utc)

def session(project="a",*,capability=True,agent="primary"):
    capabilities=("CROSS_PROJECT_EXCHANGE",) if capability else ()
    binding=ProjectBinding(project,f"repo/{project}",f"/work/{project}",agent,f"{project}-{agent}-1",PROTOCOL_VERSION,capabilities)
    return AgentSession(agent).bind(binding).initialize().activate()

class CrossProjectTest(unittest.TestCase):
    def test_denied_without_capability(self):
        with self.assertRaises(ProjectScopeError): validate_cross_project_exchange(BASE,requester_session=session(capability=False),now=NOW)
    def test_explicit_capability_and_approval(self): self.assertTrue(validate_cross_project_exchange(BASE,requester_session=session(),now=NOW))
    def test_requires_approval(self):
        with self.assertRaises(ProjectScopeError): validate_cross_project_exchange(dict(BASE,approval={"status":"PENDING"}),requester_session=session(),now=NOW)
    def test_claimed_source_must_match_bound_project(self):
        with self.assertRaises(ProjectScopeError): validate_cross_project_exchange(BASE,requester_session=session(project="b"),now=NOW)
    def test_requesting_agent_must_match_session(self):
        with self.assertRaises(ProjectScopeError): validate_cross_project_exchange(dict(BASE,requesting_agent_id="forged"),requester_session=session(),now=NOW)
    def test_expired_exchange_rejected(self):
        with self.assertRaises(ProjectScopeError): validate_cross_project_exchange(BASE,requester_session=session(),now=datetime(2026,10,4,1,0,tzinfo=timezone.utc))

if __name__=="__main__": unittest.main()
