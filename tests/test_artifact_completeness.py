import unittest

from org_agent_mesh.artifact_completeness import ArtifactCompletenessError, ArtifactReadinessCheck, Readiness


class ArtifactCompletenessTests(unittest.TestCase):
    def test_unresolved_placeholder_blocks_ready(self):
        check = ArtifactReadinessCheck(
            rendered_text="Submit value [PASTE VALUE]",
            mandatory_fields={"case": "CASE-1"},
            identifiers_current=True,
            final_render_validated=True,
        )
        with self.assertRaisesRegex(ArtifactCompletenessError, "UNRESOLVED_PLACEHOLDERS"):
            check.validate_ready(Readiness.READY_TO_SUBMIT)

    def test_missing_required_field_blocks_ready(self):
        check = ArtifactReadinessCheck(
            rendered_text="Complete payload",
            mandatory_fields={"case": "CASE-1", "review": ""},
            identifiers_current=True,
            final_render_validated=True,
        )
        with self.assertRaisesRegex(ArtifactCompletenessError, "MANDATORY_FIELDS_MISSING"):
            check.validate_ready(Readiness.READY_TO_USE)

    def test_outstanding_human_input_blocks_ready(self):
        check = ArtifactReadinessCheck(
            rendered_text="Complete payload",
            mandatory_fields={"case": "CASE-1"},
            identifiers_current=True,
            final_render_validated=True,
            human_input_outstanding=("enter value through designated UI",),
        )
        with self.assertRaisesRegex(ArtifactCompletenessError, "HUMAN_INPUT_STILL_REQUIRED"):
            check.validate_ready(Readiness.READY_TO_SUBMIT)

    def test_complete_final_render_passes(self):
        check = ArtifactReadinessCheck(
            rendered_text="Complete payload CASE-1",
            mandatory_fields={"case": "CASE-1"},
            identifiers_current=True,
            final_render_validated=True,
        )
        check.validate_ready(Readiness.READY_TO_SUBMIT)


if __name__ == "__main__":
    unittest.main()
