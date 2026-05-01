from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


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


if __name__ == "__main__":
    unittest.main()
