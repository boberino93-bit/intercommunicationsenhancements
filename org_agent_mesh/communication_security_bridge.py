from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Iterable, Mapping

from .consequence_gateway import (
    CommitAuthorizationGrant,
    ConsequenceGateway,
    ConsequenceGatewayError,
    ConsequenceReceipt,
    CurrentCommitState,
    EffectOutcome,
    EffectState,
    PreparedAction,
)
from .operational_intelligence_federation import SanitizedSnapshotBridge
from .project_scope import ProjectScopeError, require_project_id, require_resource_id
from .reliability_v18_core import digest


class CommunicationSecurityBridgeError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReviewerJudgment:
    finding_id: str
    reviewer_instance_id: str
    evidence_lineage_id: str
    evidence_refs: tuple[str, ...]
    verdict: str
    independent: bool
    falsification_attempted: bool
    confidence: int

    def __post_init__(self) -> None:
        require_resource_id(self.finding_id, field="finding_id")
        require_resource_id(self.reviewer_instance_id, field="reviewer_instance_id")
        require_resource_id(self.evidence_lineage_id, field="evidence_lineage_id")
        if self.verdict not in {"SUPPORT", "OPPOSE", "ABSTAIN"}:
            raise CommunicationSecurityBridgeError("unsupported reviewer verdict")
        if not 0 <= self.confidence <= 100:
            raise CommunicationSecurityBridgeError("reviewer confidence must be 0..100")
        if not self.evidence_refs or not all(isinstance(ref, str) and ref.strip() for ref in self.evidence_refs):
            raise CommunicationSecurityBridgeError("reviewer judgment requires evidence references")


@dataclass(frozen=True)
class ConsensusDecision:
    finding_id: str
    severity: str
    raw_support: int
    raw_oppose: int
    raw_abstain: int
    independent_lineages: int
    resolved_independent_lineages: int
    supporting_independent_lineages: int
    opposing_independent_lineages: int
    contested_lineages: tuple[str, ...]
    falsification_paths: int
    independence_adjusted_support: float
    threshold: float
    promotion_eligible: bool
    reason: str
    decision_digest: str


