from epistemic_test_support import *


class AuthorityAndSchemaTests(unittest.TestCase):
    def test_peer_evidence_requires_originating_agent(self):
        s = src("s", h="x"); e = ev("peer", "s", supports=("c",)); c = ClaimRecord("c", "x", "k", "v", evidence_for=("peer",))
        with self.assertRaises(EpistemicError): reconcile(mdl(sources=(s,), evidence=(e,), claims=(c,)), peer_evidence_ids=("peer",))

    def test_primary_only_accepted_state_uses_required_canonical_callback(self):
        store = AcceptedEpistemicStore(FakeBackend(), require_session=canonical_require_session); m = mdl(generation=1, parent=0)
        with self.assertRaises(AuthorityError): store.accept(Session("p", "RESEARCH", frozenset({"WRITE_ACCEPTED_STATE"})), m, expected_version=0, event_id="e")

    def test_accepted_store_rejects_missing_canonical_callback(self):
        with self.assertRaises(TypeError): AcceptedEpistemicStore(FakeBackend(), require_session=None)

    def test_project_isolation(self):
        store = AcceptedEpistemicStore(FakeBackend(), require_session=canonical_require_session)
        with self.assertRaises(AuthorityError): store.accept(Session("a", "PRIMARY", frozenset({"WRITE_ACCEPTED_STATE"})), mdl(project="b", generation=1, parent=0), expected_version=0, event_id="e")

    def test_idempotent_replay_precedes_stale_version_rejection(self):
        store = AcceptedEpistemicStore(FakeBackend(), require_session=canonical_require_session); actor = Session("p", "PRIMARY", frozenset({"WRITE_ACCEPTED_STATE"})); m = mdl(generation=1, parent=0)
        rec = store.accept(actor, m, expected_version=0, event_id="e"); self.assertEqual(rec.version, 1)
        self.assertEqual(store.accept(actor, m, expected_version=0, event_id="e"), "IDEMPOTENT")

    def test_event_collision_rejected_even_on_replay(self):
        store = AcceptedEpistemicStore(FakeBackend(), require_session=canonical_require_session); actor = Session("p", "PRIMARY", frozenset({"WRITE_ACCEPTED_STATE"}))
        store.accept(actor, mdl(generation=1, parent=0), expected_version=0, event_id="e")
        with self.assertRaises(EpistemicError): store.accept(actor, mdl(generation=2, parent=1), expected_version=0, event_id="e")

    def test_stale_writer_rejected(self):
        store = AcceptedEpistemicStore(FakeBackend(), require_session=canonical_require_session); actor = Session("p", "PRIMARY", frozenset({"WRITE_ACCEPTED_STATE"}))
        store.accept(actor, mdl(generation=1, parent=0), expected_version=0, event_id="e1")
        with self.assertRaises(StaleModelRevision): store.accept(actor, mdl(generation=2, parent=1), expected_version=0, event_id="e2")

    def test_generation_must_increase(self):
        store = AcceptedEpistemicStore(FakeBackend(), require_session=canonical_require_session); actor = Session("p", "PRIMARY", frozenset({"WRITE_ACCEPTED_STATE"})); m = mdl(generation=1, parent=0)
        store.accept(actor, m, expected_version=0, event_id="e1")
        with self.assertRaises(StaleModelRevision): store.accept(actor, m, expected_version=1, event_id="e2")

    def test_checkpoint_v3_is_closed_and_delta_based(self):
        schema = json.loads((ROOT / "schemas/swarm_stage_checkpoint_v3.schema.json").read_text())
        self.assertFalse(schema["additionalProperties"]); self.assertIn("epistemic", schema["required"]); self.assertNotIn("claims", schema["properties"]["epistemic"]["properties"])

    def test_checkpoint_v3_preserves_v2_stage_state_semantics(self):
        schema = json.loads((ROOT / "schemas/swarm_stage_checkpoint_v3.schema.json").read_text())
        validator = Draft202012Validator(schema)
        payload = {
            "schema": "intercommunications/swarm-stage-checkpoint/v3", "project_id": "p", "authority_conveyed": False,
            "checkpoint_id": "c", "cycle_id": "2026-10-06T12:00:00-07:00", "stage": "RESEARCHER_1", "run_id": "r",
            "sequence": 0, "state": "PRIMARY_PROGRESS", "phase": "x", "trigger": "SCHEDULED", "created_at": NOW,
            "source_revisions": {}, "upstream_checkpoint_ids": [], "evidence_refs": [], "summary": "", "blockers": [],
            "unfinished_work": [], "next_action": "x", "epistemic": {"reconciliation_generation": 0, "epistemic_delta_refs": [],
            "claims_created_or_updated": [], "hypotheses_created_or_updated": [], "contradiction_refs": [], "source_identity_refs": [],
            "duplicate_source_collapse_refs": [], "pending_verification_refs": [], "minority_finding_refs": [], "unresolved_high_impact_question_refs": []}
        }
        with self.assertRaises(ValidationError): validator.validate(payload)

    def test_checkpoint_v3_preserves_interactive_recovery_requirement(self):
        schema = json.loads((ROOT / "schemas/swarm_stage_checkpoint_v3.schema.json").read_text()); validator = Draft202012Validator(schema)
        payload = {
            "schema": "intercommunications/swarm-stage-checkpoint/v3", "project_id": "p", "authority_conveyed": False,
            "checkpoint_id": "c", "cycle_id": "2026-10-06T12:00:00-07:00", "stage": "PRIMARY", "run_id": "r",
            "sequence": 0, "state": "PRIMARY_PROGRESS", "phase": "x", "trigger": "USER_INTERACTIVE", "created_at": NOW,
            "source_revisions": {}, "upstream_checkpoint_ids": [], "evidence_refs": [], "summary": "", "blockers": [],
            "unfinished_work": [], "next_action": "x", "epistemic": {"reconciliation_generation": 0, "epistemic_delta_refs": [],
            "claims_created_or_updated": [], "hypotheses_created_or_updated": [], "contradiction_refs": [], "source_identity_refs": [],
            "duplicate_source_collapse_refs": [], "pending_verification_refs": [], "minority_finding_refs": [], "unresolved_high_impact_question_refs": []}
        }
        with self.assertRaises(ValidationError): validator.validate(payload)

    def test_new_schemas_are_draft_2020_12_valid(self):
        for name in ("research_epistemic_broadcast.schema.json", "swarm_stage_checkpoint_v3.schema.json"):
            Draft202012Validator.check_schema(json.loads((ROOT / "schemas" / name).read_text()))

    def test_reconciliation_cancels_resolved_question_advisory(self):
        q = OpenQuestionRecord("q", "done", 1, 1, 1, 1, status="RESOLVED"); r = reconcile(mdl(open_questions=(q,)))
        self.assertEqual(r.cancelled_question_ids, ("q",)); self.assertEqual(r.model.telemetry.tasks_cancelled_after_reconciliation, 1)

    def test_source_instance_collapse_telemetry(self):
        ss = (src("a", h="same"), src("b", h="same")); ii = (SourceInstance("i1", "a", "one"), SourceInstance("i2", "b", "two"))
        m = reconcile(mdl(sources=ss, source_instances=ii)).model
        self.assertEqual(m.telemetry.unique_source_origins, 1); self.assertEqual(m.telemetry.source_instances_collapsed, 1)

    def test_reconciliation_persists_revision_records(self):
        m = reconcile(mdl()).model
        self.assertEqual(len(m.model_revisions), 1); self.assertEqual(len(m.reconciliations), 1)

    def test_accepted_store_uses_injected_backend_not_second_database(self):
        backend = FakeBackend(); store = AcceptedEpistemicStore(backend, require_session=canonical_require_session)
        self.assertIs(store.backend, backend); self.assertEqual(store.NAMESPACE, "epistemic-model")

    def test_recovery_after_partial_reconciliation_is_deterministic(self):
        s = src("s", h="x"); e = ev("e", "s", supports=("c",)); c = ClaimRecord("c", "x", "k", "v", evidence_for=("e",)); base = mdl(sources=(s,), evidence=(e,), claims=(c,))
        a = reconcile(base).model; b = reconcile(base).model
        self.assertEqual(a.claims, b.claims); self.assertEqual(a.telemetry, b.telemetry); self.assertEqual(a.sources, b.sources)

