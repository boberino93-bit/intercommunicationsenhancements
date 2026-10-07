import unittest

from org_agent_mesh.scheduler_mutation_ledger import (
    GENESIS_HASH,
    MutationLedgerError,
    seal_event,
    validate_ledger,
)


class SchedulerMutationLedgerTests(unittest.TestCase):
    def base_event(self, event_id):
        return {
            "event_id": event_id,
            "observed_at": "2026-10-07T21:00:00Z",
            "actor": "test",
            "source_surface": "TEST",
            "frontend_automation_id": "task-a",
            "old_enabled_state": False,
            "requested_enabled_state": True,
            "resulting_enabled_state": True,
            "authorization_ref": "test-grant",
            "reason": "TEST",
            "readback_verified": True,
            "status": "APPLIED_AND_VERIFIED",
        }

    def test_valid_hash_chain_is_accepted(self):
        first = seal_event(self.base_event("one"), sequence=1, previous_event_hash=GENESIS_HASH)
        second = seal_event(self.base_event("two"), sequence=2, previous_event_hash=first["event_hash"])
        result = validate_ledger([first, second])
        self.assertTrue(result.valid)
        self.assertEqual(result.event_count, 2)
        self.assertEqual(result.terminal_hash, second["event_hash"])

    def test_payload_tampering_is_detected(self):
        first = seal_event(self.base_event("one"), sequence=1, previous_event_hash=GENESIS_HASH)
        first["reason"] = "SILENT_REWRITE"
        with self.assertRaises(MutationLedgerError):
            validate_ledger([first])

    def test_reordering_or_deletion_breaks_chain(self):
        first = seal_event(self.base_event("one"), sequence=1, previous_event_hash=GENESIS_HASH)
        second = seal_event(self.base_event("two"), sequence=2, previous_event_hash=first["event_hash"])
        with self.assertRaises(MutationLedgerError):
            validate_ledger([second])

    def test_duplicate_event_id_is_rejected(self):
        first = seal_event(self.base_event("same"), sequence=1, previous_event_hash=GENESIS_HASH)
        second = seal_event(self.base_event("same"), sequence=2, previous_event_hash=first["event_hash"])
        with self.assertRaises(MutationLedgerError):
            validate_ledger([first, second])


if __name__ == "__main__":
    unittest.main()
