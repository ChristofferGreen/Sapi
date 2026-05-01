from __future__ import annotations

import json
import unittest
from pathlib import Path

from sapi.contracts.run_envelopes import _SEMANTIC_FLOW_KEYS
from sapi.contracts.semantic_specs import FLOW_MAP, resolve_semantic_spec


REPO_ROOT = Path(__file__).resolve().parents[3]
QUESTION_FLOW_KEYS = {
    "question_relevance_mapping",
    "question_synthesis",
    "question_measurement_extraction",
}


class PreparedQuestionContractDocTests(unittest.TestCase):
    def test_design_defines_prepared_questions_as_durable_front_page_artifacts(self) -> None:
        design_text = (REPO_ROOT / "docs" / "design.md").read_text()

        self.assertIn("`Prepared Question`", design_text)
        self.assertIn("not ad hoc query", design_text)
        self.assertIn("not topic clusters", design_text)
        self.assertIn("question index is the primary landing experience", design_text)
        self.assertIn("about 10 field-relevant questions", design_text)
        self.assertIn("lifecycle states are `active`, `inactive`, and `draft`", design_text)
        self.assertIn("has no active prepared questions", design_text)
        self.assertIn("MUST come from live schema-conformant LLM JSON", design_text)
        self.assertIn("NOT invent answer prose", design_text)

    def test_low_level_assigns_prepared_question_module_ownership(self) -> None:
        low_level_text = (REPO_ROOT / "docs" / "low_level.md").read_text()

        self.assertIn("sapi/questions/", low_level_text)
        self.assertIn("prepared_questions.py", low_level_text)
        self.assertIn("Prepared-question implementation ownership", low_level_text)
        self.assertIn("source-to-question relevance mapping", low_level_text)
        self.assertIn("cumulative question synthesis belongs in `sapi/questions/`", low_level_text)
        self.assertIn("deterministic question index/detail rendering belongs", low_level_text)
        self.assertIn("create_questions.sh", low_level_text)

    def test_question_semantic_flows_have_canonical_specs_schemas_and_run_keys(self) -> None:
        for flow_key in QUESTION_FLOW_KEYS:
            with self.subTest(flow_key=flow_key):
                self.assertIn(flow_key, FLOW_MAP)
                self.assertIn(flow_key, _SEMANTIC_FLOW_KEYS)
                resolved = resolve_semantic_spec(flow_key, repo_root=REPO_ROOT)
                self.assertEqual(resolved.flow_key, flow_key)
                self.assertTrue(resolved.spec_path.is_file())
                self.assertTrue(resolved.schema_path.is_file())

    def test_prepared_question_record_schema_is_checked_in(self) -> None:
        schema = json.loads((REPO_ROOT / "schemas" / "prepared_question.v1.schema.json").read_text())

        self.assertEqual(schema.get("type"), "object")
        self.assertFalse(schema.get("additionalProperties", True))
        self.assertIn("question_id", schema["required"])
        self.assertIn("linked_source_ids", schema["required"])
        self.assertIn("measurement_ids", schema["required"])
        self.assertIn("synthesis", schema["required"])
        self.assertIn("freshness", schema["required"])


if __name__ == "__main__":
    unittest.main()
