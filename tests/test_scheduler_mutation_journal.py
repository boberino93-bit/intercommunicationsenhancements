import unittest

from org_agent_mesh.scheduler_mutation_journal import (
    GENESIS_HASH,
    MutationJournalError,
    seal_claim,
    seal_event,
    validate_journal,
)


class SchedulerMutationJournalTests(unittest.TestCase):
    def make_pair(self, sequence, event_id, previous_hash, actor="actor"):
        claim = seal_claim({
            "sequence": sequence,
            "event_id": event_id,
            "actor": actor,
            "previous_event_hash": previous_hash,
            "claimed_at": "2026-10-07T22:00:00Z",
            "purpose": "TEST",
        })
        event = seal_event({
            "sequence": sequence,
            "event_id": event_id,
            "previous_event_hash": previous_hash,
            "claim_hash": claim["claim_hash"],
            "observed_at": "2026-10-07T22:00:00Z",
            "actor": actor,
            "source_surface": "TEST",
            "frontend_automation_id": "task-a",
            "old_enabled_state": False,
            "requested_enabled_state": True,
            "resulting_enabled_state": None,
            "authorization_ref": "test",
            "reason": "TEST",
            "readback_verified": False,
            "status": "PLANNED",
        })
        return claim, event

    def test_valid_claim_event_chain(self):
        c1, e1 = self.make_pair(1, "one", GENESIS_HASH)
        c2, e2 = self.make_pair(2, "two", e1["event_hash"])
        result = validate_journal(claims=[c1, c2], events=[e1, e2])
        self.assertTrue(result.valid)
        self.assertEqual(result.next_sequence, 3)
        self.assertEqual(result.terminal_hash, e2["event_hash"])

    def test_stranded_claim_blocks_automatic_mutation(self):
        c1, e1 = self.make_pair(1, "one", GENESIS_HASH)
        c2, _ = self.make_pair(2, "two", e1["event_hash"])
        with self.assertRaises(MutationJournalError):
            validate_journal(claims=[c1, c2], events=[e1])

    def test_sequence_fork_is_rejected(self):
        c1, e1 = self.make_pair(1, "one", GENESIS_HASH)
        competing = dict(c1)
        competing["event_id"] = "competing"
        with self.assertRaises(MutationJournalError):
            validate_journal(claims=[c1, competing], events=[e1])

    def test_claim_event_binding_mismatch_is_rejected(self):
        c1, e1 = self.make_pair(1, "one", GENESIS_HASH)
        e1["claim_hash"] = "f" * 64
        with self.assertRaises(MutationJournalError):
            validate_journal(claims=[c1], events=[e1])

    def test_payload_tampering_is_rejected(self):
        c1, e1 = self.make_pair(1, "one", GENESIS_HASH)
        e1["reason"] = "TAMPERED"
        with self.assertRaises(MutationJournalError):
            validate_journal(claims=[c1], events=[e1])


if __name__ == "__main__":
    unittest.main()
