import unittest

from org_agent_mesh.coordination_publication import (
    CoordinationPublicationError, CoordinationRoute, require_coordination_publication,
)
from org_agent_mesh.dual_persistence import (
    ARTIFACTORY_ONLY, DIGEST_MISMATCH, DUAL_PERSISTENCE_CONFIRMED, GITHUB_ONLY,
    SINK_ARTIFACTORY, SINK_GITHUB, DualPersistenceError, DualPersistenceReceipt,
    MaterialWorkRecord, PersistenceBarrierError, PersistenceConflictError, PersistenceIndex,
    SinkAck, build_persistence_health, reconcile_digest_views, require_work_state_barrier,
    validate_hash_chain,
)
from org_agent_mesh.checkpoint_bus import StageCheckpoint
from org_agent_mesh.checkpoint_persistence import (
    CheckpointPersistenceError, PersistedCheckpoint, checkpoint_digest,
    latest_persisted_ready_for_cycle,
)
from org_agent_mesh.stage15_preflight import Stage15PreflightError, validate_persistence_health
from org_agent_mesh.project_scope import ProjectScopeError

NOW = "2026-10-06T04:40:00+00:00"
DIGEST0 = "sha256:" + "0" * 64
DIGEST1 = "sha256:" + "1" * 64


def record(record_id="r1", project_id="duo-open", previous=None, supersedes=None):
    return MaterialWorkRecord(
        record_id=record_id, project_id=project_id, run_id="run1", agent_id="agent1",
        role="RESEARCH", work_id="work1", event_type="FINDING", sequence=0,
        created_at=NOW, summary="finding", payload={"value": 1},
        previous_record_digest=previous, supersedes_record_id=supersedes,
    )


def ack(sink, rec, *, project_id=None, digest=None, operation="CREATE_NEW_RECORD", append_only=True):
    return SinkAck(
        sink=sink, project_id=project_id or rec.project_id, record_id=rec.record_id,
        content_digest=digest or rec.content_digest,
        location="/forum/r1" if sink == SINK_ARTIFACTORY else "boberino93-bit/duo-open:agentbus-backup/coordination-messages/r1.json",
        acknowledged_at=NOW, operation=operation, append_only=append_only,
    )


def confirmed(rec):
    return DualPersistenceReceipt(
        receipt_id="p1", project_id=rec.project_id, record_id=rec.record_id,
        content_digest=rec.content_digest, prepared_at=NOW,
        artifactory_ack=ack(SINK_ARTIFACTORY, rec), github_ack=ack(SINK_GITHUB, rec),
    )


def route(namespace="/DuoOpen-AgentBus/messages"):
    return CoordinationRoute("duo-open", "boberino93-bit/duo-open", namespace)


def publish(**overrides):
    args = dict(
        actor_project_id="duo-open", actor_role="RESEARCH", actor_capabilities=["PUBLISH_MESSAGE"],
        route=route(), target_repository="boberino93-bit/duo-open",
        target_artifactory_namespace="/DuoOpen-AgentBus/messages",
        github_backup_path="agentbus-backup/coordination-messages/r1.json",
    )
    args.update(overrides)
    return require_coordination_publication(**args)


def checkpoint(state="RESEARCH_HANDOFF_READY", checkpoint_id="cp1", project_id="duo-open"):
    return StageCheckpoint(
        project_id=project_id, checkpoint_id=checkpoint_id,
        cycle_id="2026-10-05T21:00:00-07:00", stage="RESEARCHER_1",
        run_id="run1", sequence=1, state=state, phase="research", trigger="SCHEDULED",
        created_at=NOW,
    )


