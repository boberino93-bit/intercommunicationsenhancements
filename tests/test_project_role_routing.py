import json
from pathlib import Path
import unittest

from org_agent_mesh.project_role_routing import RoutingError, resolve_route, validate_local_contract, validate_registry

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = {
    "schema": "org-agent-mesh/project-role-routing-registry/v1", "routing_contract_version": "1.2.0", "mode": "FAIL_CLOSED",
    "projects": {"alpha": {"repository": "owner/alpha", "repository_id": 101, "forum_namespace": "alpha::messages", "forum_locator": {"authority": "INTERNAL_ARTIFACTORY", "namespace": "alpha::messages", "repository_view": {"mode": "SNAPSHOT_BACKUP", "path": "agentbus/messages"}}, "artifact_namespace": "alpha::artifacts", "handoff_paths": ["START_HERE.md", "state"], "local_contract_path": "AGENT_BOOTSTRAP.json", "routing_contract_version": "1.2.0", "roles": ["primary", "manager", "research"]}}
}
LOCAL_CONTRACT = {"schema": "org-agent-mesh/local-agent-bootstrap/v1", "routing_contract_version": "1.2.0", "mode": "FAIL_CLOSED", "project_id": "alpha", "repository": {"full_name": "owner/alpha", "id": 101}, "forum": {"authority": "INTERNAL_ARTIFACTORY", "namespace": "alpha::messages", "repository_view": {"mode": "SNAPSHOT_BACKUP", "path": "agentbus/messages"}}, "artifact_namespace": "alpha::artifacts", "handoff_paths": ["START_HERE.md", "state"], "authorized_roles": ["primary", "manager", "research"]}

