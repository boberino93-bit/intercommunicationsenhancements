from datetime import datetime, timedelta, timezone
import unittest

from org_agent_mesh.architecture_governance import (
    ArchitectureGovernanceError,
    BoundaryContract,
    ComplexityDelta,
    DependencyGraph,
    FAILURE_TAXONOMY,
    MechanismClass,
    RegistryEntry,
    validate_recovery_disposition,
)
from org_agent_mesh.reliability_v18_core import iso, sign
from org_agent_mesh.successor_bootstrap import (
    CapabilityObservation,
    ExistingLaunch,
    GET_STARTED_SEQUENCE,
    HUMAN_PROJECT_PRIORITY,
    PriorityCandidate,
    PriorityFrontierSnapshot,
    PriorityProvenance,
    ResearchLaunchEnvelope,
    StepUpAttestation,
    StepUpVerifier,
    SuccessorBootstrapError,
    initial_duo_research_profile,
    resolve_launch_disposition,
    resolve_project_priority,
    select_capability_path,
    semantic_launch_identity,
)


NOW = datetime(2026, 10, 5, 9, 30, tzinfo=timezone.utc)


class SuccessorBootstrapTests(unittest.TestCase):
    def test_human_priority_wins_and_duo_is_first(self):
        provenance, rank, order = resolve_project_priority("Duo Screen / Duo Open")
        self.assertEqual(provenance, PriorityProvenance.HUMAN_SET)
        self.assertEqual(rank, 1)
        self.assertEqual(order, HUMAN_PROJECT_PRIORITY)

    def test_unknown_project_reports_incomplete_not_guessed(self):
        provenance, rank, _ = resolve_project_priority("Unknown Project")
        self.assertEqual(provenance, PriorityProvenance.INCOMPLETE)
        self.assertIsNone(rank)

    def test_derived_priority_is_explicit(self):
        provenance, rank, order = resolve_project_priority(
            "B", human_order=None,
            derived_candidates=(
                PriorityCandidate("A", "x", blocker_severity=1),
                PriorityCandidate("B", "y", blocker_severity=2),
            ),
        )
        self.assertEqual(provenance, PriorityProvenance.DERIVED)
        self.assertEqual(rank, 1)
        self.assertEqual(order[0], "B")

    def test_snapshot_freshness_is_fail_closed(self):
        snap = PriorityFrontierSnapshot(
            "s1", ("sha",), iso(NOW), iso(NOW + timedelta(seconds=30)),
            HUMAN_PROJECT_PRIORITY, "HUMAN_SET", "duo-open", 1, ("q",),
        )
        snap.require_fresh(NOW + timedelta(seconds=29))
        with self.assertRaises(SuccessorBootstrapError):
            snap.require_fresh(NOW + timedelta(seconds=30))

    def test_get_started_is_deterministic_and_claim_follows_read(self):
        self.assertEqual(GET_STARTED_SEQUENCE[0], "ORIENT")
        self.assertLess(GET_STARTED_SEQUENCE.index("READ_PRIORITY_FRONTIER_SNAPSHOT"), GET_STARTED_SEQUENCE.index("CLAIM_REGISTER_CANONICAL"))
        self.assertLess(GET_STARTED_SEQUENCE.index("CLAIM_REGISTER_CANONICAL"), GET_STARTED_SEQUENCE.index("EXECUTE"))

    def test_initial_duo_profile_is_scoped_to_first_kickoff(self):
        profile = initial_duo_research_profile("Duo Screen / Duo Open", first_kickoff=True)
        self.assertEqual(profile, {"MASTER": 1, "MANAGER": 1, "RESEARCH": 3})
        with self.assertRaises(SuccessorBootstrapError):
            initial_duo_research_profile("BenefitFlow", first_kickoff=True)

    def _envelope(self):
        sid = semantic_launch_identity(project_id="duo-open", objective_class="research-frontier")
        return ResearchLaunchEnvelope(
            project_id="duo-open", run_id="run-new", task_id="task-1", semantic_launch_id=sid,
            role="RESEARCH", allowed_capabilities=("web",), priority_frontier_snapshot_ref="snap-1",
            source_boundaries=("PUBLIC",), prohibited_sources=("EMPLOYER_PRIVATE",),
            objective_class="research-frontier", resource_budget={"minutes": 20},
            verification_expectations=("source-corroboration",), checkpoint_location="cp/1",
            heartbeat_destination="bus/liveness", material_delta_destination="bus/material",
            stop_criteria=("blocking-question-answered",), escalation_conditions=("human-decision",),
            handoff_contract_ref="protocols/agent_state_handoff.md", policy_versions=("p1",), protocol_versions=("v1",),
        )

    def test_duplicate_launch_attaches_before_sharding(self):
        env = self._envelope()
        disposition, run_id = resolve_launch_disposition(env, [ExistingLaunch(env.semantic_launch_id, "run-old", "ACTIVE", True)])
        self.assertEqual(disposition.value, "ATTACH")
        self.assertEqual(run_id, "run-old")

    def test_capability_discovery_denies_unauthorized_fallback(self):
        observations = [CapabilityObservation("web", True, False, "project", "authoritative", False)]
        with self.assertRaises(SuccessorBootstrapError):
            select_capability_path(observations, ("web",))

    def test_step_up_attestation_is_exact_action_nonreplayable(self):
        key = b"0123456789abcdef0123456789abcdef"
        unsigned = {
            "attestation_id": "att-1", "subject": "Robert Leonard", "authority_class": "HUMAN_ROOT",
            "project_id": "intercommunicationsenhancements", "authentication_strength": "GITHUB_AUTHENTICATED_ROOT",
            "action_digest": "action-a", "issued_at_utc": iso(NOW - timedelta(seconds=1)),
            "expires_at_utc": iso(NOW + timedelta(minutes=5)), "nonce": "n-1", "verifier_id": "github-root", "status": "VALID",
        }
        att = StepUpAttestation(**unsigned, signature=sign(unsigned, key))
        verifier = StepUpVerifier({"github-root": key})
        subject = verifier.verify_and_consume(att, now=NOW, project_id="intercommunicationsenhancements", action_digest="action-a", required_authority_class="HUMAN_ROOT")
        self.assertEqual(subject, "Robert Leonard")
        with self.assertRaises(SuccessorBootstrapError):
            verifier.verify_and_consume(att, now=NOW, project_id="intercommunicationsenhancements", action_digest="action-a", required_authority_class="HUMAN_ROOT")

    def test_step_up_attestation_cannot_authorize_different_action(self):
        key = b"0123456789abcdef0123456789abcdef"
        unsigned = {
            "attestation_id": "att-2", "subject": "Robert Leonard", "authority_class": "HUMAN_ROOT",
            "project_id": "intercommunicationsenhancements", "authentication_strength": "GITHUB_AUTHENTICATED_ROOT",
            "action_digest": "action-a", "issued_at_utc": iso(NOW - timedelta(seconds=1)),
            "expires_at_utc": iso(NOW + timedelta(minutes=5)), "nonce": "n-2", "verifier_id": "github-root", "status": "VALID",
        }
        att = StepUpAttestation(**unsigned, signature=sign(unsigned, key))
        verifier = StepUpVerifier({"github-root": key})
        with self.assertRaises(SuccessorBootstrapError):
            verifier.verify_and_consume(att, now=NOW, project_id="intercommunicationsenhancements", action_digest="action-b", required_authority_class="HUMAN_ROOT")


