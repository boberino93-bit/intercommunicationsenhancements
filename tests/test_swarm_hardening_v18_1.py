import unittest
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone

from org_agent_mesh.reliability_v18_core import sign, digest, iso
from org_agent_mesh.diagnostic_learning import *
from org_agent_mesh.intercommunication_diagnostics import *
from org_agent_mesh.consequence_gateway import *
from org_agent_mesh.operational_diagnostics import *

NOW = datetime(2026, 10, 5, 8, 0, tzinfo=timezone.utc)


class DiagnosticLearningTests(unittest.TestCase):
    def obs(self, oid, strategy, reward, *, partition=EvidencePartition.TRAIN, confidence=.9, contaminated=False, verified=True):
        return DiagnosticObservation(
            observation_id=oid, project_id="p1", global_run_id="r1", agent_id="a",
            agent_instance_id="ai1", work_id=f"w-{oid}", strategy_id=strategy,
            outcome_reward=reward, confidence=confidence, evidence_partition=partition,
            evidence_refs=(f"e:{oid}",), created_at_utc=iso(NOW),
            contaminated=contaminated, verified=verified,
        )

    def test_learning_is_advisory_and_selects_better_strategy(self):
        e = DiagnosticLearningEngine(DiagnosticPolicy(min_samples_for_recommendation=3))
        for i, r in enumerate([.7,.8,.9]): e.observe(self.obs(f"a{i}", "A", r))
        for i, r in enumerate([.1,.2,.3]): e.observe(self.obs(f"b{i}", "B", r))
        rec = recommendation_from_engine(e)
        self.assertEqual(rec.strategy_id, "A")
        self.assertFalse(rec.authority)
        self.assertEqual(rec.validation_state, "CANDIDATE")
        self.assertFalse(e.snapshot()["may_execute_effects"])

    def test_holdout_never_trains(self):
        e = DiagnosticLearningEngine(DiagnosticPolicy(min_samples_for_recommendation=1))
        e.observe(self.obs("h1", "A", 1.0, partition=EvidencePartition.HOLDOUT))
        self.assertIsNone(e.recommend())
        h = e.evaluate_holdout()
        self.assertFalse(h["trained_on_holdout"])
        self.assertEqual(h["strategies"]["A"]["samples"], 1)

    def test_contaminated_or_low_confidence_evidence_is_quarantined(self):
        e = DiagnosticLearningEngine(DiagnosticPolicy(min_samples_for_recommendation=1))
        self.assertEqual(e.observe(self.obs("x1","A",1,contaminated=True)), "QUARANTINED")
        self.assertEqual(e.observe(self.obs("x2","A",1,confidence=.1)), "QUARANTINED")
        self.assertIsNone(e.recommend())
        self.assertEqual(e.snapshot()["quarantine_count"], 2)

    def test_observation_idempotency_and_collision(self):
        e = DiagnosticLearningEngine()
        o = self.obs("i1","A",.5)
        self.assertEqual(e.observe(o), "LEARNED")
        self.assertEqual(e.observe(o), "IDEMPOTENT")
        with self.assertRaises(DiagnosticLearningError):
            e.observe(replace(o, outcome_reward=.6))

    def test_drift_detection_blocks_recommendation(self):
        p = DiagnosticPolicy(min_samples_for_recommendation=3, drift_window=2, drift_threshold=.5, max_history_per_strategy=8)
        e = DiagnosticLearningEngine(p)
        for i,r in enumerate([.9,.9,-.2,-.2]):
            e.observe(self.obs(f"d{i}","A",r))
        self.assertTrue(e.detect_drift("A"))
        self.assertIsNone(e.recommend())


