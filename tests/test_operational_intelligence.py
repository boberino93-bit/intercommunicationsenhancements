from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.operational_intelligence import (
    assert_active_execution_claim,
    participation_state,
    validate_operational_intelligence_envelope,
)
from org_agent_mesh.project_scope import ProjectScopeError

NOW = datetime(2026, 10, 7, 13, 30, tzinfo=timezone.utc)

BASE = {
    "schema": "org-agent-mesh/project-intelligence-envelope/v1",
    "message_id": "msg-1",
    "benefit_class": "DISCOVERY",
    "source_project_id": "source",
    "consumer_project_id": "consumer",
    "created_at_utc": "2026-10-07T13:00:00Z",
    "expires_at_utc": "2026-10-07T14:00:00Z",
    "correlation_id": "corr-1",
    "subject": "related research",
    "scope": "bounded metadata",
    "artifact_refs": [],
    "provenance_refs": ["source-checkpoint-1"],
    "validation_state": "CANDIDATE",
    "availability_state": "UNKNOWN",
    "capability_refs": [],
    "request_ref": None,
    "assignment_ref": None,
    "authority_conveyed": False,
}


class OperationalIntelligenceTest(unittest.TestCase):
    def test_discovery_is_indirect_benefit_only(self):
        self.assertTrue(validate_operational_intelligence_envelope(BASE, now=NOW))
        self.assertEqual(participation_state(BASE, now=NOW), "INDIRECT_BENEFIT_ONLY")

    def test_cross_project_intelligence_never_conveys_authority(self):
        with self.assertRaises(ProjectScopeError):
            validate_operational_intelligence_envelope(dict(BASE, authority_conveyed=True), now=NOW)

    def test_passive_knowledge_requires_validated_state(self):
        envelope = dict(BASE, benefit_class="PASSIVE_KNOWLEDGE", artifact_refs=["artifact-1"])
        with self.assertRaises(ProjectScopeError):
            validate_operational_intelligence_envelope(envelope, now=NOW)
        envelope["validation_state"] = "VALIDATED"
        self.assertTrue(validate_operational_intelligence_envelope(envelope, now=NOW))

    def test_expertise_awareness_does_not_imply_assignment(self):
        envelope = dict(BASE, benefit_class="EXPERTISE_AWARENESS", availability_state="AVAILABLE", assignment_ref="assignment-1")
        with self.assertRaises(ProjectScopeError):
            validate_operational_intelligence_envelope(envelope, now=NOW)

    def test_routing_request_is_not_assignment(self):
        envelope = dict(BASE, benefit_class="ROUTING_REQUEST", request_ref="route-1")
        self.assertTrue(validate_operational_intelligence_envelope(envelope, now=NOW))
        self.assertEqual(participation_state(envelope, now=NOW), "INDIRECT_BENEFIT_ONLY")
        with self.assertRaises(ProjectScopeError):
            validate_operational_intelligence_envelope(dict(envelope, assignment_ref="assignment-1"), now=NOW)

    def test_active_execution_requires_matching_canonical_evidence(self):
        envelope = dict(BASE, benefit_class="ACTIVE_EXECUTION", validation_state="NOT_APPLICABLE", availability_state="ACTIVE", assignment_ref="presence/source/research-1")
        evidence = {"project_id": "source", "task_id": "task-1", "assignee_agent_id": "research-1", "status": "ACTIVE", "observed_at_utc": "2026-10-07T13:20:00Z", "evidence_ref": "presence/source/research-1"}
        self.assertTrue(assert_active_execution_claim(envelope, assignment_evidence=evidence, now=NOW))
        self.assertEqual(participation_state(envelope, assignment_evidence=evidence, now=NOW), "ACTIVE_PARTICIPATION_VERIFIED")

    def test_active_execution_rejects_wrong_project_evidence(self):
        envelope = dict(BASE, benefit_class="ACTIVE_EXECUTION", validation_state="NOT_APPLICABLE", availability_state="ACTIVE", assignment_ref="presence/source/research-1")
        evidence = {"project_id": "other", "task_id": "task-1", "assignee_agent_id": "research-1", "status": "ACTIVE", "observed_at_utc": "2026-10-07T13:20:00Z", "evidence_ref": "presence/source/research-1"}
        with self.assertRaises(ProjectScopeError):
            assert_active_execution_claim(envelope, assignment_evidence=evidence, now=NOW)

    def test_expired_envelope_rejected(self):
        with self.assertRaises(ProjectScopeError):
            validate_operational_intelligence_envelope(dict(BASE, expires_at_utc="2026-10-07T13:15:00Z"), now=NOW)


if __name__ == "__main__":
    unittest.main()
