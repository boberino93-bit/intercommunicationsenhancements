from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.constants import PROTOCOL_VERSION
from org_agent_mesh.control_plane import AgentSession
from org_agent_mesh.dependencies import DependencyRegistry
from org_agent_mesh.durable_backend import SQLiteRecordBackend
from org_agent_mesh.generation import GenerationRegistry, StaleGeneration
from org_agent_mesh.generation_state import GenerationStateStore
from org_agent_mesh.project_scope import ProjectBinding


PROJECT = "candidate-v2"
CAPS = ("WRITE_ACCEPTED_STATE", "CLAIM_TASK")


def session():
    binding = ProjectBinding(
        PROJECT,
        "owner/candidate-v2",
        "/work/candidate-v2",
        "primary",
        "primary-1",
        PROTOCOL_VERSION,
        CAPS,
    )
    return AgentSession("primary").bind(binding).initialize().activate()


def initialize_generation(registry):
    return registry.initialize(
        session(),
        PROJECT,
        "gen-1",
        coordinator_epoch="epoch-1",
        protocol_version=PROTOCOL_VERSION,
        package_version="1.6.0-alpha.1",
        reason="candidate test",
    )


class CandidateV2GenerationStateTests(unittest.TestCase):
    def backend(self, directory):
        return SQLiteRecordBackend(Path(directory) / "mesh.sqlite3")

    def test_old_generation_state_never_becomes_current_after_advance(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = self.backend(directory)
            generations = GenerationRegistry(backend)
            first_generation = initialize_generation(generations)
            state = GenerationStateStore(backend, generations)
            old = state.initialize(session(), PROJECT, "gen-1", "architecture", {"value": 1})
            self.assertEqual({"value": 1}, state.read_current(PROJECT, "architecture").payload["value"])

            generations.advance(
                session(),
                PROJECT,
                "gen-2",
                expected_version=first_generation.version,
                coordinator_epoch="epoch-1",
                protocol_version=PROTOCOL_VERSION,
                package_version="1.6.0-alpha.1",
                reason="new integration boundary",
            )
            self.assertIsNone(state.read_current(PROJECT, "architecture"))
            self.assertEqual(
                {"value": 1},
                state.read_generation(PROJECT, "gen-1", "architecture").payload["value"],
            )
            with self.assertRaises(StaleGeneration):
                state.compare_and_set(
                    session(),
                    PROJECT,
                    "gen-1",
                    "architecture",
                    expected_version=old.version,
                    value={"value": 2},
                )

    def test_new_generation_state_is_isolated_from_old_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = self.backend(directory)
            generations = GenerationRegistry(backend)
            first_generation = initialize_generation(generations)
            state = GenerationStateStore(backend, generations)
            state.initialize(session(), PROJECT, "gen-1", "architecture", "old")
            generations.advance(
                session(),
                PROJECT,
                "gen-2",
                expected_version=first_generation.version,
                coordinator_epoch="epoch-1",
                protocol_version=PROTOCOL_VERSION,
                package_version="1.6.0-alpha.1",
                reason="new integration boundary",
            )
            state.initialize(session(), PROJECT, "gen-2", "architecture", "new")
            self.assertEqual("new", state.read_current(PROJECT, "architecture").payload["value"])
            self.assertEqual("old", state.read_generation(PROJECT, "gen-1", "architecture").payload["value"])

    def test_dependency_cycle_analysis_does_not_cross_generations(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = self.backend(directory)
            generations = GenerationRegistry(backend)
            first_generation = initialize_generation(generations)
            dependencies = DependencyRegistry(backend, generation_registry=generations)
            dependencies.create(
                session(),
                PROJECT,
                "dep-old",
                generation_id="gen-1",
                producer_task_or_node="a",
                consumer_task_or_node="b",
                required_output="old edge",
            )
            generations.advance(
                session(),
                PROJECT,
                "gen-2",
                expected_version=first_generation.version,
                coordinator_epoch="epoch-1",
                protocol_version=PROTOCOL_VERSION,
                package_version="1.6.0-alpha.1",
                reason="new integration boundary",
            )
            fresh = dependencies.create(
                session(),
                PROJECT,
                "dep-new",
                generation_id="gen-2",
                producer_task_or_node="b",
                consumer_task_or_node="a",
                required_output="new edge",
            )
            self.assertEqual("gen-2", fresh.payload["generation_id"])


if __name__ == "__main__":
    unittest.main()
