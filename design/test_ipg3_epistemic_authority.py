"""Adversarial checks for the design-only IPG3 epistemic authority gate."""

from datetime import datetime, timezone

from ipg3_epistemic_authority import (
    AuthorityContext,
    EpistemicGateError,
    EpistemicGrantLedger,
    EvidenceRef,
    issue_promotion_grant,
)


NOW = datetime(2026, 10, 8, 1, 38, tzinfo=timezone.utc)
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
PAYLOAD = "c" * 64


def record(trust_class="DERIVED_KNOWLEDGE"):
    return {
        "schema": "org-agent-mesh/trust-provenance-record/v1-draft",
        "record_id": "claim-001",
        "project_id": "intercommunicationsenhancements",
        "trust_class": trust_class,
        "validation_state": "CONTENT_VERIFIED",
    }


def authority(*, role="PRIMARY", capabilities=("WRITE_ACCEPTED_STATE", "APPROVE_CHANGE")):
    return AuthorityContext(
        project_id="intercommunicationsenhancements",
        issuer_agent_id="primary",
        issuer_agent_instance_id="intercommunicationsenhancements--primary-test",
        issuer_role=role,
        capabilities=tuple(capabilities),
        operation="accepted-state.compare-and-set",
        target_resource_id="kernel-policy",
        expected_version=7,
        payload_sha256=PAYLOAD,
        issued_at_utc="2026-10-08T01:30:00Z",
        expires_at_utc="2026-10-08T02:30:00Z",
    )


def evidence(evidence_id, source_id, digest, *, revision="r1"):
    return EvidenceRef(
        evidence_id=evidence_id,
        source_type="RUNTIME_EVENT",
        source_id=source_id,
        source_revision=revision,
        content_sha256=digest,
        observed_at_utc="2026-10-08T01:20:00Z",
    )


def expect_error(fn, needle):
    try:
        fn()
    except EpistemicGateError as exc:
        assert needle.lower() in str(exc).lower(), (needle, str(exc))
    else:
        raise AssertionError(f"expected EpistemicGateError containing {needle!r}")


def test_correlated_consensus_is_not_independent_evidence():
    same_source = [
        evidence("ev-1", "run-77", DIGEST_A),
        evidence("ev-2", "run-77", DIGEST_A),
        evidence("ev-3", "run-77", DIGEST_A),
    ]
    expect_error(
        lambda: issue_promotion_grant(
            record(),
            target_class="VERIFIED_FACT",
            decision_id="decision-1",
            validator_ids=["reviewer-a", "reviewer-b", "reviewer-c"],
            evidence=same_source,
            authority=authority(),
            now=NOW,
        ),
        "independent evidence",
    )


def test_independent_lineages_can_promote_low_trust_to_verified_fact():
    grant = issue_promotion_grant(
        record(),
        target_class="VERIFIED_FACT",
        decision_id="decision-2",
        validator_ids=["reviewer-a"],
        evidence=[
            evidence("ev-1", "run-77", DIGEST_A),
            evidence("ev-2", "run-88", DIGEST_B),
        ],
        authority=authority(),
        now=NOW,
    )
    assert grant.target_class == "VERIFIED_FACT"
    assert len(grant.evidence_independence_keys) == 2


def test_generative_output_cannot_jump_to_authoritative_config():
    expect_error(
        lambda: issue_promotion_grant(
            record("AGENT_REFLECTION"),
            target_class="AUTHORITATIVE_CONFIG",
            decision_id="decision-3",
            validator_ids=["reviewer-a"],
            evidence=[
                evidence("ev-1", "run-77", DIGEST_A),
                evidence("ev-2", "run-88", DIGEST_B),
            ],
            authority=authority(),
            now=NOW,
        ),
        "not allowed",
    )


