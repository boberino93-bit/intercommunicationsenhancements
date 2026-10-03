from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Callable, Iterable, Protocol, Sequence
import json
import os
import tempfile
import time

from .project_scope import ProjectScopeError, require_project_path


class PeerObservationError(ValueError):
    """Raised when a peer observation violates the read-only observation contract."""


def _safe_peer_path(path: str) -> str:
    if not isinstance(path, str) or not path.strip():
        raise PeerObservationError("peer artifact path is required")
    normalized = path.replace("\\", "/").strip()
    candidate = PurePosixPath(normalized)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise PeerObservationError("peer artifact path must be relative and traversal-free")
    return candidate.as_posix()


def _digest_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PeerSnapshot:
    repository_identity: str
    revision: str
    path: str
    content: str

    def __post_init__(self):
        if not self.repository_identity or not self.revision:
            raise PeerObservationError("repository_identity and revision are required")
        object.__setattr__(self, "path", _safe_peer_path(self.path))

    @property
    def content_sha256(self) -> str:
        return _digest_text(self.content)


@dataclass(frozen=True)
class ImprovementSignal:
    title: str
    pattern: str
    rationale: str
    suggested_targets: Sequence[str]
    expected_benefit: str
    risk: str = "MEDIUM"
    follow_up_paths: Sequence[str] = ()

    def __post_init__(self):
        if not self.title or not self.pattern or not self.rationale:
            raise ValueError("title, pattern, and rationale are required")
        object.__setattr__(
            self,
            "follow_up_paths",
            tuple(_safe_peer_path(path) for path in self.follow_up_paths),
        )
        object.__setattr__(self, "suggested_targets", tuple(self.suggested_targets))


class ReadOnlyPeerAdapter(Protocol):
    """Peer adapter surface intentionally exposes no mutation operations."""

    @property
    def repository_identity(self) -> str: ...

    def revision(self) -> str: ...

    def list_paths(self) -> Iterable[str]: ...

    def read_text(self, path: str) -> str: ...


@dataclass(frozen=True)
class EnhancementCandidate:
    candidate_id: str
    source_repository: str
    source_revision: str
    source_path: str
    source_sha256: str
    title: str
    pattern: str
    rationale: str
    expected_benefit: str
    risk: str
    suggested_targets: Sequence[str]
    depth: int
    parent_candidate_id: str | None
    status: str = "DISCOVERED"

    def as_dict(self) -> dict:
        return {
            "schema": "org-agent-mesh/enhancement-candidate/v1",
            "candidate_id": self.candidate_id,
            "source": {
                "repository": self.source_repository,
                "revision": self.source_revision,
                "path": self.source_path,
                "sha256": self.source_sha256,
            },
            "title": self.title,
            "pattern": self.pattern,
            "rationale": self.rationale,
            "expected_benefit": self.expected_benefit,
            "risk": self.risk,
            "suggested_targets": list(self.suggested_targets),
            "depth": self.depth,
            "parent_candidate_id": self.parent_candidate_id,
            "status": self.status,
        }