class VisibilityTests(unittest.TestCase):
    def frame(self, seq, at, *, mat="m1", state=PresenceState.ACTIVE, fence="f1", agent="ai1", task="task"):
        return HeartbeatObservation(
            frame_id=f"{agent}-{seq}", project_id="p1", agent_id="a", agent_instance_id=agent,
            task_semantic_id=task, sequence=seq, observed_at_utc=iso(at), state=state,
            progress_digest=f"p{seq}", material_delta_digest=mat, ownership_epoch=1, fence_token=fence,
        )

    def test_heartbeat_coalesces_unchanged_status_and_persists_material_delta(self):
        c = VisibilityCoordinator()
        d1 = c.record(self.frame(1,NOW))
        d2 = c.record(self.frame(2,NOW+timedelta(seconds=10)))
        d3 = c.record(self.frame(3,NOW+timedelta(seconds=20),mat="m2"))
        self.assertTrue(d1.ephemeral_emit)
        self.assertFalse(d2.ephemeral_emit)
        self.assertFalse(d2.durable_emit)
        self.assertTrue(d3.ephemeral_emit)
        self.assertTrue(d3.durable_emit)

    def test_heartbeat_emits_at_nominal_cadence(self):
        c = VisibilityCoordinator()
        c.record(self.frame(1,NOW))
        d = c.record(self.frame(2,NOW+timedelta(seconds=45)))
        self.assertTrue(d.ephemeral_emit)
        self.assertFalse(d.durable_emit)

    def test_stale_or_replayed_sequence_rejected(self):
        c = VisibilityCoordinator()
        c.record(self.frame(2,NOW))
        with self.assertRaises(VisibilityError):
            c.record(self.frame(2,NOW+timedelta(seconds=1)))

    def test_peer_discovery_is_non_authoritative_and_stale_filtered(self):
        c = VisibilityCoordinator()
        c.record(self.frame(1,NOW,agent="ai1"))
        c.record(self.frame(1,NOW-timedelta(seconds=100),agent="ai2"))
        matches = PeerDiscoveryIndex(c).discover(project_id="p1", task_semantic_id="task", now=NOW+timedelta(seconds=1))
        self.assertEqual([m.agent_instance_id for m in matches], ["ai1"])
        self.assertFalse(matches[0].authoritative)

    def test_observability_aggregator_cannot_transfer_ownership(self):
        c = VisibilityCoordinator()
        c.record(self.frame(1,NOW))
        snap = ReadOnlyObservabilityAggregator(c, allowed_projects=["p1"]).snapshot(now=NOW)
        self.assertFalse(snap["authority"])
        self.assertFalse(snap["may_transfer_ownership"])
        self.assertEqual(snap["projects"]["p1"]["active"], 1)

    def test_same_epoch_different_fence_is_durable_conflict_signal_only(self):
        c = VisibilityCoordinator()
        c.record(self.frame(1,NOW,fence="f1"))
        d = c.record(self.frame(2,NOW+timedelta(seconds=1),fence="f2"))
        self.assertTrue(d.durable_emit)
        self.assertFalse(d.authority_changed)
        self.assertEqual(c.metrics()["ownership_conflicts_observed"], 1)


