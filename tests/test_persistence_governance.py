import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

def load(path): return json.loads((ROOT/path).read_text())

class PersistenceGovernanceTests(unittest.TestCase):
    def test_mutation_policy_preserves_hard_gate_and_single_use(self):
        p=load('governance/MUTATION_AUTHORIZATION_POLICY.json')
        self.assertEqual(p['status'],'ACTIVE_HARD_GATE')
        self.assertEqual(p['valid_authorization_sources'],['CURRENT_HUMAN_SINGLE_USE_AUTHORIZATION_CASE'])
        self.assertTrue(p['authorization_case']['single_use'])
        self.assertFalse(p['authorization_case']['session_persistence'])
        self.assertTrue(p['scheduled_work']['each_distinct_mutation_case_requires_fresh_human_authorization'])
        self.assertFalse(p['delegation']['may_create_new_human_authorization'])
        self.assertFalse(p['role_is_mutation_authority'])
        self.assertFalse(p['claim_or_lease_is_mutation_authority'])
        self.assertFalse(p['authentication_is_mutation_authority'])

    def test_invalid_authorization_sources_are_preserved(self):
        p=load('governance/MUTATION_AUTHORIZATION_POLICY.json'); invalid=set(p['invalid_authorization_sources'])
        required={'INFERRED_INTENT','CAPABILITY_QUESTION','DESIGN_DISCUSSION','ENTHUSIASM_OR_PRAISE','ROLE_OR_SENIORITY','PROJECT_OWNERSHIP','TOOL_AVAILABILITY','REPOSITORY_PERMISSION','URGENCY','EXPECTED_USEFULNESS','PRIOR_AUTHORIZATION','PRIOR_AUTHENTICATION','ACTIVE_TASK_CONTRACT_ALONE','SCHEDULE_FIRE','PARENT_AGENT_DELEGATION_ALONE','SESSION_CONTEXT','CONVERSATION_CONTINUITY'}
        self.assertTrue(required <= invalid)

    def test_persistence_exception_is_narrow_and_non_authoritative(self):
        e=load('governance/MUTATION_AUTHORIZATION_POLICY.json')['narrow_capability_exception_to_case_requirement']
        self.assertTrue(e['does_not_extend_valid_authorization_sources'])
        self.assertFalse(e['is_general_mutation_authority'])
        self.assertFalse(e['consequence_gateway_bypass'])
        denied=set(e['denied_effects'])
        for effect in {'WRITE_SOURCE','WRITE_ACCEPTED_STATE','CLAIM_TASK','CONTROL_PROJECT_LIFECYCLE','SCHEDULE_MUTATION','BRANCH_CREATE','PULL_REQUEST_STATE_CHANGE','CROSS_PROJECT_MUTATION','PROTECTED_EFFECT'}:
            self.assertIn(effect,denied)

    def test_coordination_policy_preserves_existing_denials_and_adds_dual_gate(self):
        p=load('governance/COORDINATION_PUBLICATION_POLICY.json')
        self.assertEqual(p['status'],'ACTIVE_HARD_GATE')
        self.assertEqual(p['route_source']['registry'],'PROJECT_ROLE_ROUTING_REGISTRY.json')
        self.assertEqual(p['github_backup']['branch_creation'],'DENY')
        self.assertEqual(p['github_backup']['pull_request_mutation'],'DENY')
        self.assertEqual(p['artifactory_publication']['artifact_or_production_namespace'],'DENY')
        self.assertIn('CROSS_PROJECT_MUTATION',p['subordinate_denied_durable_effects'])
        self.assertIn('OVERWRITE_DELETE_RENAME_MOVE_DENIED',p['invariants'])
        self.assertTrue(p['both_destinations_required'])
        self.assertTrue(p['persistence_receipt']['sink_project_binding_required'])

    def test_completion_integrity_preserves_old_duty_and_adds_dual_gate(self):
        t=(ROOT/'protocols/completion_integrity.md').read_text()
        for phrase in ['Work is not complete while the acting agent knows it has left avoidable damage','INCOMPLETE_REMEDIATION_REQUIRED','INCOMPLETE_BLOCKED','This directive does not expand authority','Local policy may strengthen it but may not weaken it']:
            self.assertIn(phrase,t)
        self.assertIn('DUAL_PERSISTENCE_CONFIRMED',t)
        self.assertIn('ConsequenceGateway',t)

    def test_mutation_protocol_preserves_no_ambient_authority(self):
        t=(ROOT/'protocols/mutation_authorization.md').read_text()
        self.assertIn('There is no session-wide',t)
        self.assertIn('even one issued seconds earlier',t)
        self.assertIn('Every distinct mutation case requires its own case ID',t)
        self.assertIn('does not extend `valid_authorization_sources`',t)
        self.assertIn('ConsequenceGateway',t)

    def test_universal_entrypoint_cannot_default_generic_agent_to_primary(self):
        t=(ROOT/'UNIVERSAL_AGENT_ENTRYPOINT.md').read_text()
        self.assertNotIn('the universal default is `primary`',t)
        self.assertIn('enter `ROLELESS_DEMAND_DRIVEN_ADMISSION`',t)
        self.assertIn('PRIMARY is never a generic default',t)

    def test_stage15_persistence_gate_never_grants_launch_authority(self):
        p=load('governance/STAGE15_PREFLIGHT_POLICY.json')
        self.assertEqual(p['status'],'ACTIVE_FAIL_CLOSED')
        self.assertTrue(p['persistence']['required_per_project'])
        self.assertTrue(p['persistence']['zero_loss_required'])
        self.assertFalse(p['readiness_semantics']['preflight_ready_is_launch_authorization'])
        self.assertTrue(p['stage15_launch_requires_separate_authorization'])

    def test_dual_policy_is_not_claimed_worm(self):
        p=load('governance/DUAL_PERSISTENCE_POLICY.json')
        self.assertIn('NOT_WORM',p['immutability_claim'])
        self.assertEqual(p['protected_effect_authority'],'UNCHANGED_CONSEQUENCE_GATEWAY_ONLY')
        self.assertFalse(p['activation']['stage15_launch'])
        self.assertFalse(p['activation']['production_promotion'])

    def test_first_attempt_transaction_is_truthful_failure_record(self):
        p=load('governance/DUAL_PERSISTENCE_HARDENING_TRANSACTION_20261006.json')
        self.assertIn('FAILED_INTEGRATED_VALIDATION',p['status'])
        self.assertEqual(p['attempt_1_validation']['tests_run'],530)
        self.assertEqual(p['attempt_1_validation']['promotion_disposition'],'DENY')
        self.assertTrue(p['fresh_security_validation_receipts_required_for_repair'])
        self.assertFalse(p['production_promotion'])

if __name__=='__main__': unittest.main()
