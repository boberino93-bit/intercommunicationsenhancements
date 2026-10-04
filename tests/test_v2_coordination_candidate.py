from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.constants import PROTOCOL_VERSION
from org_agent_mesh.control_plane import AgentSession, StaleVersion
from org_agent_mesh.dependencies import DependencyCycleError, DependencyRegistry, RendezvousRegistry
from org_agent_mesh.durable_backend import SQLiteRecordBackend
from org_agent_mesh.ecosystem_coordination import (
    compare_coordinator_claims,
    validate_sanitized_project_summary,
)
from org_agent_mesh.generation import GenerationRegistry, StaleGeneration
from org_agent_mesh.project_scope import ProjectBinding, ProjectScopeError


PROJECT = "candidate-v2"
REPO = "owner/candidate-v2"
CAPS = ("WRITE_ACCEPTED_STATE", "CLAIM_TASK")


def active_session(agent="primary", instance="primary-1", project=PROJECT):
    binding = ProjectBinding(
        project,
        REPO if project == PROJECT else f"owner/{project}",
        f"/work/{project}",
        agent,
        instance,
        PROTOCOL_VERSION,
        CAPS,
    )
    return AgentSession(agent).bind(binding).initialize().activate()


def init_generation(registry, session=None):
    return registry.initialize(
        session or active_session(),
        PROJECT,
        "gen-1",
        coordinator_epoch="epoch-1",
        protocol_version=PROTOCOL_VERSION,
        package_version="1.6.0-alpha.1",
        reason="candidate test",
    )