class ConsequenceGatewayTests(unittest.TestCase):
    KEY=b"trusted-independent-issuer-key"
    def prepared(self, **kw):
        return PreparedAction.create(
            action_id="act1", project_id="p1", work_id="w1", preparer_instance_id="prep1",
            effect_class="EXTERNAL_MUTATION", target="system:x", parameters={"x":1},
            policy_digest="pol", capability_digest="cap", precondition_digest="pre",
            ownership_epoch=7, fence_token="f7", prepared_at=NOW, expires_at=NOW+timedelta(minutes=2),
            **kw
        )
    def grant(self, p, **changes):
        raw = {
            "grant_id":"g1","issuer_id":"reviewer","issuer_instance_id":"review1","project_id":"p1",
            "agent_instance_id":"prep1","action_digest":p.action_digest,"allowed_operation":p.effect_class,
            "allowed_target":p.target,"effect_class":p.effect_class,"ownership_epoch":7,
            "fence_token":"f7","policy_digest":"pol","capability_digest":"cap","precondition_digest":"pre",
            "issued_at_utc":iso(NOW),"expires_at_utc":iso(NOW+timedelta(minutes=1)),
            "max_uses":1,"nonce":"n1","use_policy":"SINGLE_USE",
        }
        raw.update(changes)
        return CommitAuthorizationGrant(**raw, signature=sign(raw,self.KEY))
    def current(self, **changes):
        raw = dict(project_id="p1",actor_instance_id="prep1",ownership_epoch=7,fence_token="f7",
                   policy_digest="pol",capability_digest="cap",precondition_digest="pre",health_allows_effect=True)
        raw.update(changes)
        return CurrentCommitState(**raw)

    def test_exact_action_grant_allows_confirmed_effect_once(self):
        p=self.prepared(); g=self.grant(p)
        v=CommitGrantVerifier({"reviewer":self.KEY}); gw=ConsequenceGateway(v)
        r=gw.commit(attempt_id="at1",prepared=p,grant=g,current=self.current(),now=NOW+timedelta(seconds=1),
                    executor=lambda _: EffectOutcome(EffectState.CONFIRMED,"evidence"))
        self.assertEqual(r.effect_state,"CONFIRMED")
        with self.assertRaises(ConsequenceGatewayError):
            gw.commit(attempt_id="at2",prepared=p,grant=g,current=self.current(),now=NOW+timedelta(seconds=2),
                      executor=lambda _: EffectOutcome(EffectState.CONFIRMED,"evidence"))

    def test_preparer_cannot_authorize_self(self):
        p=self.prepared(); g=self.grant(p,issuer_instance_id="prep1")
        with self.assertRaises(ConsequenceGatewayError):
            CommitGrantVerifier({"reviewer":self.KEY}).verify_and_consume(prepared=p,grant=g,current=self.current(),now=NOW)

    def test_stale_fence_or_precondition_denied(self):
        p=self.prepared(); g=self.grant(p)
        with self.assertRaises(ConsequenceGatewayError):
            CommitGrantVerifier({"reviewer":self.KEY}).verify_and_consume(
                prepared=p,grant=g,current=self.current(fence_token="stale"),now=NOW)

    def test_parameter_change_invalidates_exact_action_grant(self):
        p=self.prepared(); g=self.grant(p)
        p2=PreparedAction.create(
            action_id="act1", project_id="p1", work_id="w1", preparer_instance_id="prep1",
            effect_class="EXTERNAL_MUTATION", target="system:x", parameters={"x":2},
            policy_digest="pol", capability_digest="cap", precondition_digest="pre",
            ownership_epoch=7, fence_token="f7", prepared_at=NOW, expires_at=NOW+timedelta(minutes=2))
        with self.assertRaises(ConsequenceGatewayError):
            CommitGrantVerifier({"reviewer":self.KEY}).verify_and_consume(prepared=p2,grant=g,current=self.current(),now=NOW)

    def test_revocation_race_denies_commit(self):
        p=self.prepared(); g=self.grant(p)
        v=CommitGrantVerifier({"reviewer":self.KEY}); v.revoke(g.grant_id)
        with self.assertRaises(ConsequenceGatewayError):
            v.verify_and_consume(prepared=p,grant=g,current=self.current(),now=NOW)

    def test_unknown_effect_never_blind_retries(self):
        p=self.prepared(); g=self.grant(p)
        r=ConsequenceGateway(CommitGrantVerifier({"reviewer":self.KEY})).commit(
            attempt_id="a", prepared=p, grant=g, current=self.current(), now=NOW,
            executor=lambda _: (_ for _ in ()).throw(RuntimeError("network lost after send")))
        self.assertEqual(r.effect_state,"UNKNOWN_EFFECT")
        self.assertFalse(r.retry_allowed)
        self.assertEqual(r.next_action,"VERIFY_OR_RECOVERY")


    def test_wrong_agent_or_missing_capability_denied(self):
        p=self.prepared()
        with self.assertRaises(ConsequenceGatewayError):
            CommitGrantVerifier({"reviewer":self.KEY}).verify_and_consume(
                prepared=p,grant=self.grant(p,agent_instance_id="other"),current=self.current(),now=NOW)
        with self.assertRaises(ConsequenceGatewayError):
            CommitGrantVerifier({"reviewer":self.KEY}).verify_and_consume(
                prepared=p,grant=self.grant(p),current=self.current(required_capability_present=False),now=NOW)

    def test_quarantined_project_and_invalid_cross_project_exchange_denied(self):
        p=self.prepared()
        with self.assertRaises(ConsequenceGatewayError):
            CommitGrantVerifier({"reviewer":self.KEY}).verify_and_consume(
                prepared=p,grant=self.grant(p),current=self.current(project_quarantined=True),now=NOW)
        cp=PreparedAction.create(
            action_id="cross", project_id="p1", work_id="w1", preparer_instance_id="prep1",
            effect_class="CROSS_PROJECT_MUTATION", target="peer:p2", parameters={"x":1},
            policy_digest="pol", capability_digest="cap", precondition_digest="pre",
            ownership_epoch=7, fence_token="f7", prepared_at=NOW, expires_at=NOW+timedelta(minutes=2))
        cg=self.grant(cp, grant_id="g-cross")
        with self.assertRaises(ConsequenceGatewayError):
            CommitGrantVerifier({"reviewer":self.KEY}).verify_and_consume(
                prepared=cp,grant=cg,current=self.current(cross_project_exchange_validated=False),now=NOW)

    def test_provenance_observation_never_becomes_authority(self):
        p=ProvenanceRecord("document","doc:1",ProvenanceClass.OBSERVATION_ONLY,"abc")
        self.assertFalse(p.grants_authority)

    def test_sensitive_egress_requires_sanitization_and_receipt_is_non_authoritative(self):
        e=EgressPolicy({"tool":{DataClass.SENSITIVE}})
        with self.assertRaises(ConsequenceGatewayError):
            e.authorize_with_receipt(project_id="p1",work_id="w1",target="tool",data_class=DataClass.SENSITIVE,
                                     content_digest="h",sanitized=False,reason="diagnostic")
        r=e.authorize_with_receipt(project_id="p1",work_id="w1",target="tool",data_class=DataClass.SENSITIVE,
                                  content_digest="h",sanitized=True,reason="diagnostic")
        self.assertFalse(r.authority)

    def test_egress_policy_denies_restricted_and_unapproved_class(self):
        e=EgressPolicy({"logs":{DataClass.INTERNAL}})
        self.assertTrue(e.authorize(target="logs",data_class=DataClass.INTERNAL))
        with self.assertRaises(ConsequenceGatewayError):
            e.authorize(target="logs",data_class=DataClass.SENSITIVE)
        with self.assertRaises(ConsequenceGatewayError):
            e.authorize(target="logs",data_class=DataClass.RESTRICTED)