class ArchitectureGovernanceTests(unittest.TestCase):
    def test_registry_cannot_create_authority(self):
        entry = RegistryEntry("x", MechanismClass.INVARIANT, "human-root", True, False, "1.0", creates_authority=True)
        with self.assertRaises(ArchitectureGovernanceError): entry.validate()

    def test_contract_failure_semantics_are_canonical(self):
        contract = BoundaryContract("c1", "agent", "tool", "1.0", ("request",), ("receipt",), ("INPUT_INVALID", "UNKNOWN_EFFECT"), ("self_authorize",), "idempotency-key", ("same-or-narrower",))
        contract.validate()
        self.assertIn("UNKNOWN_EFFECT", FAILURE_TAXONOMY)

    def test_dependency_graph_reports_transitive_impact(self):
        graph = DependencyGraph({"executor": ["gateway"], "gateway": ["policy"], "policy": []})
        self.assertEqual(graph.dependents_of("policy"), ("executor", "gateway"))

    def test_unknown_effect_cannot_blind_retry(self):
        with self.assertRaises(ArchitectureGovernanceError): validate_recovery_disposition("UNKNOWN_EFFECT", "RETRY")
        validate_recovery_disposition("UNKNOWN_EFFECT", "VERIFY_OR_RECOVERY")

    def test_complexity_must_earn_its_cost(self):
        self.assertFalse(ComplexityDelta(components_added=3, measurable_gain=1).earns_cost())
        self.assertTrue(ComplexityDelta(components_added=1, duplicated_logic_eliminated=2, measurable_gain=5).earns_cost())


if __name__ == "__main__":
    unittest.main()