class IndependenceAdjustedConsensusGate:
    """Fail-closed promotion gate that counts independent evidence lineages, not reviewer identities."""

    def __init__(self, *, threshold: float = 0.80, min_independent_lineages: int = 2):
        if not 0.5 <= threshold <= 1.0:
            raise ValueError("threshold must be between 0.5 and 1.0")
        if min_independent_lineages < 1:
            raise ValueError("min_independent_lineages must be >= 1")
        self.threshold = float(threshold)
        self.min_independent_lineages = int(min_independent_lineages)

    def evaluate(
        self,
        *,
        finding_id: str,
        severity: str,
        judgments: Iterable[ReviewerJudgment],
    ) -> ConsensusDecision:
        finding_id = require_resource_id(finding_id, field="finding_id")
        severity = str(severity).upper()
        if severity not in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}:
            raise CommunicationSecurityBridgeError("unsupported severity")

        rows = tuple(judgments)
        if not rows:
            return self._decision(
                finding_id=finding_id,
                severity=severity,
                raw_support=0,
                raw_oppose=0,
                raw_abstain=0,
                independent_lineages=0,
                resolved_independent_lineages=0,
                supporting_independent_lineages=0,
                opposing_independent_lineages=0,
                contested_lineages=(),
                falsification_paths=0,
                ratio=0.0,
                eligible=False,
                reason="no reviewer judgments",
            )
        if any(row.finding_id != finding_id for row in rows):
            raise CommunicationSecurityBridgeError("reviewer judgment finding mismatch")

        raw_support = sum(row.verdict == "SUPPORT" for row in rows)
        raw_oppose = sum(row.verdict == "OPPOSE" for row in rows)
        raw_abstain = sum(row.verdict == "ABSTAIN" for row in rows)

        independent_rows = tuple(row for row in rows if row.independent)
        grouped: dict[str, list[ReviewerJudgment]] = {}
        for row in independent_rows:
            grouped.setdefault(row.evidence_lineage_id, []).append(row)

        support_lineages = 0
        oppose_lineages = 0
        contested: list[str] = []
        for lineage_id, lineage_rows in grouped.items():
            resolved = {row.verdict for row in lineage_rows if row.verdict != "ABSTAIN"}
            if len(resolved) > 1:
                contested.append(lineage_id)
            elif resolved == {"SUPPORT"}:
                support_lineages += 1
            elif resolved == {"OPPOSE"}:
                oppose_lineages += 1

        resolved_lineages = support_lineages + oppose_lineages
        ratio = (support_lineages / resolved_lineages) if resolved_lineages else 0.0
        falsification_lineages = {
            row.evidence_lineage_id
            for row in independent_rows
            if row.falsification_attempted
        }

        reason = "eligible"
        eligible = True
        if len(grouped) < self.min_independent_lineages:
            eligible = False
            reason = "insufficient independent evidence lineages"
        elif resolved_lineages < self.min_independent_lineages:
            eligible = False
            reason = "insufficient resolved independent evidence lineages"
        elif ratio < self.threshold:
            eligible = False
            reason = "independence-adjusted support below threshold"
        elif severity in {"CRITICAL", "HIGH"} and not falsification_lineages:
            eligible = False
            reason = "high-impact finding lacks independent falsification path"
        elif contested:
            # Contested lineages do not count as support, and their existence remains visible.
            reason = "eligible with contested lineages excluded from consensus ratio"

        return self._decision(
            finding_id=finding_id,
            severity=severity,
            raw_support=raw_support,
            raw_oppose=raw_oppose,
            raw_abstain=raw_abstain,
            independent_lineages=len(grouped),
            resolved_independent_lineages=resolved_lineages,
            supporting_independent_lineages=support_lineages,
            opposing_independent_lineages=oppose_lineages,
            contested_lineages=tuple(sorted(contested)),
            falsification_paths=len(falsification_lineages),
            ratio=ratio,
            eligible=eligible,
            reason=reason,
        )

    def _decision(
        self,
        *,
        finding_id: str,
        severity: str,
        raw_support: int,
        raw_oppose: int,
        raw_abstain: int,
        independent_lineages: int,
        resolved_independent_lineages: int,
        supporting_independent_lineages: int,
        opposing_independent_lineages: int,
        contested_lineages: tuple[str, ...],
        falsification_paths: int,
        ratio: float,
        eligible: bool,
        reason: str,
    ) -> ConsensusDecision:
        unsigned = {
            "finding_id": finding_id,
            "severity": severity,
            "raw_support": raw_support,
            "raw_oppose": raw_oppose,
            "raw_abstain": raw_abstain,
            "independent_lineages": independent_lineages,
            "resolved_independent_lineages": resolved_independent_lineages,
            "supporting_independent_lineages": supporting_independent_lineages,
            "opposing_independent_lineages": opposing_independent_lineages,
            "contested_lineages": list(contested_lineages),
            "falsification_paths": falsification_paths,
            "independence_adjusted_support": ratio,
            "threshold": self.threshold,
            "promotion_eligible": eligible,
            "reason": reason,
        }
        return ConsensusDecision(
            **{k: v for k, v in unsigned.items() if k != "contested_lineages"},
            contested_lineages=contested_lineages,
            decision_digest=digest(unsigned),
        )


@dataclass(frozen=True)
class BridgeEffectResult:
    receipt: ConsequenceReceipt
    record: object | None