class RecursiveEnhancementEngine:
    """
    Bounded read-only peer discovery with local-only candidate persistence.

    The engine never receives a peer write callback. Its only filesystem writes
    are constrained beneath local_state_root inside the bound local project.
    """

    def __init__(
        self,
        *,
        local_project_root,
        local_repository_identity: str,
        local_state_root=".interagent/self_enhancement",
        max_depth: int = 2,
        max_candidates_per_cycle: int = 64,
        max_artifacts_per_peer: int = 256,
    ):
        if max_depth < 0 or max_candidates_per_cycle < 1 or max_artifacts_per_peer < 1:
            raise ValueError("invalid self-enhancement bounds")
        self.local_project_root = Path(local_project_root).resolve()
        self.local_repository_identity = local_repository_identity
        self.local_state_root = require_project_path(
            self.local_project_root, self.local_project_root / local_state_root
        )
        self.max_depth = max_depth
        self.max_candidates_per_cycle = max_candidates_per_cycle
        self.max_artifacts_per_peer = max_artifacts_per_peer

    def _assert_peer(self, repository_identity: str):
        if not repository_identity:
            raise PeerObservationError("peer repository identity is required")
        if repository_identity == self.local_repository_identity:
            raise PeerObservationError("peer observation must target a different repository")

    def _candidate_for(
        self,
        snapshot: PeerSnapshot,
        signal: ImprovementSignal,
        *,
        depth: int,
        parent_candidate_id: str | None,
    ) -> EnhancementCandidate:
        identity = "\n".join(
            [
                snapshot.repository_identity,
                snapshot.revision,
                snapshot.path,
                snapshot.content_sha256,
                signal.pattern,
                "|".join(sorted(signal.suggested_targets)),
            ]
        )
        candidate_id = sha256(identity.encode("utf-8")).hexdigest()[:24]
        return EnhancementCandidate(
            candidate_id=candidate_id,
            source_repository=snapshot.repository_identity,
            source_revision=snapshot.revision,
            source_path=snapshot.path,
            source_sha256=snapshot.content_sha256,
            title=signal.title,
            pattern=signal.pattern,
            rationale=signal.rationale,
            expected_benefit=signal.expected_benefit,
            risk=signal.risk.upper(),
            suggested_targets=tuple(signal.suggested_targets),
            depth=depth,
            parent_candidate_id=parent_candidate_id,
        )

    def _persist_candidate(self, candidate: EnhancementCandidate) -> Path:
        candidate_dir = require_project_path(
            self.local_project_root, self.local_state_root / "candidates"
        )
        candidate_dir.mkdir(parents=True, exist_ok=True)
        path = require_project_path(
            self.local_project_root, candidate_dir / f"{candidate.candidate_id}.json"
        )
        payload = json.dumps(candidate.as_dict(), indent=2, sort_keys=True) + "\n"
        if path.exists():
            existing = path.read_text(encoding="utf-8")
            if existing != payload:
                raise ProjectScopeError(
                    f"candidate collision for {candidate.candidate_id}; refusing overwrite"
                )
            return path
        fd, temp_name = tempfile.mkstemp(prefix=".candidate-", suffix=".tmp", dir=candidate_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
        return path

    def _persist_cycle(self, records: Sequence[dict]) -> Path:
        cycle_dir = require_project_path(
            self.local_project_root, self.local_state_root / "cycles"
        )
        cycle_dir.mkdir(parents=True, exist_ok=True)
        seed = json.dumps(records, sort_keys=True) + str(time.time_ns())
        cycle_id = sha256(seed.encode("utf-8")).hexdigest()[:20]
        path = require_project_path(
            self.local_project_root, cycle_dir / f"{cycle_id}.json"
        )
        payload = {
            "schema": "org-agent-mesh/enhancement-cycle/v1",
            "cycle_id": cycle_id,
            "candidate_count": len(records),
            "candidates": records,
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def run_cycle(
        self,
        peers: Sequence[ReadOnlyPeerAdapter],
        analyze: Callable[[PeerSnapshot], Sequence[ImprovementSignal]],
    ) -> list[EnhancementCandidate]:
        queue: list[tuple[ReadOnlyPeerAdapter, str, int, str | None]] = []
        revision_by_repo: dict[str, str] = {}
        for peer in peers:
            self._assert_peer(peer.repository_identity)
            revision = peer.revision()
            if not revision:
                raise PeerObservationError("peer revision is required")
            revision_by_repo[peer.repository_identity] = revision
            paths = sorted({_safe_peer_path(path) for path in peer.list_paths()})
            for path in paths[: self.max_artifacts_per_peer]:
                queue.append((peer, path, 0, None))

        candidates: list[EnhancementCandidate] = []
        visited: set[tuple[str, str, str]] = set()
        while queue and len(candidates) < self.max_candidates_per_cycle:
            peer, path, depth, parent_candidate_id = queue.pop(0)
            revision = revision_by_repo[peer.repository_identity]
            key = (peer.repository_identity, revision, path)
            if key in visited or depth > self.max_depth:
                continue
            visited.add(key)
            snapshot = PeerSnapshot(
                repository_identity=peer.repository_identity,
                revision=revision,
                path=path,
                content=peer.read_text(path),
            )
            for signal in analyze(snapshot):
                if len(candidates) >= self.max_candidates_per_cycle:
                    break
                candidate = self._candidate_for(
                    snapshot,
                    signal,
                    depth=depth,
                    parent_candidate_id=parent_candidate_id,
                )
                self._persist_candidate(candidate)
                candidates.append(candidate)
                if depth < self.max_depth:
                    for follow_up in signal.follow_up_paths:
                        queue.append((peer, follow_up, depth + 1, candidate.candidate_id))

        self.local_state_root.mkdir(parents=True, exist_ok=True)
        self._persist_cycle([candidate.as_dict() for candidate in candidates])
        return candidates
