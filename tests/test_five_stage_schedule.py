from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FiveStageScheduleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schedule = json.loads((ROOT / "research_swarm" / "five_task_schedule.json").read_text())
        cls.schema = json.loads((ROOT / "research_swarm" / "checkpoint_envelope_v2.schema.json").read_text())

    def test_pipeline_has_five_serial_stages_at_ten_minute_offsets(self):
        self.assertEqual(self.schedule["execution_model"], "FIVE_STAGE_SERIAL_PIPELINE")
        self.assertEqual(self.schedule["stage_spacing_minutes"], 10)
        self.assertEqual(
            self.schedule["pipeline"]["order"],
            ["RESEARCHER_1", "RESEARCHER_2", "RESEARCHER_3", "MANAGER", "PRIMARY"],
        )
        self.assertEqual([task["minute"] for task in self.schedule["tasks"]], [0, 10, 20, 30, 40])
        self.assertEqual([task["window_end_minute"] for task in self.schedule["tasks"]], [10, 20, 30, 40, 50])

    def test_checkpoint_schema_is_project_scoped_and_non_authoritative(self):
        stages = set(self.schema["properties"]["stage"]["enum"])
        self.assertEqual(stages, {"RESEARCHER_1", "RESEARCHER_2", "RESEARCHER_3", "MANAGER", "PRIMARY"})
        self.assertIn("PROJECT_HOLD_ACTIVE", self.schema["properties"]["state"]["enum"])
        self.assertIn("project_id", self.schema["required"])
        self.assertIn("authority_conveyed", self.schema["required"])
        self.assertFalse(self.schema["properties"]["authority_conveyed"]["const"])
        self.assertEqual(self.schema["properties"]["schema"]["const"], "intercommunications/swarm-stage-checkpoint/v2")

    def test_project_scoped_coordination_transport_replaces_issue_comment_writes(self):
        transport = self.schedule["checkpoint_transport"]
        self.assertEqual(transport["transport"], "PROJECT_ARTIFACTORY_MESSAGE_FORUM_PLUS_GITHUB_BACKUP")
        self.assertEqual(transport["github_backup_prefix"], "agentbus-backup/coordination-messages/")
        self.assertEqual(transport["legacy_issue_25_transport"], "HISTORICAL_READ_ONLY")
        self.assertFalse(transport["authority_conveyed"])
        self.assertTrue(transport["artifactory_required_when_registered"])
        self.assertTrue(transport["github_backup_required"])
        self.assertFalse(transport["cross_project_fallback_allowed"])

    def test_partial_handoffs_are_explicitly_consumable(self):
        self.assertEqual(
            self.schedule["handoff_policy"],
            "PARTIAL_PROGRESS_IS_VALID_INPUT_WHEN_DURABLY_CHECKPOINTED_AND_LABELED_INCOMPLETE",
        )
        self.assertTrue(
            self.schedule["runtime_rules"][
                "downstream_does_not_require_upstream_completion_if_valid_current_project_current_cycle_progress_exists"
            ]
        )

    def test_each_prompt_loads_v2_transport_and_forbids_new_issue25_writes(self):
        for name in ["researcher_1.md", "researcher_2.md", "researcher_3.md", "manager.md", "primary.md"]:
            text = (ROOT / "research_swarm" / "prompts" / name).read_text()
            self.assertIn("checkpoint_envelope_v2.schema.json", text, name)
            self.assertIn("COORDINATION_PUBLICATION_POLICY.json", text, name)
            self.assertIn("agentbus-backup/coordination-messages/", text, name)
            self.assertIn("issue #25", text.lower(), name)
            self.assertIn("historical read-only", text.lower(), name)

    def test_manager_prompt_denies_general_durable_mutation(self):
        text = (ROOT / "research_swarm" / "prompts" / "manager.md").read_text()
        self.assertIn("only routine durable-write exception", text)
        self.assertIn("Source, accepted-state, arbitrary artifact, lifecycle, schedule", text)

    def test_primary_activation_and_mutation_authority_remain_separate(self):
        text = (ROOT / "research_swarm" / "prompts" / "primary.md").read_text()
        self.assertIn("scheduled Primary task may be enabled or re-enabled only by an explicit current human action", text)
        self.assertIn("scheduler launch is routing/execution authority only", text)
        self.assertIn("never mutation authorization", text)


if __name__ == "__main__":
    unittest.main()