class ProjectRoleRoutingTests(unittest.TestCase):
    def test_valid_route_resolves_and_acknowledges(self):
        route=resolve_route(REGISTRY,project_id="alpha",role_id="research",current_repository="owner/alpha",current_repository_id=101); self.assertEqual(route.repository,"owner/alpha"); self.assertEqual(route.forum_authority,"INTERNAL_ARTIFACTORY"); self.assertEqual(route.forum_repository_view_mode,"SNAPSHOT_BACKUP"); self.assertEqual(route.forum_repository_view_path,"agentbus/messages"); self.assertIn("IDENTITY RESOLVED: project=alpha; role=research",route.acknowledgement("handoff-7"))
    def test_local_contract_matches_registry(self): validate_local_contract(REGISTRY,project_id="alpha",contract=LOCAL_CONTRACT)
    def test_local_contract_forum_drift_fails_closed(self):
        c=json.loads(json.dumps(LOCAL_CONTRACT)); c["forum"]["repository_view"]["mode"]="LIVE_MIRROR"
        with self.assertRaisesRegex(RoutingError,"local_contract_forum_repository_view_mismatch"): validate_local_contract(REGISTRY,project_id="alpha",contract=c)
    def test_forum_namespace_and_locator_must_agree(self):
        r=json.loads(json.dumps(REGISTRY)); r["projects"]["alpha"]["forum_locator"]["namespace"]="beta::messages"
        with self.assertRaisesRegex(RoutingError,"forum_locator_namespace_mismatch"): validate_registry(r)
    def test_none_repository_view_requires_null_path(self):
        r=json.loads(json.dumps(REGISTRY)); r["projects"]["alpha"]["forum_locator"]["repository_view"]={"mode":"NONE","path":"fake/messages"}
        with self.assertRaisesRegex(RoutingError,"forum_repository_view_path_must_be_null"): validate_registry(r)
    def test_unknown_project_fails_closed(self):
        with self.assertRaisesRegex(RoutingError,"unknown_project"): resolve_route(REGISTRY,project_id="beta",role_id="primary",current_repository="owner/beta")
    def test_unknown_role_fails_closed(self):
        with self.assertRaisesRegex(RoutingError,"unknown_or_unauthorized_role"): resolve_route(REGISTRY,project_id="alpha",role_id="admin",current_repository="owner/alpha")
    def test_repository_mismatch_fails_closed(self):
        with self.assertRaisesRegex(RoutingError,"repository_identity_mismatch"): resolve_route(REGISTRY,project_id="alpha",role_id="primary",current_repository="owner/beta")
    def test_stable_repository_id_mismatch_fails_closed(self):
        with self.assertRaisesRegex(RoutingError,"repository_stable_id_mismatch"): resolve_route(REGISTRY,project_id="alpha",role_id="primary",current_repository="owner/alpha",current_repository_id=999)
    def test_non_fail_closed_registry_is_rejected(self):
        r=dict(REGISTRY); r["mode"]="PERMISSIVE"
        with self.assertRaisesRegex(RoutingError,"registry_not_fail_closed"): resolve_route(r,project_id="alpha",role_id="primary",current_repository="owner/alpha")
    def test_duplicate_repository_binding_is_rejected(self):
        r=json.loads(json.dumps(REGISTRY)); beta=json.loads(json.dumps(r["projects"]["alpha"])); beta.update({"repository_id":202,"forum_namespace":"beta::messages","artifact_namespace":"beta::artifacts"}); beta["forum_locator"]["namespace"]="beta::messages"; r["projects"]["beta"]=beta
        with self.assertRaisesRegex(RoutingError,"duplicate_repository_binding"): validate_registry(r)
    def test_unsafe_handoff_path_is_rejected(self):
        r=json.loads(json.dumps(REGISTRY)); r["projects"]["alpha"]["handoff_paths"]=["../foreign/messages"]
        with self.assertRaisesRegex(RoutingError,"unsafe_handoff_path"): validate_registry(r)
    def test_real_registry_and_local_contract_validate_v15(self):
        r=json.loads((ROOT/"PROJECT_ROLE_ROUTING_REGISTRY.json").read_text()); validate_registry(r); self.assertEqual(r["routing_contract_version"],"1.5.0"); self.assertEqual(r["mode"],"FAIL_CLOSED_LOCAL_CONTINUE_GLOBAL"); self.assertTrue(r["communication_awareness"]["required_on_startup"]); self.assertEqual(r["fresh_agent_context"]["authority"],"ORIENTATION_ONLY"); self.assertEqual(r["autonomous_continuation"]["fail_closed_scope"],"AFFECTED_MUTATION_OR_BRANCH_ONLY")
        for pid,p in r["projects"].items():
            self.assertIsInstance(p["repository_id"],int); self.assertEqual(p["local_contract_path"],"AGENT_BOOTSTRAP.json"); self.assertEqual(p["roles"],["primary","manager","research"]); self.assertIn("MASTER_HANDOFF.json",p["handoff_paths"]); self.assertIn("AGENT_CONTEXT_REFERENCE.md",p["handoff_paths"]); self.assertEqual(p["master_handoff_path"],"MASTER_HANDOFF.json"); self.assertEqual(p["context_reference_path"],"AGENT_CONTEXT_REFERENCE.md")
            if pid=="xrp-thesis": self.assertEqual(p["forum_locator"]["authority"],"INTERNAL_ARTIFACTORY"); self.assertEqual(p["forum_locator"]["namespace"],"/XRPTHESIS-AgentBus/messages"); self.assertEqual(p["forum_locator"]["repository_view"],{"mode":"SNAPSHOT_BACKUP","path":"agentbus-backup/coordination-messages"})
            else: self.assertEqual(p["forum_locator"]["authority"],"INTERNAL_ARTIFACTORY")
            if pid=="warp-propulsion-lab": self.assertEqual(p["routing_contract_version"],"1.3.0"); self.assertEqual(p["effective_continuation_overlay_version"],"1.5.0"); self.assertEqual(p["local_bootstrap_migration_state"],"LEGACY_LOCAL_BOOTSTRAP_RETAINED"); self.assertTrue(p["continuation_overlay_authority"])
            else: self.assertEqual(p["routing_contract_version"],"1.5.0")
        c=json.loads((ROOT/"AGENT_BOOTSTRAP.json").read_text()); validate_local_contract(r,project_id="intercommunicationsenhancements",contract=c); self.assertEqual(c["fresh_agent_context"]["authority"],"ORIENTATION_ONLY"); self.assertTrue(c["autonomous_continuation"]["localized_fail_closed"])
    def test_xrp_internal_forum_route_is_fixed(self):
        r=json.loads((ROOT/"PROJECT_ROLE_ROUTING_REGISTRY.json").read_text()); x=r["projects"]["xrp-thesis"]; self.assertEqual(x["forum_namespace"],"/XRPTHESIS-AgentBus/messages"); self.assertEqual(x["forum_locator"]["authority"],"INTERNAL_ARTIFACTORY")
    def test_v15_rejects_permissive_mode(self):
        r=json.loads((ROOT/"PROJECT_ROLE_ROUTING_REGISTRY.json").read_text()); r["mode"]="PERMISSIVE_CONTINUE_GLOBAL"
        with self.assertRaisesRegex(RoutingError,"registry_not_fail_closed"): validate_registry(r)
    def test_v15_rejects_context_reference_as_authority(self):
        r=json.loads((ROOT/"PROJECT_ROLE_ROUTING_REGISTRY.json").read_text()); r["fresh_agent_context"]["authority"]="AUTHORITATIVE"
        with self.assertRaisesRegex(RoutingError,"fresh_agent_context_authority_expansion"): validate_registry(r)
    def test_v15_rejects_unbounded_fail_closed_scope(self):
        r=json.loads((ROOT/"PROJECT_ROLE_ROUTING_REGISTRY.json").read_text()); r["autonomous_continuation"]["fail_closed_scope"]="IGNORE_AND_CONTINUE"
        with self.assertRaisesRegex(RoutingError,"unsafe_continuation_fail_closed_scope"): validate_registry(r)
    def test_v15_rejects_cross_project_write_expansion(self):
        r=json.loads((ROOT/"PROJECT_ROLE_ROUTING_REGISTRY.json").read_text()); r["rules"]["cross_project_write_default"]="ALLOW"
        with self.assertRaisesRegex(RoutingError,"unsafe_v15_registry_rule_cross_project_write_default"): validate_registry(r)
    def test_v15_local_contract_cannot_disable_localized_fail_closed(self):
        r=json.loads((ROOT/"PROJECT_ROLE_ROUTING_REGISTRY.json").read_text()); c=json.loads((ROOT/"AGENT_BOOTSTRAP.json").read_text()); c["autonomous_continuation"]["localized_fail_closed"]=False
        with self.assertRaisesRegex(RoutingError,"local_fail_closed_disabled"): validate_local_contract(r,project_id="intercommunicationsenhancements",contract=c)
    def test_v15_legacy_project_requires_explicit_overlay(self):
        r=json.loads((ROOT/"PROJECT_ROLE_ROUTING_REGISTRY.json").read_text()); r["projects"]["warp-propulsion-lab"].pop("effective_continuation_overlay_version")
        with self.assertRaisesRegex(RoutingError,"project_routing_contract_version_mismatch"): validate_registry(r)
    def test_v15_legacy_overlay_requires_authority_reference(self):
        r=json.loads((ROOT/"PROJECT_ROLE_ROUTING_REGISTRY.json").read_text()); r["projects"]["warp-propulsion-lab"].pop("continuation_overlay_authority")
        with self.assertRaisesRegex(RoutingError,"missing_continuation_overlay_authority"): validate_registry(r)
    def test_v14_rejects_role_mode_overlap(self):
        r=json.loads((ROOT/"PROJECT_ROLE_ROUTING_REGISTRY.json").read_text()); r["projects"]["benefitflow"]["execution_modes"].append("research")
        with self.assertRaisesRegex(RoutingError,"role_execution_mode_overlap"): validate_registry(r)
    def test_v14_requires_master_handoff_in_handoff_paths(self):
        r=json.loads((ROOT/"PROJECT_ROLE_ROUTING_REGISTRY.json").read_text()); r["projects"]["duo-open"]["handoff_paths"].remove("MASTER_HANDOFF.json")
        with self.assertRaisesRegex(RoutingError,"master_handoff_missing_from_handoff_paths"): validate_registry(r)
    def test_v14_local_contract_cannot_disable_master_handoff(self):
        r=json.loads((ROOT/"PROJECT_ROLE_ROUTING_REGISTRY.json").read_text()); c=json.loads((ROOT/"AGENT_BOOTSTRAP.json").read_text()); c["master_handoff"]["required_before_mutation"]=False
        with self.assertRaisesRegex(RoutingError,"local_master_handoff_gate_disabled"): validate_local_contract(r,project_id="intercommunicationsenhancements",contract=c)
    def test_v13_requires_communication_awareness(self):
        r=json.loads((ROOT/"PROJECT_ROLE_ROUTING_REGISTRY.json").read_text()); r.pop("communication_awareness")
        with self.assertRaisesRegex(RoutingError,"missing_communication_awareness"): validate_registry(r)
    def test_v13_rejects_permissive_visibility_default(self):
        r=json.loads((ROOT/"PROJECT_ROLE_ROUTING_REGISTRY.json").read_text()); r["communication_awareness"]["default_visibility_claim"]="FULL"
        with self.assertRaisesRegex(RoutingError,"unsafe_default_visibility_claim"): validate_registry(r)
    def test_routing_contract_is_dependency_closed_for_role_packages(self):
        shared=set(json.loads((ROOT/"packaging"/"agent_package_dependencies.json").read_text())["shared_patterns"])
        for expected in ("PROJECT_ROLE_ROUTING_REGISTRY.json","AGENT_BOOTSTRAP.json","MASTER_HANDOFF.json","bootstrap/PROJECT_ROLE_DISCOVERY.md","bootstrap/IDENTITY_GATE.md","org_agent_mesh/*.py","protocols/*.md","schemas/*.json"): self.assertIn(expected,shared)

if __name__ == "__main__": unittest.main()
