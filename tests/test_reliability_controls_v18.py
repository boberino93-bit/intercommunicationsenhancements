import copy
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from org_agent_mesh.reliability_controls_v18 import *


NOW = datetime(2026, 10, 5, 7, 0, tzinfo=timezone.utc)


class V18ReliabilityAdversarialTests(unittest.TestCase):
    def test_fairness_starvation_protection(self):
        ctl = WeightedFairAdmissionController(
            ResourceCeilings(cpu=1, provider_calls=1, tool_calls=1, write_slots=1, validation_workers=1),
            project_weights={"noisy": 5, "quiet": 1}, starvation_turns=3,
        )
        ctl.submit(ResourceRequest("quiet", "q1", cpu=1))
        admitted = []
        for i in range(8):
            ctl.submit(ResourceRequest("noisy", f"n{i}", priority=10, cpu=1))
            req, _ = ctl.next_admissible()
            if req:
                admitted.append(req.work_id)
                ctl.release(req.work_id)
            if "q1" in admitted:
                break
        self.assertIn("q1", admitted)
        self.assertLessEqual(admitted.index("q1"), 3)

    def test_admission_overcommit_is_bounded(self):
        ctl = WeightedFairAdmissionController(ResourceCeilings(2, 2, 2, 1, 1))
        ctl.submit(ResourceRequest("p1", "a", cpu=2, provider_calls=2))
        ctl.submit(ResourceRequest("p2", "b", cpu=2, provider_calls=2))
        r1, _ = ctl.next_admissible()
        self.assertEqual(r1.work_id, "a")
        r2, d2 = ctl.next_admissible()
        self.assertIsNone(r2)
        self.assertEqual(d2.decision, "THROTTLE")
        self.assertLessEqual(ctl.snapshot()["used"]["cpu"], 2)

    def test_optional_load_shed_on_queue_saturation(self):
        ctl = WeightedFairAdmissionController(ResourceCeilings(1, 1, 1, 1, 1), queue_limit=1)
        ctl.submit(ResourceRequest("p", "a", cpu=1))
        d = ctl.submit(ResourceRequest("p", "b", cpu=1, optional=True))
        self.assertEqual(d.decision, "SHED")

    def test_governance_deadlock_enters_safe_minimal(self):
        g = GovernanceLivenessEngine()
        state = g.evaluate(dependency_cycles=[["policy", "control", "policy"]])
        self.assertEqual(state, LivenessState.DEADLOCK_CONFIRMED)
        d = g.enter_safe_minimal()
        self.assertEqual(g.state, LivenessState.SAFE_MINIMAL_MODE)
        self.assertEqual(d.reason_code, ReasonCode.SAFE_MODE_CONTROL_PLANE_INCONSISTENT.value)

    def test_safe_mode_escape_denied(self):
        m = DegradedModeManager()
        m.set_mode(ServiceMode.SAFE_MINIMAL_MODE, reason="deadlock")
        self.assertTrue(m.authorize_effect("DIAGNOSTIC"))
        with self.assertRaises(GovernanceError):
            m.authorize_effect("EXTERNAL_MUTATION")

    def _human_assertion(self, key=b"human-root-key-material-123"):
        unsigned = {
            "assertion_id": "assert-1", "human_subject": "operator-7", "auth_method": "FIDO2",
            "issuer": "HUMAN_ROOT_IDP", "issued_at_utc": iso(NOW),
            "expires_at_utc": iso(NOW + timedelta(minutes=2)), "nonce": "n-1",
        }
        return HumanIdentityAssertion(**unsigned, signature=sign(unsigned, key))

    def test_agent_initiated_break_glass_denied(self):
        auth = HumanRootAuthenticator(b"human-root-key-material-123")
        bad = replace(self._human_assertion(), issuer="AGENT")
        with self.assertRaises(BreakGlassError):
            auth.verify(bad, now=NOW)

    def test_authenticated_break_glass_is_short_lived_replay_protected_and_audited(self):
        human_key = b"human-root-key-material-123"
        audit = HashChainAuditLog()
        authority = BreakGlassAuthority(HumanRootAuthenticator(human_key), b"break-glass-signing-key-123", audit)
        grant = authority.issue(
            self._human_assertion(human_key), now=NOW, project_id="p1", target="control-plane",
            reason="deadlock", expected_recovery_action="restore verifier", capability_ceiling=["RECOVERY"], ttl_seconds=60,
        )
        self.assertTrue(authority.verify_and_consume(grant, now=NOW + timedelta(seconds=5), project_id="p1", target="control-plane"))
        with self.assertRaises(BreakGlassError):
            authority.verify_and_consume(grant, now=NOW + timedelta(seconds=6), project_id="p1", target="control-plane")
        self.assertTrue(audit.verify())
        self.assertEqual([x["event"]["type"] for x in audit.entries], ["BREAK_GLASS_ISSUED", "BREAK_GLASS_CONSUMED"])

    def test_break_glass_expiry(self):
        human_key = b"human-root-key-material-123"
        authority = BreakGlassAuthority(HumanRootAuthenticator(human_key), b"break-glass-signing-key-123", HashChainAuditLog())
        grant = authority.issue(self._human_assertion(human_key), now=NOW, project_id="p1", target="cp", reason="x", expected_recovery_action="y", capability_ceiling=["RECOVERY"], ttl_seconds=1)
        with self.assertRaises(BreakGlassError):
            authority.verify_and_consume(grant, now=NOW + timedelta(seconds=2), project_id="p1", target="cp")

    def test_schema_skew_blocks_incompatible_writer(self):
        reg = SchemaEvolutionRegistry()
        reg.register(SchemaRecord("handoff", 2, "ACTIVE", "kernel", Compatibility.BREAKING, 2, 2), activate=True)
        with self.assertRaises(SchemaError):
            reg.check_writer("handoff", 1, reader_versions=[2])
        self.assertTrue(reg.check_writer("handoff", 2, reader_versions=[2]))

    def test_partial_migration_resumes_idempotently(self):
        m = TransactionalMigrationCoordinator()
        m.plan("m1", "handoff", 1, 2, {"rev": 7})
        m.enter_canary("m1")
        m.start("m1")
        m.apply_batch("m1", "b1")
        m.pause("m1")
        m.start("m1")
        before = m.apply_batch("m1", "b1")
        self.assertEqual(before.applied_batches, ("b1",))
        m.verify_batch("m1", "b1")
        m.verify("m1")
        done = m.complete("m1")
        self.assertEqual(done.state, MigrationState.COMPLETE)
        self.assertEqual(done.epoch, 1)

    def test_partial_migration_rollback_is_checkpoint_fenced(self):
        m = TransactionalMigrationCoordinator()
        m.plan("m1", "s", 1, 2, {"rev": 7})
        m.enter_canary("m1"); m.start("m1"); m.apply_batch("m1", "b1")
        m.request_rollback("m1", reason="canary regression")
        with self.assertRaises(MigrationError):
            m.rollback("m1", checkpoint={"rev": 8})
        self.assertEqual(m.rollback("m1", checkpoint={"rev": 7}).state, MigrationState.ROLLED_BACK)

    def _evidence(self, key, *, score=.7, sample_count=100, contaminated=False, evidence_id="e1"):
        unsigned = {
            "evidence_id": evidence_id, "subject": "model-a", "capability": "coding", "evaluator": "eval-1",
            "dataset_id": "d1", "sample_count": sample_count, "score": score, "confidence": .9,
            "contaminated": contaminated, "issued_at_utc": iso(NOW), "expires_at_utc": iso(NOW + timedelta(days=1)),
            "provenance_digest": digest({"d":"d1"}),
        }
        return CapabilityEvidence(**unsigned, signature=sign(unsigned, key))

    def test_capability_registry_poisoning_rejected(self):
        key = b"trusted-evaluator-key-1234"
        reg = CapabilityEvidenceRegistry({"eval-1": key})
        e = self._evidence(b"wrong-evaluator-key-123456")
        with self.assertRaises(EvidenceError):
            reg.ingest(e, now=NOW)

    def test_capability_registry_anomalous_jump_rejected(self):
        key = b"trusted-evaluator-key-1234"
        reg = CapabilityEvidenceRegistry({"eval-1": key}, max_score_jump=.2)
        reg.ingest(self._evidence(key, score=.4, sample_count=100, evidence_id="e1"), now=NOW)
        with self.assertRaises(EvidenceError):
            reg.ingest(self._evidence(key, score=.95, sample_count=3, evidence_id="e2"), now=NOW)

    def test_contaminated_benchmark_is_deweighted(self):
        p = EvaluationProvenance("v1", "bench", "1", "candidate", "eval", True, True, True, False, False, False)
        self.assertTrue(p.contaminated)
        self.assertEqual(p.independent_weight, 0.0)
        ledger = ContaminationLedger(); ledger.record(p)
        self.assertFalse(ledger.pristine("v1"))

    def _rollout_manager(self):
        policies = [RingPolicy(r, min_evidence=1, max_error_rate=.05, max_slo_burn=.5, require_human_review=(r == "RING_5_DEFAULT")) for r in RINGS]
        return RolloutManager(policies)

    def test_rollout_ring_skip_denied(self):
        rm = self._rollout_manager(); rm.start("r1", "abc", "sha1")
        with self.assertRaises(RolloutError):
            rm.promote("r1", target_ring="RING_2_PROJECT_CANARY", evidence_count=10, error_rate=0, slo_burn=0)

    def test_canary_regression_halts_and_rolls_back_with_fence(self):
        rm = self._rollout_manager(); s = rm.start("r1", "abc", "sha1")
        s = rm.promote("r1", target_ring="RING_1_ISOLATED", evidence_count=1, error_rate=0, slo_burn=0)
        d = rm.monitor("r1", expected_version=s.version, error_rate=.2, slo_burn=.1)
        self.assertEqual(d.decision, "QUARANTINE")
        q = rm.state("r1")
        with self.assertRaises(RolloutError):
            rm.automatic_rollback("r1", expected_version=q.version - 1, expected_artifact_digest="abc")
        rb = rm.automatic_rollback("r1", expected_version=q.version, expected_artifact_digest="abc")
        self.assertEqual(rb.status, "ROLLED_BACK")
        self.assertEqual(rb.ring_index, 0)

    def test_corrupt_backup_rejected_and_catastrophic_session_loss_reconstructed(self):
        valid = DurableSnapshot.create("github", 7, {"x": 1}, created_at=NOW - timedelta(seconds=2))
        corrupt = DurableSnapshot("artifactory", 8, iso(NOW), {"x": 2}, "bad", valid.payload_digest)
        result = ReconstructionEngine().reconstruct([valid, corrupt], target_time=NOW)
        self.assertTrue(result.success)
        self.assertIn("artifactory", result.rejected_survivors)
        self.assertEqual(result.cutoff_revision, 7)

    def test_split_brain_same_revision_fails_safe(self):
        a = DurableSnapshot.create("a", 8, {"x": 1}, created_at=NOW)
        b = DurableSnapshot.create("b", 8, {"x": 2}, created_at=NOW)
        result = ReconstructionEngine().reconstruct([a, b], target_time=NOW)
        self.assertFalse(result.success)
        self.assertEqual(result.mode, "SAFE_MINIMAL_MODE")

    def test_recovery_objectives_measured_by_drill(self):
        valid = DurableSnapshot.create("github", 7, {"x": 1}, created_at=NOW - timedelta(seconds=2))
        corrupt = DurableSnapshot("artifactory", 8, iso(NOW), {"x": 2}, "bad", valid.payload_digest)
        ev = RecoveryDrillRunner(ReconstructionEngine()).run_corrupt_latest_checkpoint([valid, corrupt])
        obj = RecoveryObjective("cp", 30, 5, 30, 30, 30, 30, 30, 30)
        self.assertTrue(RecoveryDrillRunner.objectives_met(ev, obj))

    def test_control_loop_oscillation_damped(self):
        h = HysteresisController(enter_threshold=.8, exit_threshold=.4, min_samples=3, min_dwell_seconds=5, cooldown_seconds=5)
        self.assertTrue(h.update([.9,.9,.9], now_mono=10))
        self.assertTrue(h.update([.1,.1,.1], now_mono=11))
        self.assertFalse(h.update([.1,.1,.1], now_mono=16))

    def test_routing_churn_freezes_updates(self):
        g = ChurnGuard(max_changes=2, window_seconds=10, freeze_seconds=20)
        self.assertTrue(g.record_change(now_mono=0))
        self.assertTrue(g.record_change(now_mono=1))
        self.assertFalse(g.record_change(now_mono=2))
        self.assertTrue(g.frozen(now_mono=10))
        self.assertFalse(g.frozen(now_mono=23))

    def test_slo_exhaustion_changes_admission(self):
        b = ReliabilityBudgetEngine(error_budget=1, durability_budget=2, liveness_budget=2, change_budget=2)
        b.consume("error", 2)
        self.assertEqual(b.decision(optional=True).decision, "SHED")
        self.assertEqual(b.decision(optional=False, fanout=4).decision, "THROTTLE")
        self.assertEqual(b.decision(optional=False, fanout=1).decision, "DEGRADED")

    def test_slo_registry_tracks_error_budget(self):
        s = SLO("writes", "success_rate", .99, ">=", 3600, "critical", .05, .1, "degrade")
        reg = SLORegistry([s])
        for _ in range(9): reg.record_binary("writes", True)
        reg.record_binary("writes", False)
        h = reg.health("writes")
        self.assertTrue(h["budget_exhausted"])
        self.assertFalse(h["target_ok"])

    def test_state_integrity_detects_divergence_and_corruption(self):
        a = DurableSnapshot.create("a", 1, {"x":1}, created_at=NOW)
        b = DurableSnapshot.create("b", 1, {"x":2}, created_at=NOW)
        c = DurableSnapshot("c", 2, iso(NOW), {"x":3}, "bad")
        r = StateIntegrityEngine().verify_snapshots([a,b,c])
        self.assertFalse(r["ok"])
        self.assertEqual(r["divergent_revisions"], [1])
        self.assertIn("c", r["invalid_stores"])

    def test_dependency_cycle_detected_and_bootstrap_root_excludes_cycle(self):
        g = DependencyGraph({"policy": ["control"], "control": ["policy"], "identity": [], "storage": ["identity"]})
        self.assertTrue(g.cycles())
        self.assertEqual(g.bootstrap_root(["identity", "policy"]), ("identity",))

    def test_clock_rollback_fails_safe(self):
        t = TrustedTimeMonitor(max_skew_seconds=2)
        t.observe(NOW, 100.0)
        with self.assertRaises(TimeReliabilityError):
            t.observe(NOW - timedelta(seconds=10), 101.0)

    def test_clock_provider_skew_fails_safe(self):
        t = TrustedTimeMonitor(max_skew_seconds=2)
        with self.assertRaises(TimeReliabilityError):
            t.observe(NOW, 100.0, provider_wall=NOW + timedelta(seconds=20))

    def _attestation(self, key, artifact_digest="abc"):
        unsigned = {
            "artifact_id":"a1", "source_repository":"o/r", "source_revision":"sha", "builder_id":"builder",
            "toolchain_id":"py", "dependency_inventory_digest":"deps", "build_environment_digest":"env",
            "artifact_digest":artifact_digest, "vulnerability_status":"CLEAR", "trust_decision":"TRUSTED",
            "promotion_ring":"RING_2_PROJECT_CANARY",
        }
        return SupplyChainAttestation(**unsigned, signature=sign(unsigned, key))

    def test_supply_chain_artifact_swap_detected(self):
        key = b"trusted-builder-key-123456"
        v = SupplyChainVerifier({"builder":key})
        a = self._attestation(key, artifact_digest="abc")
        with self.assertRaises(IntegrityError):
            v.verify(a, actual_artifact_digest="def")
        self.assertTrue(v.verify(a, actual_artifact_digest="abc", required_ring="RING_1_ISOLATED"))

    def test_stale_credential_scope_revocation_and_zeroization(self):
        b = CredentialBroker()
        lease = b.issue(project_id="p1", environment="test", capabilities=["READ"], secret_value=b"secret", ttl_seconds=60, provenance="vault", now=NOW)
        self.assertEqual(lease.use(now=NOW, project_id="p1", environment="test", capability="READ"), b"secret")
        with self.assertRaises(CredentialError):
            lease.use(now=NOW, project_id="p2", environment="test", capability="READ")
        b.revoke(lease.credential_id)
        self.assertTrue(lease.revoked)
        self.assertEqual(bytes(lease._secret), b"\x00"*6)
        with self.assertRaises(CredentialError):
            lease.use(now=NOW, project_id="p1", environment="test", capability="READ")

    def test_credential_expiry(self):
        b = CredentialBroker()
        lease = b.issue(project_id="p1", environment="test", capabilities=["READ"], secret_value=b"secret", ttl_seconds=1, provenance="vault", now=NOW)
        with self.assertRaises(CredentialError):
            lease.use(now=NOW+timedelta(seconds=2), project_id="p1", environment="test", capability="READ")

    def test_assurance_case_requires_material_evidence(self):
        builder = AssuranceCaseBuilder()
        with self.assertRaises(AssuranceError):
            builder.build(objective="promote")
        case = builder.build(
            objective="promote", project_id="p1", exact_artifact_digest="abc", policy_certificate_id="pc1",
            ownership_ref="lease1", test_evidence=("ci:1",), independent_validation=("manager", "research"),
            rollback_plan="rollback to sha0", blast_radius_ring="RING_2_PROJECT_CANARY",
            supply_chain_attestation_id="att1", backup_state_ref="backup1", monitoring_plan="watch SLOs",
            acceptance_criteria=("tests pass",), known_risks=("risk1",), unresolved_limitations=(), slo_health={"ok":True},
        )
        self.assertTrue(case.case_id.startswith("ac-"))

    def test_protected_preflight_respects_degraded_mode_and_budgets(self):
        modes = DegradedModeManager(); modes.set_mode(ServiceMode.DEGRADED_NO_EXTERNAL_MUTATION, reason="slo")
        pre = ProtectedTransitionPreflight(degraded_modes=modes, budget_engine=ReliabilityBudgetEngine(error_budget=1,durability_budget=1,liveness_budget=1,change_budget=1))
        with self.assertRaises(GovernanceError):
            pre.check(effect="EXTERNAL_MUTATION", optional=False, fanout=1)

    def test_reference_game_day_runs_and_meets_objective(self):
        result = run_reference_game_day(NOW)
        self.assertTrue(result["scenario"]["success"])
        self.assertTrue(result["objectives_met"])
        self.assertEqual(len(result["evidence_digest"]), 64)


if __name__ == "__main__":
    unittest.main(verbosity=2)