def test_authoritative_config_requires_primary_and_both_capabilities():
    verified = record("VERIFIED_FACT")
    ev = [
        evidence("ev-1", "run-77", DIGEST_A),
        evidence("ev-2", "run-88", DIGEST_B),
    ]
    expect_error(
        lambda: issue_promotion_grant(
            verified,
            target_class="AUTHORITATIVE_CONFIG",
            decision_id="decision-4",
            validator_ids=["reviewer-a"],
            evidence=ev,
            authority=authority(role="MANAGER"),
            now=NOW,
        ),
        "PRIMARY",
    )
    expect_error(
        lambda: issue_promotion_grant(
            verified,
            target_class="AUTHORITATIVE_CONFIG",
            decision_id="decision-4",
            validator_ids=["reviewer-a"],
            evidence=ev,
            authority=authority(capabilities=("WRITE_ACCEPTED_STATE",)),
            now=NOW,
        ),
        "missing capabilities",
    )


def test_grant_is_bound_to_exact_effect_and_single_use():
    grant = issue_promotion_grant(
        record("VERIFIED_FACT"),
        target_class="AUTHORITATIVE_CONFIG",
        decision_id="decision-5",
        validator_ids=["reviewer-a", "reviewer-b"],
        evidence=[
            evidence("ev-1", "run-77", DIGEST_A),
            evidence("ev-2", "run-88", DIGEST_B),
        ],
        authority=authority(),
        now=NOW,
    )
    ledger = EpistemicGrantLedger()
    assert ledger.consume(
        grant,
        project_id="intercommunicationsenhancements",
        operation="accepted-state.compare-and-set",
        target_resource_id="kernel-policy",
        expected_version=7,
        payload_sha256=PAYLOAD,
        issuer_agent_instance_id="intercommunicationsenhancements--primary-test",
        now=NOW,
    )
    expect_error(
        lambda: ledger.consume(
            grant,
            project_id="intercommunicationsenhancements",
            operation="accepted-state.compare-and-set",
            target_resource_id="kernel-policy",
            expected_version=7,
            payload_sha256=PAYLOAD,
            issuer_agent_instance_id="intercommunicationsenhancements--primary-test",
            now=NOW,
        ),
        "already consumed",
    )


def test_wrong_version_or_payload_fails_closed():
    grant = issue_promotion_grant(
        record("VERIFIED_FACT"),
        target_class="AUTHORITATIVE_CONFIG",
        decision_id="decision-6",
        validator_ids=["reviewer-a"],
        evidence=[
            evidence("ev-1", "run-77", DIGEST_A),
            evidence("ev-2", "run-88", DIGEST_B),
        ],
        authority=authority(),
        now=NOW,
    )
    ledger = EpistemicGrantLedger()
    expect_error(
        lambda: ledger.consume(
            grant,
            project_id="intercommunicationsenhancements",
            operation="accepted-state.compare-and-set",
            target_resource_id="kernel-policy",
            expected_version=8,
            payload_sha256=PAYLOAD,
            issuer_agent_instance_id="intercommunicationsenhancements--primary-test",
            now=NOW,
        ),
        "binding mismatch",
    )
    expect_error(
        lambda: ledger.consume(
            grant,
            project_id="intercommunicationsenhancements",
            operation="accepted-state.compare-and-set",
            target_resource_id="kernel-policy",
            expected_version=7,
            payload_sha256="d" * 64,
            issuer_agent_instance_id="intercommunicationsenhancements--primary-test",
            now=NOW,
        ),
        "binding mismatch",
    )


def main():
    for fn in (
        test_correlated_consensus_is_not_independent_evidence,
        test_independent_lineages_can_promote_low_trust_to_verified_fact,
        test_generative_output_cannot_jump_to_authoritative_config,
        test_authoritative_config_requires_primary_and_both_capabilities,
        test_grant_is_bound_to_exact_effect_and_single_use,
        test_wrong_version_or_payload_fails_closed,
    ):
        fn()
    print("IPG3 epistemic authority gate tests: PASS")


if __name__ == "__main__":
    main()
