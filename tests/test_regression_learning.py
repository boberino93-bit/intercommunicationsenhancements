import unittest

from org_agent_mesh.regression_learning import (
    ALLOWED_PRIMARY_MAINTENANCE_CLASSES,
    PROTECTED_CLASSES,
    RegressionEvent,
    RegressionLedger,
    normalize_intake,
    primary_maintenance_allowed,
)


class RegressionLearningTests(unittest.TestCase):
    def test_fingerprint_is_deterministic(self):
        self.assertEqual(
            RegressionEvent.fingerprint("PACKAGING", " a   b "),
            RegressionEvent.fingerprint("packaging", "a b"),
        )

    def test_unscoped_chat_does_not_require_project(self):
        normalize_intake(
            event_id="E1", level="UNSCOPED_CHAT", project_id="", family="PACKAGING",
            signature="placeholder presented as ready", provenance="OBSERVED", severity=4,
            evidence_ref="chat:1",
        )

    def test_project_chat_requires_project(self):
        with self.assertRaisesRegex(ValueError, "PROJECT_ID_REQUIRED"):
            normalize_intake(
                event_id="E2", level="PROJECT_CHAT", project_id="", family="STATE",
                signature="stale state", provenance="OBSERVED", severity=3,
                evidence_ref="chat:2",
            )

    def test_event_cannot_convey_authority(self):
        with self.assertRaisesRegex(ValueError, "CANNOT_CONVEY_AUTHORITY"):
            RegressionEvent(
                "E3", "UNSCOPED_CHAT", "", "AUTH", "claim", "OBSERVED", 5, "chat:3",
                authority_conveyed=True,
            ).validate()

    def test_hash_chain_and_snapshot_verify(self):
        ledger = RegressionLedger()
        ledger.append(RegressionEvent("E1", "PROJECT_CHAT", "p1", "X", "x", "OBSERVED", 3, "r1"))
        ledger.append(RegressionEvent("E2", "PROJECT_CHAT", "p1", "X", "y", "RETRIEVED", 3, "r2"))
        snapshot = ledger.snapshot()
        self.assertTrue(ledger.verify())
        self.assertTrue(ledger.verify_snapshot(snapshot))

    def test_snapshot_detects_tail_truncation(self):
        ledger = RegressionLedger()
        ledger.append(RegressionEvent("E1", "PROJECT_CHAT", "p1", "X", "x", "OBSERVED", 3, "r1"))
        ledger.append(RegressionEvent("E2", "PROJECT_CHAT", "p1", "X", "y", "OBSERVED", 3, "r2"))
        snapshot = ledger.snapshot()
        ledger.events.pop()
        ledger.hashes.pop()
        self.assertTrue(ledger.verify())
        self.assertFalse(ledger.verify_snapshot(snapshot))

    def test_duplicate_event_id_is_denied(self):
        ledger = RegressionLedger()
        event = RegressionEvent("E1", "PROJECT_CHAT", "p1", "X", "x", "OBSERVED", 3, "r1")
        ledger.append(event)
        with self.assertRaisesRegex(ValueError, "EVENT_ID_REPLAY_DENIED"):
            ledger.append(event)

    def test_family_correlation_is_case_insensitive(self):
        ledger = RegressionLedger()
        ledger.append(RegressionEvent("E1", "PROJECT_CHAT", "p1", "routing drift", "x", "OBSERVED", 4, "r1"))
        ledger.append(RegressionEvent("E2", "PROJECT_CHAT", "p1", "ROUTING_DRIFT", "y", "RETRIEVED", 4, "r2"))
        self.assertEqual(ledger.candidate("routing drift"), "HOTFIX_CANDIDATE")

    def test_three_projects_escalate_service_pack(self):
        ledger = RegressionLedger()
        for index in range(3):
            ledger.append(RegressionEvent(
                f"E{index}", "PROJECT_CHAT", f"p{index}", "ROUTING", f"sig{index}", "OBSERVED", 4, f"r{index}"
            ))
        self.assertEqual(ledger.candidate("ROUTING"), "SERVICE_PACK_CANDIDATE")

    def test_recurrence_after_remediation_escalates_service_pack(self):
        ledger = RegressionLedger()
        ledger.append(RegressionEvent(
            "E1", "PROJECT_CHAT", "p1", "CLEANUP", "x", "OBSERVED", 4, "r1",
            remediated=True, remediation_ref="fix:1",
        ))
        ledger.append(RegressionEvent(
            "E2", "PROJECT_CHAT", "p1", "CLEANUP", "x-again", "OBSERVED", 4, "r2",
            remediation_ref="fix:1", post_remediation_recurrence=True,
        ))
        self.assertEqual(ledger.candidate("CLEANUP"), "SERVICE_PACK_CANDIDATE")
        self.assertEqual(ledger.family_stats("CLEANUP")["remediation_effectiveness"], 0.0)

    def test_remediation_state_requires_reference(self):
        with self.assertRaisesRegex(ValueError, "REMEDIATION_REFERENCE_REQUIRED"):
            RegressionEvent(
                "E1", "PROJECT_CHAT", "p1", "CLEANUP", "x", "OBSERVED", 3, "r1",
                remediated=True,
            ).validate()

    def test_protected_classes_never_use_primary_maintenance_lane(self):
        for change_class in PROTECTED_CLASSES:
            self.assertFalse(primary_maintenance_allowed(
                change_class, reversible=True, tests_passed=True, bounded_scope=True,
            ))

    def test_unknown_class_is_denied_not_assumed_safe(self):
        self.assertFalse(primary_maintenance_allowed(
            "NEW_UNCLASSIFIED_THING", reversible=True, tests_passed=True, bounded_scope=True,
        ))

    def test_each_allowlisted_class_still_requires_all_safety_conditions(self):
        for change_class in ALLOWED_PRIMARY_MAINTENANCE_CLASSES:
            self.assertTrue(primary_maintenance_allowed(
                change_class, reversible=True, tests_passed=True, bounded_scope=True,
            ))
            self.assertFalse(primary_maintenance_allowed(
                change_class, reversible=False, tests_passed=True, bounded_scope=True,
            ))
            self.assertFalse(primary_maintenance_allowed(
                change_class, reversible=True, tests_passed=False, bounded_scope=True,
            ))
            self.assertFalse(primary_maintenance_allowed(
                change_class, reversible=True, tests_passed=True, bounded_scope=False,
            ))

    def test_security_sensitive_flag_denies_even_allowlisted_class(self):
        self.assertFalse(primary_maintenance_allowed(
            "DOC_NORMALIZATION", reversible=True, tests_passed=True, bounded_scope=True,
            touches_security=True,
        ))

    def test_cross_project_write_blocks_primary_lane(self):
        self.assertFalse(primary_maintenance_allowed(
            "DOC_NORMALIZATION", reversible=True, tests_passed=True, bounded_scope=True,
            cross_project_write=True,
        ))


if __name__ == "__main__":
    unittest.main()