class OperationalDiagnosticTests(unittest.TestCase):
    def test_scheduler_probe_distinguishes_preventive_from_mitigation(self):
        weak = SchedulerAdmissionEvidence(False, False, True, "runtime")
        strong = SchedulerAdmissionEvidence(True, True, True, "runtime")
        self.assertEqual(weak.assessment()["mode"], "MITIGATION_ONLY")
        self.assertEqual(strong.assessment()["mode"], "PREVENTIVE")

    def test_backend_probe_never_overclaims_partial_backend(self):
        e = DistributedBackendEvidence(True, True, True, True, False, False, False, False, "sqlite-ref")
        a = e.assessment()
        self.assertEqual(a["assurance"], "PARTIAL")
        self.assertIn("multi_node_tested", a["missing"])
        self.assertFalse(a["authority"])

    def test_runtime_readiness_is_diagnostic_not_deployment_authority(self):
        result = RuntimeReadinessDiagnostic().evaluate(
            scheduler=SchedulerAdmissionEvidence(False, False, True, "host"),
            backend=DistributedBackendEvidence(True, True, True, True, False, False, False, False, "sqlite"),
            repository=RepositoryGovernanceEvidence(False, False, False, False, False, "github"),
        )
        self.assertEqual(result["overall_assurance"], "PARTIAL")
        self.assertFalse(result["may_authorize_deployment"])


if __name__=="__main__":
    unittest.main()
