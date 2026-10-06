from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.epistemic_coordination import (
    AcceptedEpistemicStore,
    ActorContext,
    Applicability,
    AuthorityError,
    BlindedRendezvous,
    ClaimRecord,
    ContradictionClass,
    EvidenceItem,
    EvidenceTier,
    HypothesisRecord,
    HypothesisStatus,
    OpenQuestionRecord,
    PeerDisposition,
    ResearchBroadcast,
    ResearchMode,
    SharedEpistemicModel,
    SourceIdentity,
    SourceInstance,
    StaleModelRevision,
    TemporalStatus,
    calibrated_confidence,
    classify_claim_conflict,
    collapse_source_identities,
    information_gain_rank,
    reconcile,
)


class Record:
    def __init__(self, version, payload):
        self.version = version
        self.payload = payload


class MemoryBackend:
    def __init__(self):
        self.rows = {}

    def create(self, namespace, project_id, resource_id, payload):
        key = (namespace, project_id, resource_id)
        if key in self.rows:
            raise RuntimeError("exists")
        self.rows[key] = Record(1, payload)
        return self.rows[key]

    def read(self, namespace, project_id, resource_id):
        return self.rows.get((namespace, project_id, resource_id))

    def compare_and_set(self, namespace, project_id, resource_id, *, expected_version, payload):
        key = (namespace, project_id, resource_id)
        current = self.rows[key]
        if current.version != expected_version:
            raise RuntimeError("stale")
        self.rows[key] = Record(current.version + 1, payload)
        return self.rows[key]


def source(source_id, *, content_hash=None, derived_from=()):
    return SourceIdentity(source_id, "vendor", "Vendor", "Doc", "2026-01-01", "1", source_id, content_hash, derived_from)


def evidence(evidence_id, source_id, tier=EvidenceTier.CURRENT_AUTHORITATIVE, *, supports=(), opposes=(), applicability=Applicability()):
    return EvidenceItem(evidence_id, "inst-" + evidence_id, source_id, tier, evidence_id, supports=supports, opposes=opposes, applicability=applicability)