class CandidateV2CoordinationTests(unittest.TestCase):
    def backend(self, directory):
        return SQLiteRecordBackend(Path(directory) / "mesh.sqlite3")

    def test_generation_transition_fences_stale_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = GenerationRegistry(self.backend(directory))
            first = init_generation(registry)
            second = registry.advance(
                active_session(),
                PROJECT,
                "gen-2",
                expected_version=first.version,
                coordinator_epoch="epoch-1",
                protocol_version=PROTOCOL_VERSION,
                package_version="1.6.0-alpha.1",
                reason="integration boundary",
            )
            self.assertEqual("gen-2", second.payload["generation_id"])
            self.assertEqual("gen-1", second.payload["parent_generation_id"])
            self.assertEqual("SUPERSEDED", second.payload["history"][0]["status"])
            with self.assertRaises(StaleGeneration):
                registry.assert_current(PROJECT, "gen-1")

    def test_concurrent_generation_advance_has_one_cas_winner(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = GenerationRegistry(self.backend(directory))
            first = init_generation(registry)

            def attempt(index):
                try:
                    return registry.advance(
                        active_session(f"primary-{index}", f"instance-{index}"),
                        PROJECT,
                        f"gen-{index + 2}",
                        expected_version=first.version,
                        coordinator_epoch="epoch-1",
                        protocol_version=PROTOCOL_VERSION,
                        package_version="1.6.0-alpha.1",
                        reason="concurrent transition",
                    ).payload["generation_id"]
                except StaleVersion:
                    return None

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(attempt, range(2)))
            self.assertEqual(1, len([value for value in results if value is not None]))

    def test_stale_generation_cannot_create_dependency(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = self.backend(directory)
            generations = GenerationRegistry(backend)
            first = init_generation(generations)
            generations.advance(
                active_session(),
                PROJECT,
                "gen-2",
                expected_version=first.version,
                coordinator_epoch="epoch-1",
                protocol_version=PROTOCOL_VERSION,
                package_version="1.6.0-alpha.1",
                reason="advance",
            )
            dependencies = DependencyRegistry(backend, generation_registry=generations)
            with self.assertRaises(StaleGeneration):
                dependencies.create(
                    active_session(),
                    PROJECT,
                    "dep-stale",
                    generation_id="gen-1",
                    producer_task_or_node="producer",
                    consumer_task_or_node="consumer",
                    required_output="artifact",
                )

    def test_dependency_cycle_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = self.backend(directory)
            generations = GenerationRegistry(backend)
            init_generation(generations)
            dependencies = DependencyRegistry(backend, generation_registry=generations)
            session = active_session()
            dependencies.create(session, PROJECT, "dep-ab", generation_id="gen-1", producer_task_or_node="a", consumer_task_or_node="b", required_output="ab")
            dependencies.create(session, PROJECT, "dep-bc", generation_id="gen-1", producer_task_or_node="b", consumer_task_or_node="c", required_output="bc")
            with self.assertRaises(DependencyCycleError):
                dependencies.create(session, PROJECT, "dep-ca", generation_id="gen-1", producer_task_or_node="c", consumer_task_or_node="a", required_output="ca")

    def test_rendezvous_requires_all_required_nodes(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = self.backend(directory)
            generations = GenerationRegistry(backend)
            init_generation(generations)
            rendezvous = RendezvousRegistry(backend, generation_registry=generations)
            session = active_session()
            start = datetime(2026, 10, 4, 16, 0, tzinfo=timezone.utc)
            record = rendezvous.create(
                session,
                PROJECT,
                "rv-1",
                generation_id="gen-1",
                required_nodes=("node-a", "node-b"),
                consumer="primary",
                timeout_at_utc=(start + timedelta(hours=1)).isoformat(),
                now=start,
            )
            one = rendezvous.record_arrival(session, PROJECT, "rv-1", expected_version=record.version, node_id="node-a", evidence_ref="evidence-a", now=start + timedelta(minutes=1))
            self.assertEqual("OPEN", one.payload["status"])
            two = rendezvous.record_arrival(session, PROJECT, "rv-1", expected_version=one.version, node_id="node-b", evidence_ref="evidence-b", now=start + timedelta(minutes=2))
            self.assertEqual("COMPLETED", two.payload["status"])

    def test_rendezvous_timeout_preserves_missing_required_nodes(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = self.backend(directory)
            generations = GenerationRegistry(backend)
            init_generation(generations)
            rendezvous = RendezvousRegistry(backend, generation_registry=generations)
            session = active_session()
            start = datetime(2026, 10, 4, 16, 0, tzinfo=timezone.utc)
            record = rendezvous.create(
                session,
                PROJECT,
                "rv-timeout",
                generation_id="gen-1",
                required_nodes=("node-a", "node-b"),
                consumer="primary",
                timeout_at_utc=(start + timedelta(minutes=5)).isoformat(),
                now=start,
            )
            timed_out = rendezvous.timeout(session, PROJECT, "rv-timeout", expected_version=record.version, now=start + timedelta(minutes=6))
            self.assertEqual("TIMED_OUT", timed_out.payload["status"])
            self.assertEqual(["node-a", "node-b"], timed_out.payload["missing_required_nodes"])

    def test_twelve_parallel_bounded_dependency_creations(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = self.backend(directory)
            generations = GenerationRegistry(backend)
            init_generation(generations)
            dependencies = DependencyRegistry(backend, generation_registry=generations)

            def create_one(index):
                session = active_session(f"worker-{index}", f"worker-instance-{index}")
                return dependencies.create(
                    session,
                    PROJECT,
                    f"dep-{index}",
                    generation_id="gen-1",
                    producer_task_or_node=f"producer-{index}",
                    consumer_task_or_node=f"consumer-{index}",
                    required_output=f"artifact-{index}",
                ).resource_id

            with ThreadPoolExecutor(max_workers=12) as pool:
                results = list(pool.map(create_one, range(12)))
            self.assertEqual(12, len(set(results)))
            self.assertEqual(12, len(backend.list_records("dependencies", project_id=PROJECT)))

    def test_duplicate_coordinator_epoch_freezes_global_mutation(self):
        base = {
            "coordinator_agent_id": "primary-a",
            "coordinator_project_id": "project-a",
            "epoch_id": "epoch-7",
            "scope": "ECOSYSTEM_SCOPE",
            "allowed_reads": ["sanitized-registry"],
            "allowed_writes": [],
            "prohibited_actions": ["peer-project-mutation"],
            "start_time": "2026-10-04T16:00:00Z",
            "expiry_or_review_condition": "human review",
            "human_assignment_ref": "human-20261004",
        }
        other = dict(base, coordinator_agent_id="primary-b", coordinator_project_id="project-b")
        result = compare_coordinator_claims(base, other)
        self.assertEqual("SPLIT_BRAIN_DETECTED", result["state"])
        self.assertTrue(result["freeze_global_mutations"])
        self.assertIsNone(result["authoritative_claim"])

    def test_sanitized_ecosystem_summary_rejects_extra_payload(self):
        summary = {
            "project_id": "project-a",
            "project_name": "Project A",
            "purpose": "test",
            "status": "ACTIVE",
            "repository_identity": "owner/project-a",
            "canonical_branch": "main",
            "board_root": "/Project A/AgentBus",
            "protocol_version": PROTOCOL_VERSION,
            "package_version": "1.6.0-alpha.1",
            "capacity_state": "SAFE",
            "backup_state": "VERIFIED",
            "recovery_state": "VERIFIED",
            "allowed_cross_project_links": [],
            "last_verified": "2026-10-04T16:00:00Z",
            "secret": "must-not-cross-boundary",
        }
        with self.assertRaises(ProjectScopeError):
            validate_sanitized_project_summary(summary)

    def test_foreign_project_session_cannot_create_dependency(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = self.backend(directory)
            dependencies = DependencyRegistry(backend)
            with self.assertRaises(ProjectScopeError):
                dependencies.create(
                    active_session(project="other-project"),
                    PROJECT,
                    "dep-foreign",
                    generation_id="gen-1",
                    producer_task_or_node="a",
                    consumer_task_or_node="b",
                    required_output="artifact",
                )


if __name__ == "__main__":
    unittest.main()
