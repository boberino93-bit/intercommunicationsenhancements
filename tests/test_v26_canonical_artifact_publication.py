from pathlib import Path
import hashlib
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_NAME = "Intercommunication_Enhancements_Herd_AI_BIOS_V26_CANONICAL_PROJECT_BOOTSTRAP_SINGLE_FILE.md"
CANONICAL_BYTES = 108015662
CANONICAL_SHA = "e85a52c01dcc1e359db93d18a5b73e1328fd9f5a7943cf7999579b4e7e4a4348"
PARENT_SHA = "122e73dc7ba01384d799fc508c337081948ae1714f869a318d2ab96cd142d778"
LOGICAL_ID = "INTERCOMMUNICATION_ENHANCEMENTS::AGENTBUS::V26_CANONICAL_ARTIFACT_PUBLICATION"
PAYLOAD_SHA = "f07557f609b84e11431f633f4bd79d4545c3ec03e181d2a39d5c275d8eaf975f"
CASE_ID = "AUTH-20261016-V26-CANONICAL-ARTIFACT-PUBLISH-01"


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class V26CanonicalArtifactPublicationTests(unittest.TestCase):
    def test_root_pointer_identifies_canonical_project_file(self):
        pointer = load_json("V26_CANONICAL_PROJECT_BOOTSTRAP_POINTER.json")
        self.assertEqual(pointer["canonical_bootstrap_generation"], "V26")
        artifact = pointer["canonical_project_bootstrap_artifact"]
        self.assertEqual(artifact["name"], CANONICAL_NAME)
        self.assertEqual(artifact["bytes"], CANONICAL_BYTES)
        self.assertEqual(artifact["sha256"], CANONICAL_SHA)
        self.assertTrue(artifact["canonical_promotion"])
        self.assertFalse(pointer["precedence"]["v25_r11_current"])
        self.assertFalse(pointer["project_separation"]["cv_support_federated"])

    def test_generation_manifest_distinguishes_project_file_from_validated_parent(self):
        manifest = load_json("PROJECT_MANIFEST_V26.json")
        self.assertEqual(manifest["artifact"]["sha256"], PARENT_SHA)
        project_file = manifest["canonical_project_file_representation"]
        self.assertEqual(project_file["name"], CANONICAL_NAME)
        self.assertEqual(project_file["bytes"], CANONICAL_BYTES)
        self.assertEqual(project_file["sha256"], CANONICAL_SHA)
        self.assertTrue(project_file["embedded_validated_parent_byte_for_byte_verified"])
        self.assertEqual(project_file["embedded_validated_parent_sha256"], PARENT_SHA)
        self.assertEqual(manifest["authorization"]["canonical_artifact_publication_case_id"], CASE_ID)
        self.assertEqual(manifest["authorization"]["canonical_artifact_publication_proof_issue"], 201)

    def test_agentbus_record_is_hash_bound_but_not_falsely_claimed_written(self):
        record = load_json("agentbus-backup/coordination-messages/v26-canonical-artifact/V26_CANONICAL_ARTIFACT_PUBLICATION_PENDING_AGENTBUS.json")
        self.assertEqual(record["logical_record_id"], LOGICAL_ID)
        self.assertEqual(record["payload_sha256"], PAYLOAD_SHA)
        canonical_payload = json.dumps(record["payload"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        self.assertEqual(hashlib.sha256(canonical_payload).hexdigest(), PAYLOAD_SHA)
        bus = record["payload"]["agentbus"]
        self.assertFalse(bus["write_performed_from_current_runtime"])
        self.assertFalse(bus["readback_performed_from_current_runtime"])
        self.assertEqual(bus["surface"], "CHATGPT_LIBRARY_AGENTBUS")
        self.assertEqual(bus["message_board"], "/Intercommunication enhancements/AgentBus/messages")

    def test_publication_record_matches_agentbus_envelope(self):
        publication = load_json("governance/V26_CANONICAL_ARTIFACT_PUBLICATION.json")
        self.assertEqual(publication["artifact"]["sha256"], CANONICAL_SHA)
        self.assertEqual(publication["agentbus"]["logical_record_id"], LOGICAL_ID)
        self.assertEqual(publication["agentbus"]["payload_sha256"], PAYLOAD_SHA)
        self.assertFalse(publication["agentbus"]["write_performed_from_current_runtime"])
        self.assertEqual(publication["authorization"]["case_id"], CASE_ID)
        self.assertEqual(publication["authorization"]["proof_issue"], 201)
        self.assertFalse(publication["project_separation"]["cv_support_federated"])


if __name__ == "__main__":
    unittest.main()
