import unittest
from datetime import datetime, timezone

from org_agent_mesh.handoff_security_controls import (
    ActionableLink,
    BreakGlassTokenBinding,
    CompletionAssessment,
    CompletionState,
    HandoffEnvelope,
    LinkStatus,
    SecurityControlError,
    require_all_controls,
)


class HandoffSecurityControlTests(unittest.TestCase):
    def test_handoff_cannot_convey_authority(self):
        handoff = HandoffEnvelope(
            handoff_id="H-1",
            project_id="intercommunicationsenhancements",
            source_agent_id="manager-1",
            source_agent_role="MANAGER",
            target_agent_id="manager-2",
            target_agent_role="MANAGER",
            canonical_project_revision="abc123",
            authority_conveyed=True,
        )
        with self.assertRaisesRegex(SecurityControlError, "HANDOFF_MAY_NOT_CONVEY_EXECUTION_AUTHORITY"):
            handoff.validate(expected_project_id="intercommunicationsenhancements")

    def test_handoff_rejects_project_mismatch(self):
        handoff = HandoffEnvelope(
            handoff_id="H-2",
            project_id="project-a",
            source_agent_id="research-1",
            source_agent_role="RESEARCH",
            target_agent_id="research-2",
            target_agent_role="RESEARCH",
            canonical_project_revision="rev-1",
        )
        with self.assertRaisesRegex(SecurityControlError, "PROJECT_MISMATCH"):
            handoff.validate(expected_project_id="project-b")

    def make_break_glass(self, raw_token="emergency-token"):
        return BreakGlassTokenBinding(
            token_id="bg-1",
            token_digest=BreakGlassTokenBinding.digest_token(raw_token),
            principal_id="robert_leonard",
            project_id="intercommunicationsenhancements",
            target_scope="main",
            action_digest="sha256:action",
            consequence_class="SECURITY_OR_CREDENTIAL_BOUNDARY_CHANGE",
            issued_at_utc="2026-10-05T17:00:00Z",
            expires_at_utc="2026-10-05T17:30:00Z",
        )

    def test_break_glass_requires_normal_security_controls(self):
        token = self.make_break_glass()
        with self.assertRaisesRegex(SecurityControlError, "NORMAL_SECURITY_CONTROLS_NOT_SATISFIED"):
            token.validate(
                raw_token="emergency-token",
                now=datetime(2026, 10, 5, 17, 10, tzinfo=timezone.utc),
                principal_id="robert_leonard",
                project_id="intercommunicationsenhancements",
                target_scope="main",
                action_digest="sha256:action",
                consequence_class="SECURITY_OR_CREDENTIAL_BOUNDARY_CHANGE",
                normal_security_controls_ok=False,
            )

    def test_break_glass_requires_valid_fresh_token(self):
        token = self.make_break_glass()
        with self.assertRaisesRegex(SecurityControlError, "BREAK_GLASS_TOKEN_INVALID"):
            token.validate(
                raw_token="wrong-token",
                now=datetime(2026, 10, 5, 17, 10, tzinfo=timezone.utc),
                principal_id="robert_leonard",
                project_id="intercommunicationsenhancements",
                target_scope="main",
                action_digest="sha256:action",
                consequence_class="SECURITY_OR_CREDENTIAL_BOUNDARY_CHANGE",
                normal_security_controls_ok=True,
            )
        with self.assertRaisesRegex(SecurityControlError, "BREAK_GLASS_TOKEN_EXPIRED"):
            token.validate(
                raw_token="emergency-token",
                now=datetime(2026, 10, 5, 17, 31, tzinfo=timezone.utc),
                principal_id="robert_leonard",
                project_id="intercommunicationsenhancements",
                target_scope="main",
                action_digest="sha256:action",
                consequence_class="SECURITY_OR_CREDENTIAL_BOUNDARY_CHANGE",
                normal_security_controls_ok=True,
            )

    def test_break_glass_token_is_scope_bound(self):
        token = self.make_break_glass()
        with self.assertRaisesRegex(SecurityControlError, "TARGET_SCOPE_MISMATCH"):
            token.validate(
                raw_token="emergency-token",
                now=datetime(2026, 10, 5, 17, 10, tzinfo=timezone.utc),
                principal_id="robert_leonard",
                project_id="intercommunicationsenhancements",
                target_scope="other",
                action_digest="sha256:action",
                consequence_class="SECURITY_OR_CREDENTIAL_BOUNDARY_CHANGE",
                normal_security_controls_ok=True,
            )

    def test_verified_download_requires_verification_timestamp(self):
        link = ActionableLink(
            url="https://github.com/example/repo/releases/download/v1/file.zip",
            status=LinkStatus.VERIFIED_DOWNLOAD,
            target_id="artifact-1",
            project_id="intercommunicationsenhancements",
        )
        with self.assertRaisesRegex(SecurityControlError, "VERIFIED_LINK_REQUIRES_VERIFICATION_TIMESTAMP"):
            link.validate_for_presentation()

    def test_security_token_may_not_be_embedded_in_url(self):
        link = ActionableLink(
            url="https://github.com/example/repo/issues/new?security_token=secret",
            status=LinkStatus.UNVERIFIED_DIRECT,
            target_id="issue-new",
            project_id="intercommunicationsenhancements",
        )
        with self.assertRaisesRegex(SecurityControlError, "SECRET_MATERIAL_IN_URL"):
            link.validate_for_presentation()

    def test_verified_direct_link_passes_when_bound_and_timestamped(self):
        link = ActionableLink(
            url="https://github.com/example/repo/issues/35",
            status=LinkStatus.VERIFIED_DIRECT,
            target_id="issue-35",
            project_id="intercommunicationsenhancements",
            verified_at_utc="2026-10-05T17:22:45Z",
        )
        link.validate_for_presentation()

    def test_required_controls_fail_closed(self):
        with self.assertRaisesRegex(SecurityControlError, "MISSING_REQUIRED_CONTROLS:B"):
            require_all_controls(["A", "B"], ["A"])

    def test_completion_is_blocked_by_known_avoidable_residue(self):
        assessment = CompletionAssessment(
            objective_verified=True,
            known_avoidable_residue=("accidental_issue",),
            remediation_authorized_and_possible=True,
        )
        self.assertEqual(assessment.state(), CompletionState.INCOMPLETE_REMEDIATION_REQUIRED)
        with self.assertRaisesRegex(SecurityControlError, "COMPLETION_INTEGRITY_BLOCKED"):
            assessment.require_complete()

    def test_completion_reports_blocked_when_cleanup_needs_authority(self):
        assessment = CompletionAssessment(
            objective_verified=True,
            known_avoidable_residue=("external_cleanup",),
            remediation_authorized_and_possible=False,
        )
        self.assertEqual(assessment.state(), CompletionState.INCOMPLETE_BLOCKED)

    def test_completion_passes_after_cleanup(self):
        assessment = CompletionAssessment(objective_verified=True)
        self.assertEqual(assessment.state(), CompletionState.COMPLETE)
        assessment.require_complete()


if __name__ == "__main__":
    unittest.main()
