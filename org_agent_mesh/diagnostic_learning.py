from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
import math
from typing import Iterable, Mapping

from .reliability_v18_core import digest, ensure_aware, iso, parse_iso


class DiagnosticLearningError(ValueError):
    pass


class EvidencePartition(str, Enum):
    TRAIN = "TRAIN"
    HOLDOUT = "HOLDOUT"


@dataclass(frozen=True)
class DiagnosticObservation:
    observation_id: str
    project_id: str
    global_run_id: str
    agent_id: str
    agent_instance_id: str
    work_id: str
    strategy_id: str
    outcome_reward: float
    confidence: float
    evidence_partition: EvidencePartition
    evidence_refs: tuple[str, ...]
    created_at_utc: str
    verified: bool = True
    contaminated: bool = False
    context_tags: tuple[str, ...] = ()

    def __post_init__(self):
        if not all((self.observation_id, self.project_id, self.agent_id, self.agent_instance_id, self.work_id, self.strategy_id)):
            raise DiagnosticLearningError("required diagnostic identity field missing")
        if not -1.0 <= float(self.outcome_reward) <= 1.0:
            raise DiagnosticLearningError("outcome_reward must be in [-1, 1]")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise DiagnosticLearningError("confidence must be in [0, 1]")
        parse_iso(self.created_at_utc)
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))
        object.__setattr__(self, "context_tags", tuple(sorted(set(self.context_tags))))


@dataclass(frozen=True)
class DiagnosticPolicy:
    min_confidence: float = 0.55
    min_samples_for_recommendation: int = 3
    uncertainty_penalty: float = 0.75
    drift_window: int = 4
    drift_threshold: float = 0.45
    max_history_per_strategy: int = 128

    def __post_init__(self):
        if not 0 <= self.min_confidence <= 1:
            raise DiagnosticLearningError("min_confidence must be in [0,1]")
        if self.min_samples_for_recommendation < 1 or self.drift_window < 2:
            raise DiagnosticLearningError("sample/window bounds invalid")
        if self.drift_threshold <= 0 or self.max_history_per_strategy < self.drift_window * 2:
            raise DiagnosticLearningError("drift/history bounds invalid")


@dataclass(frozen=True)
class StrategyDiagnostic:
    strategy_id: str
    samples: int
    weighted_samples: float
    mean_reward: float
    uncertainty: float
    conservative_score: float
    drift_suspected: bool
    status: str
    authority: bool = False