class SecurityHardenedCommunicationBridge:
    """Composes exact-action authorization with the immutable sanitized snapshot bridge.

    It does not mint grants and cannot make an external host route through this class. Deployment
    must ensure protected effects reach this boundary; bypasses are architecture non-compliance.
    """

    EXPORT_EFFECT = "CROSS_PROJECT_SNAPSHOT_EXPORT"
    IMPORT_EFFECT = "CROSS_PROJECT_SNAPSHOT_IMPORT"

    def __init__(
        self,
        *,
        snapshot_bridge: SanitizedSnapshotBridge,
        consequence_gateway: ConsequenceGateway,
    ) -> None:
        if not isinstance(snapshot_bridge, SanitizedSnapshotBridge):
            raise TypeError("snapshot_bridge must be SanitizedSnapshotBridge")
        if not isinstance(consequence_gateway, ConsequenceGateway):
            raise TypeError("consequence_gateway must be ConsequenceGateway")
        self.snapshot_bridge = snapshot_bridge
        self.consequence_gateway = consequence_gateway

    @staticmethod
    def export_target(project_id: str, snapshot_id: str) -> str:
        return f"cross-project-snapshot-export:{require_project_id(project_id)}:{require_resource_id(snapshot_id, field='snapshot_id')}"

    @staticmethod
    def import_target(destination_project_id: str, source_project_id: str, snapshot_id: str) -> str:
        return (
            "cross-project-snapshot-import:"
            f"{require_project_id(destination_project_id)}:"
            f"{require_project_id(source_project_id)}:"
            f"{require_resource_id(snapshot_id, field='snapshot_id')}"
        )

    @staticmethod
    def _require_prepared(prepared: PreparedAction, *, effect: str, target: str) -> None:
        if prepared.effect_class != effect:
            raise CommunicationSecurityBridgeError("prepared action effect class mismatch")
        if prepared.target != target:
            raise CommunicationSecurityBridgeError("prepared action target mismatch")

    def publish_export(
        self,
        *,
        attempt_id: str,
        source_session,
        exchange: Mapping,
        snapshot: Mapping,
        prepared: PreparedAction,
        grant: CommitAuthorizationGrant,
        current: CurrentCommitState,
        now: datetime,
    ) -> BridgeEffectResult:
        project_id = require_project_id(exchange.get("source_project_id"))
        snapshot_id = require_resource_id(snapshot.get("snapshot_id"), field="snapshot_id")
        target = self.export_target(project_id, snapshot_id)
        self._require_prepared(prepared, effect=self.EXPORT_EFFECT, target=target)
        record_holder: dict[str, object] = {}

        def execute(_: PreparedAction) -> EffectOutcome:
            record = self.snapshot_bridge.publish_export(source_session, exchange, snapshot, now=now)
            record_holder["record"] = record
            return EffectOutcome(
                EffectState.CONFIRMED,
                target_evidence_digest=digest({"namespace": self.snapshot_bridge.EXPORT_NAMESPACE, "project_id": project_id, "snapshot_id": snapshot_id, "record": repr(record)}),
            )

        receipt = self.consequence_gateway.commit(
            attempt_id=attempt_id,
            prepared=prepared,
            grant=grant,
            current=current,
            now=now,
            executor=execute,
        )
        return BridgeEffectResult(receipt=receipt, record=record_holder.get("record"))

    def import_export(
        self,
        *,
        attempt_id: str,
        destination_session,
        destination_project_id: str,
        source_project_id: str,
        snapshot_id: str,
        prepared: PreparedAction,
        grant: CommitAuthorizationGrant,
        current: CurrentCommitState,
        now: datetime,
    ) -> BridgeEffectResult:
        destination_project_id = require_project_id(destination_project_id)
        source_project_id = require_project_id(source_project_id)
        snapshot_id = require_resource_id(snapshot_id, field="snapshot_id")
        target = self.import_target(destination_project_id, source_project_id, snapshot_id)
        self._require_prepared(prepared, effect=self.IMPORT_EFFECT, target=target)
        if current.project_id != destination_project_id:
            raise ProjectScopeError("current commit state does not match destination project")
        record_holder: dict[str, object] = {}

        def execute(_: PreparedAction) -> EffectOutcome:
            record = self.snapshot_bridge.import_export(
                destination_session,
                source_project_id=source_project_id,
                snapshot_id=snapshot_id,
                now=now,
            )
            record_holder["record"] = record
            return EffectOutcome(
                EffectState.CONFIRMED,
                target_evidence_digest=digest({"namespace": self.snapshot_bridge.IMPORT_NAMESPACE, "destination_project_id": destination_project_id, "source_project_id": source_project_id, "snapshot_id": snapshot_id, "record": repr(record)}),
            )

        receipt = self.consequence_gateway.commit(
            attempt_id=attempt_id,
            prepared=prepared,
            grant=grant,
            current=current,
            now=now,
            executor=execute,
        )
        return BridgeEffectResult(receipt=receipt, record=record_holder.get("record"))


def require_promotion_eligible(decision: ConsensusDecision) -> None:
    if not decision.promotion_eligible:
        raise CommunicationSecurityBridgeError(
            f"security finding is not eligible for promotion: {decision.reason}"
        )
