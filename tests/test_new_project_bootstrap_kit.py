from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NewProjectBootstrapKitTests(unittest.TestCase):
    def test_manifest_is_unbound_and_has_required_templates(self):
        kit = json.loads((ROOT / "NEW_PROJECT_BOOTSTRAP.json").read_text())
        self.assertEqual(kit["seed_state"]["repository_binding"], "UNBOUND")
        self.assertFalse(kit["seed_state"]["github_required_to_start"])
        self.assertIsNone(kit["seed_state"]["repository_view"]["path"])

        outputs = {item["output"] for item in kit["required_documents"]}
        self.assertEqual(
            outputs,
            {
                "AGENT_BOOTSTRAP.json",
                "PROJECT_IDENTITY_LOCK.json",
                "PROJECT_MANIFEST.json",
                "BOOTSTRAP_ORDER.json",
                "START_HERE.md",
                "PROJECT_CHARTER.md",
                "HARDENING_STATUS.md",
            },
        )

        for item in kit["required_documents"]:
            self.assertTrue((ROOT / item["template"]).is_file(), item["template"])

    def test_json_templates_parse_and_do_not_bind_source_repository(self):
        template_names = [
            "AGENT_BOOTSTRAP.template.json",
            "PROJECT_IDENTITY_LOCK.template.json",
            "PROJECT_MANIFEST.template.json",
            "BOOTSTRAP_ORDER.template.json",
        ]
        for name in template_names:
            raw = (ROOT / "templates" / "new-project" / name).read_text()
            parsed = json.loads(raw)
            repository = parsed.get("repository")
            if repository is not None:
                self.assertEqual(repository.get("binding_state"), "UNBOUND")
                self.assertIsNone(repository.get("full_name"))
                self.assertIsNone(repository.get("id"))
            self.assertNotIn('"full_name": "boberino93-bit/', raw)

    def test_global_entrypoint_has_explicit_new_project_branch(self):
        entrypoint = json.loads((ROOT / "GLOBAL_AGENT_ENTRYPOINT.json").read_text())
        branch = entrypoint["intent_branches"]["new_project_bootstrap"]
        self.assertEqual(branch["mode"], "UNBOUND_PROJECT_SEED")
        self.assertFalse(branch["repository_required"])
        self.assertEqual(branch["source_project_identity_inheritance"], "DENY")
        self.assertEqual(branch["cross_project_mutation"], "DENY")

    def test_local_bootstrap_exposes_project_factory(self):
        bootstrap = json.loads((ROOT / "AGENT_BOOTSTRAP.json").read_text())
        self.assertEqual(bootstrap["project_factory"]["pointer"], "NEW_PROJECT_BOOTSTRAP.json")
        self.assertTrue(bootstrap["project_factory"]["supports_unbound_repository"])
        self.assertIn("NEW_PROJECT_BOOTSTRAP.json", bootstrap["handoff_paths"])


if __name__ == "__main__":
    unittest.main()
