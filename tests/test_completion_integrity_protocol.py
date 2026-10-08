from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] if (Path(__file__).resolve().parent.name == 'tests') else Path(__file__).resolve().parent
PROTOCOL = ROOT / 'protocols' / 'completion_integrity.md'


class CompletionIntegrityProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = PROTOCOL.read_text(encoding='utf-8')

    def test_version_and_scope_are_universal(self):
        self.assertIn('Version: 1.1.0', self.text)
        self.assertIn('Status: ACTIVE HARD GATE', self.text)
        self.assertIn('Scope: UNIVERSAL / ALL PROJECTS / ALL AGENTS', self.text)

    def test_preparation_and_intent_are_not_completion(self):
        self.assertIn('Never substitute preparation for execution.', self.text)
        self.assertIn('Never substitute intent for verified completion.', self.text)
        self.assertIn('drafted != attached', self.text)
        self.assertIn('handoff != downstream completion', self.text)
        self.assertIn('tool success != verified postcondition', self.text)

    def test_requested_end_state_requires_action_reconciliation(self):
        self.assertIn("reconstruct the user's original requested end-state", self.text)
        for state in (
            'EXECUTED_VERIFIED',
            'BLOCKED',
            'NOT_AUTHORIZED',
            'TOOL_OR_ACCESS_UNAVAILABLE',
        ):
            self.assertIn(state, self.text)

    def test_external_mutation_requires_execution_evidence(self):
        self.assertIn('Any externally durable action counts as completed only when the canonical action actually succeeds', self.text)
        self.assertIn('commit SHA', self.text)
        self.assertIn('read-back of the resulting state', self.text)
        self.assertIn('postcondition check', self.text)

    def test_partial_completion_is_first_class(self):
        self.assertIn('`PARTIALLY_COMPLETE`', self.text)
        self.assertIn('materially requested downstream action is knowingly outstanding', self.text)

    def test_completion_pressure_cannot_expand_authority(self):
        self.assertIn('This directive does not expand authority.', self.text)
        self.assertIn('Completion pressure must never be used to bypass', self.text)


if __name__ == '__main__':
    unittest.main()
