from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.self_enhancement import (
    ImprovementSignal,
    PeerObservationError,
    RecursiveEnhancementEngine,
)


class FakePeer:
    def __init__(self, repository_identity, files, revision="abc123"):
        self._repository_identity = repository_identity
        self._files = dict(files)
        self._revision = revision
        self.reads = []

    @property
    def repository_identity(self):
        return self._repository_identity

    def revision(self):
        return self._revision

    def list_paths(self):
        return self._files.keys()

    def read_text(self, path):
        self.reads.append(path)
        return self._files[path]


class EnhancementTest(unittest.TestCase):
    def test_peer_is_read_only_and_candidate_writes_stay_local(self):
        with TemporaryDirectory() as temp:
            peer = FakePeer(
                "peer/project",
                {
                    "artifactory/CONTROL.md": "accepted state and succession",
                    "artifactory/DETAIL.md": "checksum and review contract",
                },
            )
            engine = RecursiveEnhancementEngine(
                local_project_root=temp,
                local_repository_identity="local/project",
                max_depth=1,
            )

            def analyze(snapshot):
                if snapshot.path.endswith("CONTROL.md"):
                    return [
                        ImprovementSignal(
                            title="Succession checkpoint",
                            pattern="controller succession with revalidation",
                            rationale="Improves recovery without autonomous authority transfer.",
                            expected_benefit="Safer primary handoff",
                            risk="LOW",
                            suggested_targets=("bootstrap/PRIMARY.md",),
                            follow_up_paths=("artifactory/DETAIL.md",),
                        )
                    ]
                return []

            result = engine.run_cycle([peer], analyze)
            self.assertEqual(1, len(result))
            candidate_path = (
                Path(temp)
                / ".interagent/self_enhancement/candidates"
                / f"{result[0].candidate_id}.json"
            )
            self.assertTrue(candidate_path.is_file())
            payload = json.loads(candidate_path.read_text())
            self.assertEqual("peer/project", payload["source"]["repository"])
            self.assertEqual(["artifactory/CONTROL.md", "artifactory/DETAIL.md"], peer.reads)

    def test_local_repository_cannot_be_registered_as_peer(self):
        with TemporaryDirectory() as temp:
            peer = FakePeer("local/project", {"x.md": "data"})
            engine = RecursiveEnhancementEngine(
                local_project_root=temp,
                local_repository_identity="local/project",
            )
            with self.assertRaises(PeerObservationError):
                engine.run_cycle([peer], lambda snapshot: [])

    def test_peer_traversal_path_rejected(self):
        with TemporaryDirectory() as temp:
            peer = FakePeer("peer/project", {"../secret": "nope"})
            engine = RecursiveEnhancementEngine(
                local_project_root=temp,
                local_repository_identity="local/project",
            )
            with self.assertRaises(PeerObservationError):
                engine.run_cycle([peer], lambda snapshot: [])

    def test_candidate_collision_does_not_overwrite(self):
        with TemporaryDirectory() as temp:
            peer = FakePeer("peer/project", {"a.md": "same"})
            engine = RecursiveEnhancementEngine(
                local_project_root=temp,
                local_repository_identity="local/project",
            )
            signal = ImprovementSignal(
                title="A",
                pattern="P",
                rationale="R",
                expected_benefit="B",
                suggested_targets=("x",),
            )
            first = engine.run_cycle([peer], lambda snapshot: [signal])
            second = engine.run_cycle([peer], lambda snapshot: [signal])
            self.assertEqual(first[0].candidate_id, second[0].candidate_id)


if __name__ == "__main__":
    unittest.main()
