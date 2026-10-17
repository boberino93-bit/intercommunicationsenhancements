from org_agent_mesh.communication_security_bridge import (
    IndependenceAdjustedConsensusGate,
    ReviewerJudgment,
    SecurityHardenedCommunicationBridge,
)


def judgment(
    reviewer: str,
    lineage: str,
    verdict: str = "SUPPORT",
    *,
    falsification: bool = False,
    independent: bool = True,
):
    return ReviewerJudgment(
        finding_id="F-001",
        reviewer_instance_id=reviewer,
        evidence_lineage_id=lineage,
        evidence_refs=(f"evidence-{lineage}",),
        verdict=verdict,
        independent=independent,
        falsification_attempted=falsification,
        confidence=90,
    )


def test_four_reviewers_sharing_one_lineage_do_not_create_consensus():
    gate = IndependenceAdjustedConsensusGate(threshold=0.80, min_independent_lineages=2)
    rows = [
        judgment("reviewer-1", "lineage-a", falsification=True),
        judgment("reviewer-2", "lineage-a"),
        judgment("reviewer-3", "lineage-a"),
        judgment("reviewer-4", "lineage-a"),
    ]
    result = gate.evaluate(finding_id="F-001", severity="CRITICAL", judgments=rows)
    assert result.raw_support == 4
    assert result.independent_lineages == 1
    assert result.promotion_eligible is False
    assert result.reason == "insufficient independent evidence lineages"


def test_four_of_five_independent_lineages_pass_eighty_percent_with_falsification():
    gate = IndependenceAdjustedConsensusGate(threshold=0.80, min_independent_lineages=2)
    rows = [
        judgment("reviewer-1", "lineage-a", falsification=True),
        judgment("reviewer-2", "lineage-b"),
        judgment("reviewer-3", "lineage-c"),
        judgment("reviewer-4", "lineage-d"),
        judgment("reviewer-5", "lineage-e", verdict="OPPOSE"),
    ]
    result = gate.evaluate(finding_id="F-001", severity="CRITICAL", judgments=rows)
    assert result.supporting_independent_lineages == 4
    assert result.opposing_independent_lineages == 1
    assert result.independence_adjusted_support == 0.8
    assert result.falsification_paths == 1
    assert result.promotion_eligible is True


def test_high_severity_requires_falsification_path():
    gate = IndependenceAdjustedConsensusGate(threshold=0.80, min_independent_lineages=2)
    rows = [judgment("reviewer-1", "lineage-a"), judgment("reviewer-2", "lineage-b")]
    result = gate.evaluate(finding_id="F-001", severity="HIGH", judgments=rows)
    assert result.independence_adjusted_support == 1.0
    assert result.promotion_eligible is False
    assert result.reason == "high-impact finding lacks independent falsification path"


def test_inherited_reviews_are_excluded_from_independence_denominator():
    gate = IndependenceAdjustedConsensusGate(threshold=0.80, min_independent_lineages=2)
    rows = [
        judgment("reviewer-1", "lineage-a", falsification=True),
        judgment("reviewer-2", "lineage-b", independent=False),
        judgment("reviewer-3", "lineage-c", independent=False),
    ]
    result = gate.evaluate(finding_id="F-001", severity="HIGH", judgments=rows)
    assert result.raw_support == 3
    assert result.independent_lineages == 1
    assert result.promotion_eligible is False


def test_bridge_targets_are_exact_project_scoped_resources():
    assert (
        SecurityHardenedCommunicationBridge.export_target("project-a", "snapshot-1")
        == "cross-project-snapshot-export:project-a:snapshot-1"
    )
    assert (
        SecurityHardenedCommunicationBridge.import_target("project-b", "project-a", "snapshot-1")
        == "cross-project-snapshot-import:project-b:project-a:snapshot-1"
    )
