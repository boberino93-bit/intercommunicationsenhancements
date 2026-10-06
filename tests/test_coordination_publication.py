import unittest
from org_agent_mesh.coordination_publication import *
from org_agent_mesh.project_scope import ProjectScopeError
def route(ns="/DuoOpen-AgentBus/messages"): return CoordinationRoute("duo-open","boberino93-bit/duo-open",ns)
def ok(role="RESEARCH",**kw):
 d=dict(actor_project_id="duo-open",actor_role=role,actor_capabilities=["PUBLISH_MESSAGE"],route=route(),target_repository="boberino93-bit/duo-open",target_artifactory_namespace="/DuoOpen-AgentBus/messages",github_backup_path="agentbus-backup/coordination-messages/r.json"); d.update(kw); return require_coordination_publication(**d)
class CoordinationPublicationTests(unittest.TestCase):
 def test_both_required(self): self.assertTrue(ok())
 def test_forum_only_denied(self):
  with self.assertRaises(CoordinationPublicationError): ok(github_backup_path=None)
 def test_github_only_denied(self):
  with self.assertRaises(CoordinationPublicationError): ok(target_artifactory_namespace=None)
 def test_primary_and_recovery_supported(self): self.assertTrue(ok("PRIMARY")); self.assertTrue(ok("RECOVERY"))
 def test_incomplete_route_denied(self):
  with self.assertRaises(CoordinationPublicationError): ok(route=route(None))
 def test_foreign_repo(self):
  with self.assertRaises(ProjectScopeError): ok(target_repository="boberino93-bit/benefitflow")
 def test_authority_smuggling(self):
  with self.assertRaises(CoordinationPublicationError): ok(authority_conveyed=True)
 def test_overwrite_denied(self):
  with self.assertRaises(CoordinationPublicationError): ok(operation="OVERWRITE")
 def test_traversal_denied(self):
  with self.assertRaises(CoordinationPublicationError): ok(github_backup_path="agentbus-backup/coordination-messages/../x")
if __name__=="__main__": unittest.main()
