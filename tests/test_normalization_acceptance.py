from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import tempfile
import unittest

from org_agent_mesh.constants import PROTOCOL_VERSION
from org_agent_mesh.capsules import StateCapsuleRegistry, validate_swarm_capsule
from org_agent_mesh.containment import ContainmentStateError, ProjectHealthRegistry
from org_agent_mesh.continuity import ContinuityStateError, OperationalCheckpointRegistry
from org_agent_mesh.control_plane import AgentSession, LeaseConflict
from org_agent_mesh.dependencies import DependencyRegistry
from org_agent_mesh.durable_backend import SQLiteRecordBackend
from org_agent_mesh.durable_state import DurableLeaseRegistry
from org_agent_mesh.ecosystem_coordination import SanitizedEcosystemRegistry, assert_summary_promotable, compare_coordinator_claims
from org_agent_mesh.evaluation import ScenarioEvidence, assert_anti_goodhart, passive_intelligence_baseline
from org_agent_mesh.generation import GenerationRegistry, StaleGeneration
from org_agent_mesh.project_scope import ProjectBinding, ProjectScopeError
from org_agent_mesh.scheduled_tasks import ScheduledTaskRoute
from org_agent_mesh.thematic_routing import ThematicRouteRegistry

PROJECT = "intercommunicationsenhancements"
REPO = "boberino93-bit/intercommunicationsenhancements"
CAPS = ("WRITE_ACCEPTED_STATE", "CLAIM_TASK")


def session(agent="primary", instance="primary-1", project=PROJECT):
    return AgentSession(agent).bind(ProjectBinding(
        project_id=project,
        repository_identity=REPO if project == PROJECT else f"boberino93-bit/{project}",
        project_root=f"/work/{project}",
        agent_id=agent,
        agent_instance_id=instance,
        protocol_version=PROTOCOL_VERSION,
        capabilities=CAPS,
    )).initialize().activate()


