from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.constants import PROTOCOL_VERSION
from org_agent_mesh.control_plane import AgentSession
from org_agent_mesh.delivery import DeliveryLedger, RetryExhausted, safe_append_message
from org_agent_mesh.project_scope import ProjectBinding, ProjectScopeError

BASE = {
    "schema": "org-agent-mesh/message/v2", "protocol_version": PROTOCOL_VERSION, "id": "m1", "project_id": "project-a",
    "destination_project_id": "project-a", "timestamp_utc": "2099-01-01T00:00:00Z", "from_agent": "worker",
    "from_agent_instance_id": "worker-1", "from_role": "SPECIALIST", "to": ["manager"], "kind": "FINDING", "priority": "normal",
    "subject": "s", "summary": "x", "applies_to_state": "v", "evidence": [], "artifacts": [], "reply_to": None,
    "supersedes": [], "requires_ack": True, "tags": [], "correlation_id": "c1", "causation_id": None,
    "idempotency_key": "idem-1", "expires_at_utc": None,
}


def session(project, agent, instance):
    binding = ProjectBinding(project, f"repo/{project}", f"/work/{project}", agent, instance, PROTOCOL_VERSION, ("PUBLISH_MESSAGE",))
    return AgentSession(agent).bind(binding).initialize().activate()


def sender(): return session("project-a", "worker", "worker-1")
def recipient(): return session("project-a", "manager", "manager-1")


class DeliveryRecoveryTest(unittest.TestCase):
    def test_unsafe_message_is_quarantined(self):
        with tempfile.TemporaryDirectory() as directory:
            result = safe_append_message(Path(directory)/"messages", Path(directory)/"quarantine", dict(BASE, destination_project_id="project-b"), sender_session=sender(), expected_project_id="project-a")
            self.assertEqual("QUARANTINED", result["outcome"]); self.assertTrue(result["quarantine_path"].exists())

    def test_duplicate_delivery_is_safe_noop(self):
        with tempfile.TemporaryDirectory() as directory:
            messages=Path(directory)/"messages"; quarantine=Path(directory)/"quarantine"
            self.assertEqual("ACCEPTED", safe_append_message(messages, quarantine, BASE, sender_session=sender(), expected_project_id="project-a")["outcome"])
            duplicate=dict(BASE,id="m2",timestamp_utc="2099-01-01T00:00:01Z")
            self.assertEqual("DUPLICATE", safe_append_message(messages, quarantine, duplicate, sender_session=sender(), expected_project_id="project-a")["outcome"])

    def test_acknowledgement_lifecycle_completes(self):
        ledger=DeliveryLedger(); r=recipient(); record=ledger.register(BASE, recipient_session=r); self.assertEqual("RECEIVED", record.status)
        record=ledger.transition(r,"project-a","idem-1","ACCEPTED"); record=ledger.transition(r,"project-a","idem-1","STARTED"); record=ledger.transition(r,"project-a","idem-1","COMPLETED")
        self.assertEqual("COMPLETED",record.status)

    def test_duplicate_register_preserves_attempt_count(self):
        ledger=DeliveryLedger(); r=recipient(); first=ledger.register(BASE,recipient_session=r); second=ledger.register(dict(BASE,id="m2"),recipient_session=r)
        self.assertEqual(first,second); self.assertEqual(1,second.attempts)

    def test_retry_is_bounded(self):
        ledger=DeliveryLedger(); r=recipient(); ledger.register(BASE,recipient_session=r,max_attempts=2); ledger.transition(r,"project-a","idem-1","ACCEPTED"); ledger.transition(r,"project-a","idem-1","FAILED",error="temporary")
        retry=ledger.retry(r,"project-a","idem-1"); self.assertEqual(2,retry.attempts); ledger.transition(r,"project-a","idem-1","FAILED",error="still failing")
        with self.assertRaises(RetryExhausted): ledger.retry(r,"project-a","idem-1")

    def test_foreign_acknowledgement_denied(self):
        ledger=DeliveryLedger(); r=recipient(); ledger.register(BASE,recipient_session=r); foreign=session("project-b","manager","b-manager-1")
        with self.assertRaises(ProjectScopeError): ledger.transition(foreign,"project-a","idem-1","ACCEPTED")


if __name__ == "__main__": unittest.main()