class DiagnosticLearningEngine:
    """Bounded evidence-weighted learner.

    It learns only advisory strategy scores. It has no policy mutation, capability
    mutation, task ownership, deployment, or external-effect surface.
    """

    def __init__(self, policy: DiagnosticPolicy | None = None):
        self.policy = policy or DiagnosticPolicy()
        self._seen: dict[str, str] = {}
        self._stats = defaultdict(lambda: {"count": 0, "weight": 0.0, "sum": 0.0, "sum_sq": 0.0})
        self._history: dict[str, deque[float]] = defaultdict(
            lambda: deque(maxlen=self.policy.max_history_per_strategy)
        )
        self._holdout: list[DiagnosticObservation] = []
        self._quarantine: list[DiagnosticObservation] = []

    def observe(self, observation: DiagnosticObservation) -> str:
        payload_digest = digest(asdict(observation))
        prior = self._seen.get(observation.observation_id)
        if prior is not None:
            if prior != payload_digest:
                raise DiagnosticLearningError("observation id collision")
            return "IDEMPOTENT"

        self._seen[observation.observation_id] = payload_digest
        if (
            observation.contaminated
            or not observation.verified
            or observation.confidence < self.policy.min_confidence
        ):
            self._quarantine.append(observation)
            return "QUARANTINED"

        if observation.evidence_partition == EvidencePartition.HOLDOUT:
            self._holdout.append(observation)
            return "HOLDOUT_ONLY"

        stats = self._stats[observation.strategy_id]
        weight = float(observation.confidence)
        reward = float(observation.outcome_reward)
        stats["count"] += 1
        stats["weight"] += weight
        stats["sum"] += reward * weight
        stats["sum_sq"] += reward * reward * weight
        self._history[observation.strategy_id].append(reward)
        return "LEARNED"

    def _diagnostic(self, strategy_id: str) -> StrategyDiagnostic:
        stats = self._stats[strategy_id]
        if stats["count"] == 0 or stats["weight"] <= 0:
            return StrategyDiagnostic(strategy_id, 0, 0.0, 0.0, 1.0, -1.0, False, "INSUFFICIENT_EVIDENCE")
        mean = stats["sum"] / stats["weight"]
        variance = max(0.0, (stats["sum_sq"] / stats["weight"]) - mean * mean)
        uncertainty = math.sqrt(variance / max(stats["weight"], 1e-9))
        conservative = mean - self.policy.uncertainty_penalty * uncertainty
        drift = self.detect_drift(strategy_id)
        status = (
            "DRIFT_SUSPECTED"
            if drift
            else "CANDIDATE"
            if stats["count"] >= self.policy.min_samples_for_recommendation
            else "INSUFFICIENT_EVIDENCE"
        )
        return StrategyDiagnostic(
            strategy_id=strategy_id,
            samples=stats["count"],
            weighted_samples=stats["weight"],
            mean_reward=mean,
            uncertainty=uncertainty,
            conservative_score=conservative,
            drift_suspected=drift,
            status=status,
        )

    def diagnostics(self) -> tuple[StrategyDiagnostic, ...]:
        return tuple(self._diagnostic(s) for s in sorted(self._stats))

    def recommend(self) -> StrategyDiagnostic | None:
        eligible = [
            d for d in self.diagnostics()
            if d.samples >= self.policy.min_samples_for_recommendation and not d.drift_suspected
        ]
        if not eligible:
            return None
        return max(eligible, key=lambda d: (d.conservative_score, d.mean_reward, d.strategy_id))

    def detect_drift(self, strategy_id: str) -> bool:
        values = list(self._history.get(strategy_id, ()))
        w = self.policy.drift_window
        if len(values) < 2 * w:
            return False
        old = sum(values[-2*w:-w]) / w
        new = sum(values[-w:]) / w
        return abs(new - old) >= self.policy.drift_threshold

    def evaluate_holdout(self) -> dict:
        by_strategy: dict[str, list[float]] = defaultdict(list)
        for row in self._holdout:
            by_strategy[row.strategy_id].append(row.outcome_reward)
        result = {
            strategy: {
                "samples": len(values),
                "mean_reward": sum(values) / len(values),
            }
            for strategy, values in sorted(by_strategy.items())
        }
        return {
            "partition": "HOLDOUT",
            "trained_on_holdout": False,
            "strategies": result,
            "digest": digest(result),
        }

    def snapshot(self) -> dict:
        payload = {
            "algorithm": "bounded-evidence-weighted-online-mean-v1",
            "policy": asdict(self.policy),
            "strategies": [asdict(d) for d in self.diagnostics()],
            "observation_count": len(self._seen),
            "holdout_count": len(self._holdout),
            "quarantine_count": len(self._quarantine),
            "authority": False,
            "may_promote_doctrine": False,
            "may_execute_effects": False,
        }
        return {**payload, "snapshot_digest": digest(payload)}


@dataclass(frozen=True)
class LearningRecommendation:
    strategy_id: str
    rationale: str
    evidence_digest: str
    confidence_class: str
    validation_state: str = "CANDIDATE"
    authority: bool = False


def recommendation_from_engine(engine: DiagnosticLearningEngine) -> LearningRecommendation | None:
    best = engine.recommend()
    if best is None:
        return None
    confidence_class = "HIGH" if best.samples >= max(8, engine.policy.min_samples_for_recommendation * 2) and best.uncertainty < 0.15 else "MEDIUM"
    return LearningRecommendation(
        strategy_id=best.strategy_id,
        rationale=(
            f"strategy has conservative diagnostic score {best.conservative_score:.4f} "
            f"from {best.samples} verified training observations"
        ),
        evidence_digest=engine.snapshot()["snapshot_digest"],
        confidence_class=confidence_class,
    )