class NormalizationAcceptanceTests(unittest.TestCase):
    def backend(self, d):
        return SQLiteRecordBackend(Path(d) / "mesh.sqlite3")

    def test_controlled_debugging_active_owner_then_expiry(self):
        with tempfile.TemporaryDirectory() as d:
            backend = self.backend(d)
            leases = DurableLeaseRegistry(backend)
            now = datetime(2026, 10, 4, 20, 0, tzinfo=timezone.utc)
            owner = session("primary", "owner-1")
            other = session("manager", "manager-1")
            first = leases.claim(owner, PROJECT, "debug-resource", ttl_seconds=30, now=now)
            with self.assertRaises(LeaseConflict):
                leases.claim(other, PROJECT, "debug-resource", ttl_seconds=30, now=now + timedelta(seconds=1))
            leases.recover_expired(project_id=PROJECT, now=now + timedelta(seconds=31))
            second = leases.claim(other, PROJECT, "debug-resource", ttl_seconds=30, now=now + timedelta(seconds=32))
            self.assertNotEqual(first.lease_id, second.lease_id)

    def test_crashed_blocker_handback_and_stale_resume(self):
        with tempfile.TemporaryDirectory() as d:
            backend = self.backend(d)
            deps = DependencyRegistry(backend)
            continuity = OperationalCheckpointRegistry(backend)
            a = session("primary", "a-1")
            b = session("manager", "b-1")
            dep = deps.create(a, PROJECT, "dep-1", generation_id="gen-1", producer_task_or_node="b", consumer_task_or_node="a", required_output="artifact")
            cp = continuity.create(a, PROJECT, "cp-1", objective="ship", latest_user_request="continue", base_revision="rev-a", dependency_ids=("dep-1",), unexecuted_plan_steps=("merge", "publish"), next_action="wait")
            cp = continuity.suspend(a, PROJECT, "cp-1", expected_version=cp.version, reason="dependency")
            dep = deps.transition(b, PROJECT, "dep-1", expected_version=dep.version, status="RESOLVED", evidence_ref="artifact://done")
            cp = continuity.handback(b, PROJECT, "cp-1", expected_version=cp.version, evidence_ref="artifact://done", resolved_dependency_ids=("dep-1",), canonical_revision="rev-b")
            cp = continuity.resume(session("primary", "successor-2"), PROJECT, "cp-1", expected_version=cp.version, current_canonical_revision="rev-b", validated_dependency_ids=("dep-1",))
            self.assertTrue(cp.payload["resume"]["stale_base_detected"])
            self.assertEqual(["merge", "publish"], cp.payload["resume"]["invalidated_plan_steps"])
            self.assertEqual([], cp.payload["unexecuted_plan_steps"])

    def test_contamination_hysteresis_and_controlled_rejoin(self):
        with tempfile.TemporaryDirectory() as d:
            backend = self.backend(d)
            health = ProjectHealthRegistry(backend, required_recovery_probes=3, cooldown_seconds=60)
            s = session()
            t0 = datetime(2026, 10, 4, 20, 0, tzinfo=timezone.utc)
            rec = health.initialize(s, PROJECT, now=t0)
            rec = health.trip(s, PROJECT, expected_version=rec.version, reason="integrity", hard_stop=True, now=t0)
            with self.assertRaises(ContainmentStateError):
                health.assert_trusted_for_promotion(PROJECT)
            rec = health.begin_recovery(s, PROJECT, expected_version=rec.version, now=t0 + timedelta(seconds=1))
            for sec in (10, 20, 30):
                rec = health.record_probe(s, PROJECT, expected_version=rec.version, success=True, now=t0 + timedelta(seconds=sec))
            with self.assertRaises(ContainmentStateError):
                health.rejoin(s, PROJECT, expected_version=rec.version, now=t0 + timedelta(seconds=59))
            rec = health.rejoin(s, PROJECT, expected_version=rec.version, now=t0 + timedelta(seconds=61))
            self.assertEqual("HEALTHY", rec.payload["state"])
            self.assertTrue(health.assert_trusted_for_promotion(PROJECT))

    def test_split_brain_freezes_global_mutation(self):
        base = {"coordinator_agent_id": "a", "coordinator_project_id": PROJECT, "epoch_id": "e1", "scope": "ECOSYSTEM_SCOPE", "allowed_reads": [], "allowed_writes": [], "prohibited_actions": ["peer-project-mutation"], "start_time": "2026-10-04T20:00:00Z", "expiry_or_review_condition": "review", "human_assignment_ref": "human"}
        other = dict(base, coordinator_agent_id="b")
        result = compare_coordinator_claims(base, other)
        self.assertEqual("SPLIT_BRAIN_DETECTED", result["state"])
        self.assertTrue(result["freeze_global_mutations"])

    def test_cross_project_isolation_blocks_foreign_publication(self):
        with tempfile.TemporaryDirectory() as d:
            registry = SanitizedEcosystemRegistry(self.backend(d))
            foreign = session(project="foreign-project")
            summary = {"project_id": "benefitflow", "project_name": "BenefitFlow", "purpose": "benefits", "status": "ACTIVE", "repository_identity": "boberino93-bit/benefitflow", "canonical_branch": "main", "board_root": "/BenefitFlow-AgentBus", "protocol_version": PROTOCOL_VERSION, "package_version": "1.6.0-alpha.1", "capacity_state": "SAFE", "backup_state": "VERIFIED", "recovery_state": "VERIFIED", "allowed_cross_project_links": [], "last_verified": "2026-10-04T20:00:00Z"}
            with self.assertRaises(ProjectScopeError):
                registry.publish(foreign, PROJECT, summary, source_exchange_ref="x")

    def test_quarantined_peer_summary_cannot_be_promoted(self):
        summary = {"project_id": "benefitflow", "project_name": "BenefitFlow", "purpose": "benefits", "status": "QUARANTINED", "repository_identity": "boberino93-bit/benefitflow", "canonical_branch": "main", "board_root": "/BenefitFlow-AgentBus", "protocol_version": PROTOCOL_VERSION, "package_version": "1.6.0-alpha.1", "capacity_state": "QUARANTINED", "backup_state": "VERIFIED", "recovery_state": "RECOVERING", "allowed_cross_project_links": [], "last_verified": "2026-10-04T20:00:00Z"}
        with self.assertRaises(ProjectScopeError):
            assert_summary_promotable(summary)

    def test_recursive_generation_rejects_stale_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            backend = self.backend(d)
            generations = GenerationRegistry(backend)
            s = session()
            g1 = generations.initialize(s, PROJECT, "gen-1", coordinator_epoch="e1", protocol_version=PROTOCOL_VERSION, package_version="1.6.0-alpha.1", reason="start")
            generations.advance(s, PROJECT, "gen-2", expected_version=g1.version, coordinator_epoch="e1", protocol_version=PROTOCOL_VERSION, package_version="1.6.0-alpha.1", reason="advance")
            deps = DependencyRegistry(backend, generation_registry=generations)
            with self.assertRaises(StaleGeneration):
                deps.create(s, PROJECT, "stale-dep", generation_id="gen-1", producer_task_or_node="x", consumer_task_or_node="y", required_output="z")

    def test_passive_baseline_and_anti_goodhart(self):
        baseline = passive_intelligence_baseline([
            ScenarioEvidence("canary", True, True, 0, duplicate_work_avoided=1, recoveries_completed=1, raw_messages=100, raw_agent_steps=200),
            ScenarioEvidence("recovery", True, True, 0, recoveries_completed=1, raw_messages=5, raw_agent_steps=9),
        ])
        self.assertTrue(assert_anti_goodhart(baseline))
        self.assertEqual(0, baseline["user_intervention_index"])
        self.assertFalse(baseline["activity_metrics_are_authority"])

    def test_cold_start_and_scheduled_context_from_contract(self):
        contract = json.loads(Path("AGENT_BOOTSTRAP.json").read_text())
        route = ScheduledTaskRoute.from_project_contract(contract, task_id="normalization-canary", role_id="primary")
        ctx = route.build_launch_context(occurrence_id="occ-1")
        self.assertTrue(ctx.assert_matches_project_contract(contract))
        self.assertEqual(PROJECT, ctx.project_id)

    def test_project_and_swarm_capsules_reconstruct_shared_state(self):
        with tempfile.TemporaryDirectory() as d:
            backend = self.backend(d)
            reg = StateCapsuleRegistry(backend)
            s = session()
            t0 = "2026-10-04T20:00:00Z"
            project = {"project_id": PROJECT, "repository_identity": REPO, "repository_revision": "rev-1", "protocol_version": PROTOCOL_VERSION, "package_version": "1.6.0-alpha.1", "health_state": "HEALTHY", "generation_id": "gen-1", "active_objective_id": "obj-1", "active_claims": ["claim-1"], "open_dependencies": ["dep-1"], "blocked_tasks": [], "last_checkpoint_ref": "cp-1", "updated_at_utc": t0}
            reg.publish_project(s, PROJECT, project)
            self.assertEqual("rev-1", reg.read_project(PROJECT).payload["repository_revision"])
            swarm = {"swarm_id": "swarm-1", "coordinator_epoch": "epoch-1", "protocol_version": PROTOCOL_VERSION, "project_capsules": [project], "quarantined_projects": [], "global_freeze": False, "updated_at_utc": t0}
            self.assertTrue(validate_swarm_capsule(swarm))
            srec = reg.publish_swarm(s, PROJECT, swarm)
            self.assertEqual("swarm-1", srec.payload["swarm_id"])

    def test_thematic_routing_is_project_local_and_deterministic(self):
        with tempfile.TemporaryDirectory() as d:
            routes = ThematicRouteRegistry(self.backend(d))
            s = session()
            routes.publish(s, PROJECT, "security-route", themes=("security", "containment"), destination="research", priority=10)
            routes.publish(s, PROJECT, "general-route", themes=("planning",), destination="manager", priority=20)
            matches = routes.resolve(PROJECT, ("security",))
            self.assertEqual(["research"], [r.payload["destination"] for r in matches])
            self.assertEqual([], routes.resolve("foreign-project", ("security",)))

    def test_recurring_protocol_smoke_contract_exists(self):
        text = Path("protocols/primary_recurring_swarm_protocol.md").read_text()
        for phrase in ("PRIMARY RECURRING SWARM PROTOCOL", "Dependency and suspension lifecycle", "Containment and recovery", "Re-entry to full normalization", "Smoke-test criterion"):
            self.assertIn(phrase, text)

    def test_parallel_dependency_canary(self):
        with tempfile.TemporaryDirectory() as d:
            backend = self.backend(d)
            deps = DependencyRegistry(backend)
            def create(i):
                return deps.create(session(f"worker-{i}", f"worker-{i}"), PROJECT, f"dep-{i}", generation_id="g", producer_task_or_node=f"p-{i}", consumer_task_or_node=f"c-{i}", required_output="artifact").resource_id
            with ThreadPoolExecutor(max_workers=8) as pool:
                out = list(pool.map(create, range(8)))
            self.assertEqual(8, len(set(out)))


if __name__ == "__main__":
    unittest.main()