class EpistemicCoordinationTest(unittest.TestCase):
    def test_source_identity_collapses_same_content_hash(self):
        collapsed, aliases = collapse_source_identities((source("s1", content_hash="abc"), source("s2", content_hash="abc")))
        self.assertEqual(len(collapsed), 1)
        self.assertEqual(aliases["s2"], "s1")

    def test_source_identity_collapses_same_lineage(self):
        collapsed, _ = collapse_source_identities((source("s1", derived_from=("root",)), source("s2", derived_from=("root",))))
        self.assertEqual(len(collapsed), 1)

    def test_duplicate_instances_do_not_become_independent_support(self):
        sources = (source("s1", content_hash="abc"), source("s2", content_hash="abc"))
        _, aliases = collapse_source_identities(sources)
        ev = {
            "e1": evidence("e1", "s1"),
            "e2": evidence("e2", "s2"),
        }
        claim = ClaimRecord("c", "feature enabled", "feature", "enabled", evidence_for=("e1", "e2"))
        confidence, independent, _, _, _ = calibrated_confidence(claim, ev, {item.source_identity_id: item for item in sources}, aliases)
        self.assertEqual(independent, 1)
        self.assertLess(confidence, 90)

    def test_independent_support_is_not_agent_vote(self):
        sources = (source("s1", content_hash="a"), source("s2", content_hash="b"))
        _, aliases = collapse_source_identities(sources)
        ev = {"e1": evidence("e1", "s1"), "e2": evidence("e2", "s2")}
        claim = ClaimRecord("c", "feature enabled", "feature", "enabled", evidence_for=("e1", "e2"))
        _, independent, _, _, _ = calibrated_confidence(claim, ev, {item.source_identity_id: item for item in sources}, aliases)
        self.assertEqual(independent, 2)

    def test_temporal_transition_classification(self):
        old = ClaimRecord("old", "F disabled", "F", "disabled", applicability=Applicability(effective_until="2026-01-01T00:00:00Z", temporal_status=TemporalStatus.HISTORICAL))
        new = ClaimRecord("new", "F enabled", "F", "enabled", applicability=Applicability(effective_from="2026-01-01T00:00:00Z", temporal_status=TemporalStatus.CURRENT))
        self.assertEqual(classify_claim_conflict(old, new), ContradictionClass.TEMPORAL_TRANSITION)

    def test_version_environment_and_deployment_are_contextual(self):
        base = ClaimRecord("a", "F disabled", "F", "disabled", applicability=Applicability(software_version="1", environment="DEV", deployment_id="d1"))
        self.assertEqual(classify_claim_conflict(base, ClaimRecord("b", "F enabled", "F", "enabled", applicability=Applicability(software_version="2", environment="DEV", deployment_id="d1"))), ContradictionClass.VERSION_DIFFERENCE)
        self.assertEqual(classify_claim_conflict(base, ClaimRecord("b", "F enabled", "F", "enabled", applicability=Applicability(software_version="1", environment="PROD", deployment_id="d1"))), ContradictionClass.ENVIRONMENT_DIFFERENCE)
        self.assertEqual(classify_claim_conflict(base, ClaimRecord("b", "F enabled", "F", "enabled", applicability=Applicability(software_version="1", environment="DEV", deployment_id="d2"))), ContradictionClass.DEPLOYMENT_CUSTOMIZATION)

    def test_unscoped_disagreement_stays_true_contradiction(self):
        a = ClaimRecord("a", "F disabled", "F", "disabled")
        b = ClaimRecord("b", "F enabled", "F", "enabled")
        self.assertEqual(classify_claim_conflict(a, b), ContradictionClass.TRUE_CONTRADICTION)

    def test_information_gain_frontier(self):
        low = OpenQuestionRecord("low", "low", 1, 1, 10, 1)
        high = OpenQuestionRecord("high", "high", 5, 2, 1, 3)
        self.assertEqual(information_gain_rank((low, high))[0].question_id, "high")

    def test_blinded_rendezvous_blocks_peer_material(self):
        rendezvous = BlindedRendezvous(("a", "b"))
        rendezvous.submit("a", ResearchMode.EXPLORER, {"finding": 1})
        with self.assertRaises(ValueError):
            rendezvous.peer_material()
        rendezvous.submit("b", ResearchMode.SKEPTIC, {"finding": 2})
        self.assertEqual(len(rendezvous.open()), 2)
        rendezvous.classify_peer("a", "b", PeerDisposition.CONTRADICT)

    def test_first_pass_is_immutable(self):
        rendezvous = BlindedRendezvous(("a",), threshold=1)
        rendezvous.submit("a", ResearchMode.EXPLORER, {"x": 1})
        with self.assertRaises(ValueError):
            rendezvous.submit("a", ResearchMode.EXPLORER, {"x": 2})

    def test_broadcast_never_conveys_authority(self):
        with self.assertRaises(AuthorityError):
            ResearchBroadcast("m", "p", "DISCOVERY_BROADCAST", "RESEARCH", "a", "finding", authority_conveyed=True)

    def test_reconciliation_dedups_reclassifies_and_changes_peer_conclusion(self):
        sources = (
            source("target", content_hash="target"),
            source("vendor", content_hash="vendor"),
            source("mirror", derived_from=("vendor-root",)),
            source("mirror2", derived_from=("vendor-root",)),
            source("history", content_hash="history"),
        )
        target_app = Applicability(environment="PROD", software_version="2026.5", deployment_id="target", effective_from="2026-01-01T00:00:00Z", temporal_status=TemporalStatus.CURRENT)
        default_app = Applicability(software_version="2026.5", temporal_status=TemporalStatus.CURRENT)
        history_app = Applicability(software_version="2025", effective_until="2026-01-01T00:00:00Z", temporal_status=TemporalStatus.HISTORICAL)
        ev = (
            evidence("e-target", "target", EvidenceTier.DIRECT_CURRENT_OPERATIONAL, supports=("c-target",), applicability=target_app),
            evidence("e-vendor", "vendor", EvidenceTier.CURRENT_AUTHORITATIVE, supports=("c-default",), applicability=default_app),
            evidence("e-mirror", "mirror", EvidenceTier.CURRENT_AUTHORITATIVE, supports=("c-default",), applicability=default_app),
            evidence("e-history", "history", EvidenceTier.HISTORICAL_AUTHORITATIVE, supports=("c-history",), applicability=history_app),
        )
        claims = (
            ClaimRecord("c-target", "F is enabled in target PROD 2026.5", "F-target", "enabled", evidence_for=("e-target",), applicability=target_app),
            ClaimRecord("c-default", "F is disabled by current product default", "F-default", "disabled", evidence_for=("e-vendor", "e-mirror"), applicability=default_app),
            ClaimRecord("c-history", "F was disabled in 2025", "F-target", "disabled", evidence_for=("e-history",), applicability=history_app, minority_finding=True),
        )
        hypotheses = (
            HypothesisRecord("h-default", "target enabled because product default changed", 60, opposing_claims=("c-default",)),
            HypothesisRecord("h-override", "target enabled because deployment override differs", 60, supporting_claims=("c-target", "c-default")),
        )
        instances = tuple(SourceInstance("i-" + item.source_identity_id, item.source_identity_id, item.source_identity_id) for item in sources)
        result = reconcile(SharedEpistemicModel("p", sources=sources, source_instances=instances, evidence=ev, claims=claims, hypotheses=hypotheses), previous_synthesis="F is probably generally enabled", peer_evidence_arrived=True)
        self.assertEqual(result.model.telemetry.conclusions_changed_after_peer_evidence, 1)
        self.assertGreaterEqual(result.model.telemetry.source_instances_collapsed, 1)
        self.assertGreaterEqual(result.model.telemetry.temporal_conflicts_reclassified, 1)
        self.assertEqual(result.model.hypotheses[0].status, HypothesisStatus.FALSIFIED)
        self.assertEqual(result.model.hypotheses[1].status, HypothesisStatus.SUPPORTED)
        self.assertEqual(result.model.telemetry.minority_findings_preserved, 1)

    def test_only_primary_can_accept_shared_model(self):
        store = AcceptedEpistemicStore(MemoryBackend())
        model = SharedEpistemicModel("p", generation=1)
        with self.assertRaises(AuthorityError):
            store.accept(ActorContext("p", "MANAGER", "m", frozenset({"WRITE_ACCEPTED_STATE"})), model, expected_version=None, event_id="e1")
        accepted = store.accept(ActorContext("p", "PRIMARY", "p1", frozenset({"WRITE_ACCEPTED_STATE"})), model, expected_version=None, event_id="e1")
        self.assertEqual(accepted.version, 1)
        self.assertFalse(accepted.payload["authority"])

    def test_accepted_store_idempotency_and_stale_writer(self):
        backend = MemoryBackend()
        store = AcceptedEpistemicStore(backend)
        primary = ActorContext("p", "PRIMARY", "p1", frozenset({"WRITE_ACCEPTED_STATE"}))
        model1 = SharedEpistemicModel("p", generation=1)
        store.accept(primary, model1, expected_version=None, event_id="e1")
        self.assertEqual(store.accept(primary, model1, expected_version=1, event_id="e1"), "IDEMPOTENT")
        with self.assertRaises(StaleModelRevision):
            store.accept(primary, SharedEpistemicModel("p", generation=2), expected_version=0, event_id="e2")

    def test_new_schemas_are_closed_and_authority_free(self):
        broadcast = json.loads((ROOT / "schemas/research_epistemic_broadcast.schema.json").read_text())
        checkpoint = json.loads((ROOT / "schemas/swarm_stage_checkpoint_v3.schema.json").read_text())
        self.assertFalse(broadcast["additionalProperties"])
        self.assertEqual(broadcast["properties"]["authority_conveyed"]["const"], False)
        self.assertFalse(checkpoint["additionalProperties"])
        self.assertEqual(checkpoint["properties"]["authority_conveyed"]["const"], False)
        self.assertIn("epistemic", checkpoint["required"])


if __name__ == "__main__":
    unittest.main()
