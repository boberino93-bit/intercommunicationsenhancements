from epistemic_test_support import *


class SourcesAndReconciliationTests(unittest.TestCase):
    def test_source_identity_vs_instance(self):
        i1 = SourceInstance("i1", "s1", "repo.pdf"); i2 = SourceInstance("i2", "s1", "email.pdf")
        self.assertNotEqual(i1.source_instance_id, i2.source_instance_id)
        self.assertEqual(i1.source_identity_id, i2.source_identity_id)

    def test_duplicate_source_collapse_by_hash(self):
        collapsed, alias = collapse_source_identities([src("a", h="deadbeef"), src("b", h="deadbeef")])
        self.assertEqual(len(collapsed), 1); self.assertEqual(alias["b"], "a"); self.assertEqual(alias["a"], "a")

    def test_duplicate_source_collapse_by_external_lineage(self):
        collapsed, _ = collapse_source_identities([src("a", derived=("origin-x",)), src("b", derived=("origin-x",))])
        self.assertEqual(len(collapsed), 1)

    def test_transitive_source_lineage_collapses_to_root(self):
        root = src("root", h="abc")
        mirror = src("mirror", derived=("root",))
        mirror2 = src("mirror2", derived=("mirror",))
        collapsed, alias = collapse_source_identities([root, mirror, mirror2])
        self.assertEqual([item.source_identity_id for item in collapsed], ["root"])
        self.assertEqual(alias["mirror2"], "root")

    def test_source_lineage_cycle_fails_closed(self):
        with self.assertRaises(EpistemicError):
            collapse_source_identities([src("a", derived=("b",)), src("b", derived=("a",))])

    def test_provenance_rejects_dangling_instance(self):
        s = src("s", h="x")
        with self.assertRaises(EpistemicError):
            validate_model_provenance(mdl(sources=(s,), source_instances=(SourceInstance("i", "missing", "x"),)))

    def test_provenance_rejects_evidence_instance_identity_mismatch(self):
        s1, s2 = src("s1", h="1"), src("s2", h="2")
        e = EvidenceItem("e", "i", "s1", EvidenceTier.CURRENT_AUTHORITATIVE, "x")
        m = mdl(sources=(s1, s2), evidence=(e,), source_instances=(SourceInstance("i", "s2", "x"),))
        with self.assertRaises(EpistemicError): validate_model_provenance(m)

    def test_provenance_rejects_claim_unknown_evidence(self):
        c = ClaimRecord("c", "X", "x", "yes", evidence_for=("missing",))
        with self.assertRaises(EpistemicError): reconcile(mdl(claims=(c,)))

    def test_reconciliation_canonicalizes_source_references(self):
        a, b = src("a", h="same"), src("b", h="same")
        e = ev("e", "b", supports=("c",))
        c = ClaimRecord("c", "X", "x", "yes", evidence_for=("e",))
        out = reconcile(mdl(sources=(a, b), evidence=(e,), claims=(c,))).model
        self.assertEqual([s.source_identity_id for s in out.sources], ["a"])
        self.assertEqual(out.source_instances[0].source_identity_id, "a")
        self.assertEqual(out.evidence[0].source_identity_id, "a")

    def test_independent_support_not_agent_vote(self):
        sources = (src("a", h="same"), src("b", h="same"))
        evidence = (ev("e1", "a", supports=("c",)), ev("e2", "b", supports=("c",)))
        c = ClaimRecord("c", "X", "x", "yes", evidence_for=("e1", "e2"))
        r = reconcile(mdl(sources=sources, evidence=evidence, claims=(c,))).model.claims[0]
        self.assertEqual(r.independent_support_count, 1)

    def test_confidence_decreases_when_independence_lost(self):
        independent = (src("a", h="a"), src("b", h="b")); duplicate = (src("a", h="a"), src("b", h="a"))
        evidence = (ev("e1", "a", supports=("c",)), ev("e2", "b", supports=("c",)))
        c = ClaimRecord("c", "X", "x", "yes", evidence_for=("e1", "e2"))
        ci = reconcile(mdl(sources=independent, evidence=evidence, claims=(c,))).model.claims[0].confidence
        cd = reconcile(mdl(sources=duplicate, evidence=evidence, claims=(c,))).model.claims[0].confidence
        self.assertGreater(ci, cd)

    def test_opposing_evidence_lowers_confidence(self):
        ss = (src("a", h="a"), src("b", h="b"))
        ee = (ev("e1", "a", supports=("c",)), ev("e2", "b", opposes=("c",)))
        plain = ClaimRecord("c", "X", "x", "yes", evidence_for=("e1",))
        opposed = replace(plain, evidence_against=("e2",))
        cp = reconcile(mdl(sources=ss, evidence=ee, claims=(plain,))).model.claims[0].confidence
        co = reconcile(mdl(sources=ss, evidence=ee, claims=(opposed,))).model.claims[0].confidence
        self.assertLess(co, cp)

    def test_stale_evidence_penalty(self):
        s = src("a", h="a")
        current = ev("ec", "a", supports=("c1",), applicability=Applicability(temporal_status=TemporalStatus.CURRENT))
        old = ev("eo", "a", supports=("c2",), applicability=Applicability(temporal_status=TemporalStatus.HISTORICAL))
        c1 = ClaimRecord("c1", "X", "x", "yes", evidence_for=("ec",)); c2 = ClaimRecord("c2", "X", "x2", "yes", evidence_for=("eo",))
        m = reconcile(mdl(sources=(s,), evidence=(current, old), claims=(c1, c2))).model
        self.assertGreater(m.claims[0].confidence, m.claims[1].confidence)

    def test_negative_evidence_not_found_is_weaker_than_absent(self):
        s1, s2 = src("a", h="a"), src("b", h="b")
        nf = NegativeEvidence("NOT_FOUND", "config", ("console",), NOW, confidence=90)
        ab = NegativeEvidence("ABSENT", "config", ("console",), NOW, confidence=90)
        e1 = ev("e1", "a", EvidenceTier.DIRECT_CURRENT_OPERATIONAL, supports=("c1",), negative=nf)
        e2 = ev("e2", "b", EvidenceTier.DIRECT_CURRENT_OPERATIONAL, supports=("c2",), negative=ab)
        c1 = ClaimRecord("c1", "not found", "k1", "absent", evidence_for=("e1",))
        c2 = ClaimRecord("c2", "absent", "k2", "absent", evidence_for=("e2",))
        out = reconcile(mdl(sources=(s1, s2), evidence=(e1, e2), claims=(c1, c2))).model
        self.assertLess(out.claims[0].confidence, out.claims[1].confidence)
        self.assertLessEqual(out.claims[0].confidence, 60)

    def test_negative_evidence_rejects_bad_kind(self):
        with self.assertRaises(EpistemicError): NegativeEvidence("NOPE", "x", ("a",), NOW)

    def test_negative_evidence_requires_surface_tuple(self):
        with self.assertRaises(EpistemicError): NegativeEvidence("NOT_FOUND", "x", "console", NOW)

    def test_temporal_transition_not_true_contradiction(self):
        a = ClaimRecord("a", "disabled", "f", "disabled", applicability=Applicability(effective_until="2025-12-31T23:59:59Z"))
        b = ClaimRecord("b", "enabled", "f", "enabled", applicability=Applicability(effective_from="2026-01-01T00:00:00Z"))
        self.assertEqual(classify_claim_conflict(a, b), ContradictionClass.TEMPORAL_TRANSITION)

    def test_version_difference(self):
        a = ClaimRecord("a", "off", "f", "off", applicability=Applicability(software_version="1")); b = ClaimRecord("b", "on", "f", "on", applicability=Applicability(software_version="2"))
        self.assertEqual(classify_claim_conflict(a, b), ContradictionClass.VERSION_DIFFERENCE)

    def test_environment_difference(self):
        a = ClaimRecord("a", "off", "f", "off", applicability=Applicability(environment="DEV")); b = ClaimRecord("b", "on", "f", "on", applicability=Applicability(environment="PROD"))
        self.assertEqual(classify_claim_conflict(a, b), ContradictionClass.ENVIRONMENT_DIFFERENCE)

    def test_configuration_difference(self):
        a = ClaimRecord("a", "off", "f", "off", applicability=Applicability(configuration_profile="default")); b = ClaimRecord("b", "on", "f", "on", applicability=Applicability(configuration_profile="override"))
        self.assertEqual(classify_claim_conflict(a, b), ContradictionClass.CONFIGURATION_DIFFERENCE)

    def test_deployment_difference(self):
        a = ClaimRecord("a", "off", "f", "off", applicability=Applicability(deployment_id="a")); b = ClaimRecord("b", "on", "f", "on", applicability=Applicability(deployment_id="b"))
        self.assertEqual(classify_claim_conflict(a, b), ContradictionClass.DEPLOYMENT_CUSTOMIZATION)

    def test_terminology_difference(self):
        a = ClaimRecord("a", "off", "f", "off", applicability=Applicability(terminology_namespace="vendor")); b = ClaimRecord("b", "on", "f", "on", applicability=Applicability(terminology_namespace="deployment"))
        self.assertEqual(classify_claim_conflict(a, b), ContradictionClass.TERMINOLOGY_DIFFERENCE)

    def test_source_quality_difference(self):
        a = ClaimRecord("a", "off", "f", "off", confidence=85, independent_support_count=1, evidence_tier=EvidenceTier.DIRECT_CURRENT_OPERATIONAL)
        b = ClaimRecord("b", "on", "f", "on", confidence=60, independent_support_count=1, evidence_tier=EvidenceTier.SECONDARY)
        self.assertEqual(classify_claim_conflict(a, b), ContradictionClass.SOURCE_QUALITY_DIFFERENCE)

    def test_incomplete_evidence_difference(self):
        a = ClaimRecord("a", "off", "f", "off", confidence=20, independent_support_count=0)
        b = ClaimRecord("b", "on", "f", "on", confidence=20, independent_support_count=0)
        self.assertEqual(classify_claim_conflict(a, b), ContradictionClass.INCOMPLETE_EVIDENCE)

    def test_true_contradiction_preserved_when_both_supported(self):
        s1, s2 = src("s1", h="1"), src("s2", h="2")
        e1 = ev("e1", "s1", EvidenceTier.DIRECT_CURRENT_OPERATIONAL, supports=("a",))
        e2 = ev("e2", "s2", EvidenceTier.DIRECT_CURRENT_OPERATIONAL, supports=("b",))
        a = ClaimRecord("a", "off", "f", "off", evidence_for=("e1",)); b = ClaimRecord("b", "on", "f", "on", evidence_for=("e2",))
        m = reconcile(mdl(sources=(s1, s2), evidence=(e1, e2), claims=(a, b))).model
        self.assertEqual(m.contradictions[0].classification, ContradictionClass.TRUE_CONTRADICTION)
        self.assertFalse(m.contradictions[0].resolved)

