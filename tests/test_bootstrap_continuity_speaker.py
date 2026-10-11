from datetime import datetime, timezone
import json

import pytest

from org_agent_mesh.bootstrap_continuity import (
    ContinuityRestorationError,
    SpeakerClaimAuditTable,
    SpeakerIdentitySession,
    restore_project_continuity,
)


def test_verified_external_restoration_has_no_authority():
    attestation = restore_project_continuity(
        "intercommunicationsenhancements",
        [
            {
                "source_id": "continuity-record",
                "project_id": "intercommunicationsenhancements",
                "source_class": "EXTERNAL_CANONICAL",
            }
        ],
        required_source_ids=["continuity-record"],
        now=datetime(2026, 10, 11, 4, 20, tzinfo=timezone.utc),
    )
    assert attestation.result == "RESTORED_VERIFIED"
    assert attestation.authority == "NONE"
    assert attestation.mutation_authority is False
    assert attestation.native_memory_used is False


def test_native_memory_source_is_denied():
    with pytest.raises(ContinuityRestorationError, match="native_or_unknown_memory_source_denied"):
        restore_project_continuity(
            "intercommunicationsenhancements",
            [
                {
                    "source_id": "native-memory",
                    "project_id": "intercommunicationsenhancements",
                    "source_class": "NATIVE_MEMORY",
                }
            ],
        )


def test_project_mismatch_is_identity_conflict():
    attestation = restore_project_continuity(
        "intercommunicationsenhancements",
        [
            {
                "source_id": "wrong-project",
                "project_id": "another-project",
                "source_class": "EXTERNAL_CANONICAL",
            }
        ],
    )
    assert attestation.result == "IDENTITY_CONFLICT"
    assert attestation.conflict_source_ids == ("wrong-project",)


def test_missing_required_source_is_preserved_as_missing():
    attestation = restore_project_continuity(
        "intercommunicationsenhancements",
        [],
        required_source_ids=["required-a"],
    )
    assert attestation.result == "CANONICAL_SOURCE_MISSING"
    assert attestation.missing_required_source_ids == ("required-a",)


def test_startup_asks_open_ended_name_question():
    session = SpeakerIdentitySession()
    assert session.startup_prompt() == "What is your name?"
    assert session.active_claim is None


def test_vocal_modulation_invalidates_active_claim_and_reasks(tmp_path):
    table = SpeakerClaimAuditTable(tmp_path / "speaker.jsonl")
    session = SpeakerIdentitySession()
    session.startup_prompt()
    session.bind_claim(
        "First Speaker",
        project_id="intercommunicationsenhancements",
        session_id="session-1",
        audit_table=table,
    )
    assert session.active_claim is not None
    prompt = session.signal_possible_speaker_change(vocal_modulation_changed=True)
    assert prompt == "What is your name?"
    assert session.active_claim is None


def test_speaker_rebind_replaces_active_claim_but_preserves_history(tmp_path):
    path = tmp_path / "speaker.jsonl"
    table = SpeakerClaimAuditTable(path)
    session = SpeakerIdentitySession()

    session.startup_prompt()
    first = session.bind_claim(
        "First Speaker",
        project_id="intercommunicationsenhancements",
        session_id="session-1",
        audit_table=table,
    )
    assert first.status == "CLAIMED_NOT_AUTHENTICATED"

    session.signal_possible_speaker_change(speaker_change_suspected=True)
    second = session.bind_claim(
        "Robert Leonard",
        project_id="intercommunicationsenhancements",
        session_id="session-1",
        audit_table=table,
    )
    assert session.active_claim.claimed_name == "Robert Leonard"
    assert second.authentication_effect == "NONE"
    assert second.authorization_effect == "NONE"
    assert second.authority == "NONE"

    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [row["claimed_name"] for row in rows] == ["First Speaker", "Robert Leonard"]
    assert rows[1]["previous_event_hash"] == rows[0]["event_hash"]
    assert all(row["mutation_authority"] is False for row in rows)
    assert all(row["voice_signal_is_identity_proof"] is False for row in rows)


def test_no_change_signal_does_not_reprompt(tmp_path):
    table = SpeakerClaimAuditTable(tmp_path / "speaker.jsonl")
    session = SpeakerIdentitySession()
    session.startup_prompt()
    session.bind_claim(
        "Robert Leonard",
        project_id="intercommunicationsenhancements",
        session_id="session-1",
        audit_table=table,
    )
    assert session.signal_possible_speaker_change() is None
    assert session.active_claim.claimed_name == "Robert Leonard"
