from epistemic_test_support import *


class CoordinationAndTelemetryTests(unittest.TestCase):
    def test_claim_supersession(self):
        c = ClaimRecord("old", "old", "k", "x", superseded_by="new")
        out = reconcile(mdl(claims=(c,))).model.claims[0]
        self.assertEqual(out.status, ClaimStatus.SUPERSEDED)

    def test_hypothesis_falsification(self):
        s = src("s", h="x"); e = ev("e", "s", EvidenceTier.DIRECT_CURRENT_OPERATIONAL, supports=("opp",))
        c = ClaimRecord("opp", "Opposes H", "k", "v", evidence_for=("e",)); h = HypothesisRecord("h", "H", 70, opposing_claims=("opp",))
        out = reconcile(mdl(sources=(s,), evidence=(e,), claims=(c,), hypotheses=(h,))).model.hypotheses[0]
        self.assertEqual(out.status, HypothesisStatus.FALSIFIED); self.assertLessEqual(out.probability_or_confidence, 15)

    def test_hypothesis_support(self):
        s = src("s", h="x"); e = ev("e", "s", EvidenceTier.DIRECT_CURRENT_OPERATIONAL, supports=("sup",)); c = ClaimRecord("sup", "S", "k", "v", evidence_for=("e",)); h = HypothesisRecord("h", "H", 55, supporting_claims=("sup",))
        out = reconcile(mdl(sources=(s,), evidence=(e,), claims=(c,), hypotheses=(h,))).model.hypotheses[0]
        self.assertEqual(out.status, HypothesisStatus.SUPPORTED); self.assertGreaterEqual(out.probability_or_confidence, 80)

    def test_blinded_first_pass_isolation(self):
        r = BlindedRendezvous("r", ["a", "b", "c"]); r.submit(FirstPassSubmission("a", ResearchMode.EXPLORER, "d", ("c",), ("e",), NOW))
        self.assertEqual(r.peer_material("a"), ())

    def test_rendezvous_threshold_and_peer_review(self):
        r = BlindedRendezvous("r", ["a", "b", "c"], 2)
        for lane in ("a", "b"): r.submit(FirstPassSubmission(lane, ResearchMode.EXPLORER, lane, (), (), NOW))
        self.assertEqual(len(r.open()), 2); self.assertEqual(len(r.peer_material("a")), 1)
        r.classify_peer("a", "b", PeerDisposition.CONTRADICT)

    def test_rendezvous_force_timeout(self):
        r = BlindedRendezvous("r", ["a", "b", "c"]); r.submit(FirstPassSubmission("a", ResearchMode.EXPLORER, "d", (), (), NOW))
        self.assertEqual(len(r.open(force_timeout=True)), 1)

    def test_first_pass_immutable(self):
        r = BlindedRendezvous("r", ["a"]); x = FirstPassSubmission("a", ResearchMode.EXPLORER, "d", (), (), NOW); r.submit(x)
        self.assertEqual(r.submit(x), "IDEMPOTENT")
        with self.assertRaises(EpistemicError): r.submit(replace(x, result_digest="z"))

    def test_peer_classification_requires_open(self):
        r = BlindedRendezvous("r", ["a", "b"], 1)
        with self.assertRaises(EpistemicError): r.classify_peer("a", "b", PeerDisposition.SUPPORT)

    def test_broadcast_runtime_matches_schema(self):
        schema = json.loads((ROOT / "schemas/research_epistemic_broadcast.schema.json").read_text())
        broadcast = ResearchBroadcast("m", "p", "DISCOVERY_BROADCAST", "RESEARCH", "agent-1", "finding", ("s",), ("i",), (1, 3), claims_affected=("c",), confidence=80)
        Draft202012Validator(schema).validate(broadcast.to_payload())

    def test_broadcast_never_authority(self):
        with self.assertRaises(AuthorityError): ResearchBroadcast("m", "p", "DISCOVERY_BROADCAST", "RESEARCH", "a", "x", authority_conveyed=True)

    def test_broadcast_rejects_primary_role(self):
        with self.assertRaises(EpistemicError): ResearchBroadcast("m", "p", "DISCOVERY_BROADCAST", "PRIMARY", "a", "x")

    def test_broadcast_requires_existing_coordination_permit(self):
        b = ResearchBroadcast("m", "p", "DISCOVERY_BROADCAST", "RESEARCH", "a", "x")
        self.assertTrue(require_existing_coordination_permit(b, Permit("p", "RESEARCH")))
        with self.assertRaises(AuthorityError): require_existing_coordination_permit(b, Permit("other", "RESEARCH"))

    def test_information_gain_ranking(self):
        q1 = OpenQuestionRecord("q1", "high", 2, 2, 1, 5); q2 = OpenQuestionRecord("q2", "low", 1, 1, 5, 1)
        self.assertEqual(information_gain_rank([q2, q1])[0].question_id, "q1")

    def test_duplicate_penalty_can_redirect_frontier(self):
        q1 = OpenQuestionRecord("q1", "duplicate", 2, 2, 1, 5); q2 = OpenQuestionRecord("q2", "fresh", 2, 2, 2, 4)
        self.assertEqual(information_gain_rank([q1, q2], {"q1": .9})[0].question_id, "q2")

    def test_minority_finding_preserved(self):
        c = ClaimRecord("m", "minority", "k", "v", minority_finding=True)
        m = reconcile(mdl(claims=(c,))).model
        self.assertEqual(m.telemetry.minority_findings_preserved, 1)

    def test_model_revision_lineage_monotonic(self):
        r = reconcile(mdl(generation=7, parent=6)).model
        self.assertEqual((r.parent_generation, r.generation), (7, 8))

    def test_peer_evidence_metric_is_counterfactual_not_boolean(self):
        s = src("s", h="x")
        e = ev("peer", "s", EvidenceTier.DIRECT_CURRENT_OPERATIONAL, supports=("c",), originating_agent="peer-agent")
        c = ClaimRecord("c", "peer-supported conclusion", "k", "v", evidence_for=("peer",))
        r = reconcile(mdl(sources=(s,), evidence=(e,), claims=(c,)), peer_evidence_ids=("peer",))
        self.assertTrue(r.peer_changed_conclusion); self.assertEqual(r.model.telemetry.conclusions_changed_after_peer_evidence, 1)

    def test_irrelevant_peer_evidence_gets_no_change_credit(self):
        s1, s2 = src("s1", h="1"), src("s2", h="2")
        e1 = ev("base", "s1", EvidenceTier.DIRECT_CURRENT_OPERATIONAL, supports=("c",), originating_agent="base")
        e2 = ev("peer", "s2", EvidenceTier.CURRENT_AUTHORITATIVE, originating_agent="peer")
        c = ClaimRecord("c", "stable", "k", "v", evidence_for=("base",))
        r = reconcile(mdl(sources=(s1, s2), evidence=(e1, e2), claims=(c,)), peer_evidence_ids=("peer",))
        self.assertFalse(r.peer_changed_conclusion); self.assertEqual(r.model.telemetry.conclusions_changed_after_peer_evidence, 0)

