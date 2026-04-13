from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]

SPEC_CONTRACT = {
    "ingest_extraction": {
        "spec": "ai_flows/generation_specs/ingest_extraction.v1.md",
        "schema": "schemas/ingest_extraction.v1.schema.json",
        "required_keys": [
            "source_date_inference",
            "source",
            "claims",
            "relations",
            "summary",
            "warnings",
        ],
    },
    "topic_generation": {
        "spec": "ai_flows/generation_specs/topic_generation.v1.md",
        "schema": "schemas/topic_generation.v1.schema.json",
        "required_keys": [
            "topics",
        ],
    },
    "query_synthesis": {
        "spec": "ai_flows/generation_specs/query_synthesis.v1.md",
        "schema": "schemas/query_synthesis.v1.schema.json",
        "required_keys": [
            "query_id",
            "answer",
            "claims_used",
            "sources_used",
            "retrieval_counts",
            "contradictions_considered",
            "falsification_signals",
            "mode",
            "scope",
            "execution",
            "warnings",
        ],
    },
    "comment_section_generation": {
        "spec": "ai_flows/generation_specs/comment_section_generation.v1.md",
        "schema": "schemas/comment_section_generation.v1.schema.json",
        "required_keys": ["page_ref", "requested_count", "comments"],
    },
    "persona_profile_generation": {
        "spec": "ai_flows/generation_specs/persona_profile_generation.v1.md",
        "schema": "schemas/persona_profile_generation.v1.schema.json",
        "required_keys": [
            "persona_id",
            "space_name",
            "profile_sections",
            "profile_image_path",
            "accountability_summary",
        ],
    },
}


class Todo0202SpecSchemaInventoryTests(unittest.TestCase):
    def test_required_v1_inventory_exists(self) -> None:
        for flow_key, contract in SPEC_CONTRACT.items():
            spec_path = REPO_ROOT / contract["spec"]
            schema_path = REPO_ROOT / contract["schema"]
            self.assertTrue(spec_path.is_file(), flow_key)
            self.assertTrue(schema_path.is_file(), flow_key)

    def test_each_spec_has_required_machine_readable_header_fields(self) -> None:
        for flow_key, contract in SPEC_CONTRACT.items():
            spec_path = REPO_ROOT / contract["spec"]
            text = spec_path.read_text()
            header, _, _ = text.partition("\n---\n")

            self.assertIn(f"flow_key: {flow_key}", header, flow_key)
            self.assertIn("version: v1", header, flow_key)
            self.assertIn(f"schema_path: {contract['schema']}", header, flow_key)
            self.assertIn("output_json_path:", header, flow_key)
            self.assertIn("context_paths:", header, flow_key)
            self.assertRegex(header, r"(?m)^\s*-\s+\S+", flow_key)
            self.assertRegex(header, r"(?m)^output_json_path:\s+\S+", flow_key)

    def test_spec_and_schema_paths_follow_v1_inventory_naming(self) -> None:
        for flow_key, contract in SPEC_CONTRACT.items():
            self.assertEqual(
                Path(contract["spec"]).name,
                f"{flow_key}.v1.md",
                flow_key,
            )
            self.assertEqual(
                Path(contract["schema"]).name,
                f"{flow_key}.v1.schema.json",
                flow_key,
            )

    def test_each_schema_enforces_top_level_object_and_required_keys(self) -> None:
        for flow_key, contract in SPEC_CONTRACT.items():
            schema_path = REPO_ROOT / contract["schema"]
            schema = json.loads(schema_path.read_text())

            self.assertEqual(schema.get("type"), "object", flow_key)
            self.assertFalse(schema.get("additionalProperties", True), flow_key)
            self.assertIn("required", schema, flow_key)

            required = set(schema["required"])
            for key in contract["required_keys"]:
                self.assertIn(key, required, f"{flow_key}:{key}")


if __name__ == "__main__":
    unittest.main()