class DualPersistenceAdversarialTests(unittest.TestCase):
    # 1
    def test_forum_succeeds_github_missing_blocks(self):
        r=record(); p=DualPersistenceReceipt("p",r.project_id,r.record_id,r.content_digest,NOW,artifactory_ack=ack(SINK_ARTIFACTORY,r))
        self.assertEqual(p.state, ARTIFACTORY_ONLY)
    # 2
    def test_github_succeeds_forum_missing_blocks(self):
        r=record(); p=DualPersistenceReceipt("p",r.project_id,r.record_id,r.content_digest,NOW,github_ack=ack(SINK_GITHUB,r))
        self.assertEqual(p.state, GITHUB_ONLY)
    # 3
    def test_crash_after_first_sink_recovers_idempotently(self):
        r=record(); i=PersistenceIndex(); self.assertEqual(i.observe(ack(SINK_ARTIFACTORY,r)),ARTIFACTORY_ONLY); self.assertEqual(i.observe(ack(SINK_ARTIFACTORY,r)),ARTIFACTORY_ONLY); self.assertEqual(i.observe(ack(SINK_GITHUB,r)),DUAL_PERSISTENCE_CONFIRMED)
    # 4
    def test_same_id_same_digest_retry_safe(self):
        r=record(); i=PersistenceIndex(); a=ack(SINK_ARTIFACTORY,r); i.observe(a); self.assertEqual(i.observe(a),ARTIFACTORY_ONLY)
    # 5
    def test_same_id_different_digest_quarantines(self):
        r=record(); i=PersistenceIndex(); i.observe(ack(SINK_ARTIFACTORY,r));
        with self.assertRaises(PersistenceConflictError): i.observe(ack(SINK_GITHUB,r,digest=DIGEST0))
    # 6
    def test_sink_digest_mismatch_receipt_quarantines(self):
        r=record(); p=DualPersistenceReceipt("p",r.project_id,r.record_id,r.content_digest,NOW,ack(SINK_ARTIFACTORY,r,digest=DIGEST0),ack(SINK_GITHUB,r)); self.assertEqual(p.state,DIGEST_MISMATCH)
    # 7
    def test_missing_namespace_denies_publication(self):
        with self.assertRaises(CoordinationPublicationError): publish(route=route(None))
    # 8
    def test_wrong_repository_denied(self):
        with self.assertRaises(ProjectScopeError): publish(target_repository="boberino93-bit/benefitflow")
    # 9
    def test_cross_project_ack_cannot_confirm(self):
        r=record(); p=DualPersistenceReceipt("p",r.project_id,r.record_id,r.content_digest,NOW,ack(SINK_ARTIFACTORY,r),ack(SINK_GITHUB,r,project_id="benefitflow")); self.assertEqual(p.state,DIGEST_MISMATCH)
    # 10
    def test_ineligible_role_denied(self):
        with self.assertRaises(CoordinationPublicationError): publish(actor_role="MASTER")
    # 11
    def test_missing_capability_denied(self):
        with self.assertRaises(CoordinationPublicationError): publish(actor_capabilities=[])
    # 12
    def test_authority_smuggling_denied(self):
        with self.assertRaises(CoordinationPublicationError): publish(authority_conveyed=True)
    # 13
    def test_overwrite_denied(self):
        with self.assertRaises(CoordinationPublicationError): publish(operation="OVERWRITE")
    # 14
    def test_delete_denied(self):
        with self.assertRaises(CoordinationPublicationError): publish(operation="DELETE")
    # 15
    def test_path_traversal_denied(self):
        with self.assertRaises(CoordinationPublicationError): publish(github_backup_path="agentbus-backup/coordination-messages/../x")
    # 16
    def test_secret_field_rejected_before_hash(self):
        with self.assertRaises(Exception): MaterialWorkRecord(record_id="r",project_id="duo-open",run_id="run",agent_id="a",role="RESEARCH",work_id="w",event_type="F",sequence=0,created_at=NOW,summary="x",payload={"ephemeral_value":"secret"})
    # 17
    def test_secret_label_rejected_before_hash(self):
        with self.assertRaises(Exception): MaterialWorkRecord(record_id="r",project_id="duo-open",run_id="run",agent_id="a",role="RESEARCH",work_id="w",event_type="F",sequence=0,created_at=NOW,summary="Security-Token: abc",payload={})
    # 18
    def test_hash_chain_break_detected(self):
        a=record("a"); b=record("b",previous=DIGEST0)
        with self.assertRaises(DualPersistenceError): validate_hash_chain([a,b])
    # 19
    def test_cross_project_hash_chain_denied(self):
        a=record("a"); b=record("b",project_id="benefitflow",previous=a.content_digest)
        with self.assertRaises(DualPersistenceError): validate_hash_chain([a,b])
    # 20
    def test_correction_is_new_record_not_self_supersession(self):
        with self.assertRaises(DualPersistenceError): record("r1",supersedes="r1")
    # 21
    def test_ready_without_receipt_denied(self):
        with self.assertRaises(PersistenceBarrierError): require_work_state_barrier("READY",record=record(),receipt=None)
    # 22
    def test_complete_with_unrelated_receipt_denied(self):
        r=record(); other=record("other")
        with self.assertRaises(PersistenceBarrierError): require_work_state_barrier("COMPLETE",record=r,receipt=confirmed(other))
    # 23
    def test_complete_with_dual_bound_receipt_allowed(self):
        r=record(); self.assertTrue(require_work_state_barrier("COMPLETE",record=r,receipt=confirmed(r)))
    # 24
    def test_progress_state_does_not_require_terminal_barrier(self):
        self.assertTrue(require_work_state_barrier("IN_PROGRESS"))
    # 25
    def test_checkpoint_ready_without_dual_receipt_denied(self):
        cp=checkpoint(); d=checkpoint_digest(cp); r=DualPersistenceReceipt("p",cp.project_id,cp.checkpoint_id,d,NOW,artifactory_ack=SinkAck(SINK_ARTIFACTORY,cp.project_id,cp.checkpoint_id,d,"/f",NOW))
        item=PersistedCheckpoint(cp,r)
        with self.assertRaises(CheckpointPersistenceError): item.require_ready()
    # 26
    def test_checkpoint_wrong_digest_denied(self):
        cp=checkpoint();
        with self.assertRaises(CheckpointPersistenceError): PersistedCheckpoint(cp,DualPersistenceReceipt("p",cp.project_id,cp.checkpoint_id,DIGEST0,NOW))
    # 27
    def test_checkpoint_wrong_project_denied(self):
        cp=checkpoint(); d=checkpoint_digest(cp)
        with self.assertRaises(CheckpointPersistenceError): PersistedCheckpoint(cp,DualPersistenceReceipt("p","benefitflow",cp.checkpoint_id,d,NOW))
    # 28
    def test_latest_checkpoint_ignores_degraded_candidate(self):
        cp=checkpoint(); d=checkpoint_digest(cp); p=DualPersistenceReceipt("p",cp.project_id,cp.checkpoint_id,d,NOW,artifactory_ack=SinkAck(SINK_ARTIFACTORY,cp.project_id,cp.checkpoint_id,d,"/f",NOW)); self.assertIsNone(latest_persisted_ready_for_cycle([PersistedCheckpoint(cp,p)],project_id=cp.project_id,cycle_id=cp.cycle_id,stage=cp.stage))
    # 29
    def test_reconciler_forum_only_visible(self):
        f=reconcile_digest_views(project_id="duo-open",artifactory_records={"r":DIGEST0},github_records={}); self.assertEqual(f[0].state,ARTIFACTORY_ONLY)
    # 30
    def test_reconciler_github_only_visible(self):
        f=reconcile_digest_views(project_id="duo-open",artifactory_records={},github_records={"r":DIGEST0}); self.assertEqual(f[0].state,GITHUB_ONLY)
    # 31
    def test_reconciler_mismatch_visible(self):
        f=reconcile_digest_views(project_id="duo-open",artifactory_records={"r":DIGEST0},github_records={"r":DIGEST1}); self.assertEqual(f[0].state,DIGEST_MISMATCH)
    # 32
    def test_health_zero_loss_requires_verified_route_and_sinks(self):
        h=build_persistence_health(project_id="duo-open",reconciled_at_utc=NOW,artifactory_records={"r":DIGEST0},github_records={"r":DIGEST0},route_normalized=False,forum_verified=True,github_backup_verified=True,conflict_record_ids=["conflict-r"]); self.assertFalse(h["zero_loss"]); self.assertEqual(h["conflict_count"],1)
    # 33
    def test_stage15_rejects_degraded_persistence(self):
        h=build_persistence_health(project_id="duo-open",reconciled_at_utc=NOW,artifactory_records={"r":DIGEST0},github_records={},route_normalized=True,forum_verified=True,github_backup_verified=True)
        with self.assertRaises(Stage15PreflightError): validate_persistence_health(h,expected_project_id="duo-open",now_utc=NOW)
    # 34
    def test_stage15_rejects_unnormalized_route(self):
        h=build_persistence_health(project_id="duo-open",reconciled_at_utc=NOW,artifactory_records={},github_records={},route_normalized=False,forum_verified=True,github_backup_verified=True)
        with self.assertRaises(Stage15PreflightError): validate_persistence_health(h,expected_project_id="duo-open",now_utc=NOW)
    # 35
    def test_persistence_never_conveys_authority(self):
        r=record()
        with self.assertRaises(DualPersistenceError): DualPersistenceReceipt("p",r.project_id,r.record_id,r.content_digest,NOW,authority_conveyed=True)


if __name__ == "__main__":
    unittest.main()
