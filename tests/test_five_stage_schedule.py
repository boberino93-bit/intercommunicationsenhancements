from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FiveStageScheduleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schedule = json.loads((ROOT / "research_swarm" / "five_task_schedule.json").read_text())
        cls.schema = json.loads((ROOT / "research_swarm" / "checkpoint_envelope.schema.json").read_text())

    def test_pipeline_has_five_serial_stages_at_ten_minute_offsets(self):
        self.assertEqual(self.schedule["execution_model"], "FIVE_STAGE_SERIAL_PIPELINE")
        self.assertEqual(self.schedule["stage_spacing_minutes"], 10)
        self.assertEqual(
            self.schedule["pipeline"]["order"],
            ["RESEARCHER_1", "RESEARCHER_2", "RESEARCHER_3", "MANAGER", "PRIMARY"],
        )
        self.assertEqual([task["minute"] for task in self.schedule["tasks"]], [0, 10, 20, 30, 40])
        self.assertEqual([task["window_end_minute"] for task in self.schedule["tasks"]], [10, 20, 30, 40, 50])

    def test_checkpoint_schema_accepts_all_five_stages_and_hold_state(self):
        stages = set(self.schema["properties"]["stage"]["enum"])
        self.assertEqual(stages, {"RESEARCHER_1", "RESEARCHER_2", "RESEARCHER_3", "MANAGER", "PRIMARY"})
        self.assertIn("PROJECT_HOLD_ACTIVE", self.schema["properties"]["state"]["enum"])

    def test_partial_handoffs_are_explicitly_consumable(self):
        self.assertEqual(
            self.schedule["handoff_policy"],
            "PARTIAL_PROGRESS_IS_VALID_INPUT_WHEN_DURABLY_CHECKPOINTED_AND_LABELED_INCOMPLETE",
        )
        self.assertTrue(self.schedule["runtime_rules"]["downstream_does_not_require_upstream_completion_if_valid_current_cycle_progress_exists"])

    def test_each_prompt_declares_correct_slot_and_hold_gate(self):
        expectations = {
            "researcher_1.md": [":00", ":10", "PROJECT_HOLD_ACTIVE"],
            "researcher_2.md": [":10", ":20", "RESEARCHER_1", "PROJECT_HOLD_ACTIVE"],
            "researcher_3.md": [":20", ":30", "RESEARCHER_2", "PROJECT_HOLD_ACTIVE"],
            "manager.md": [":30", ":40", "RESEARCHER_3", "PROJECT_HOLD_ACTIVE"],
            "primary.md": [":40", ":50", "MANAGER", "PROJECT_HOLD_ACTIVE"],
        }
        for name, required in expectations.items():
            text = (ROOT / "research_swarm" / "prompts" / name).read_text()
            for marker in required:
                self.assertIn(marker, text, f"{name} missing {marker}")

    def test_primary_activation_and_mutation_authority_remain_separate(self):
        text = (ROOT / "research_swarm" / "prompts" / "primary.md").read_text()
        self.assertIn("scheduled Primary task may be enabled or re-enabled only by an explicit current human action", text)
        self.assertIn("scheduler launch is routing/execution authority only", text)
        self.assertIn("never mutation authorization", text)


if __name__ == "__main__":
    unittest.main()
