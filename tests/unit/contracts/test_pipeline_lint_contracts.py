from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DESIGN_DOC_PATH = REPO_ROOT / "docs" / "design.md"
LOW_LEVEL_DOC_PATH = REPO_ROOT / "docs" / "low_level.md"
TESTING_PLAN_PATH = REPO_ROOT / "docs" / "testing_plan.md"


class PipelineLintContractTests(unittest.TestCase):
    def test_design_docs_require_shared_lint_gate_finalization(self) -> None:
        design_text = DESIGN_DOC_PATH.read_text()
        self.assertIn(
            "semantic pipeline entrypoints MUST derive committed run-envelope lint totals and terminal status from the shared lint-gate evaluation path",
            design_text,
        )
        self.assertNotIn(
            "stamp literal zero-count lint metadata as a shortcut",
            design_text.split(
                "semantic pipeline entrypoints MUST derive committed run-envelope lint totals and terminal status from the shared lint-gate evaluation path"
            )[0],
        )

    def test_low_level_docs_require_shared_lint_gate_helper(self) -> None:
        low_level_text = LOW_LEVEL_DOC_PATH.read_text()
        self.assertIn(
            "semantic pipeline entrypoints MUST populate `RunEnvelopeBase.lint_*` counts from a `LintSummary`",
            low_level_text,
        )
        self.assertIn(
            "callers MUST NOT hardcode zero-count lint summaries as a shortcut",
            low_level_text,
        )

    def test_testing_plan_tracks_pipeline_lint_finalization_coverage(self) -> None:
        testing_plan_text = TESTING_PLAN_PATH.read_text()
        self.assertIn(
            "Shared pipeline finalization stamps run-envelope lint totals/status from the lint gate instead of hardcoded zero-count metadata.",
            testing_plan_text,
        )
        self.assertIn("tests/unit/core/test_pipeline_policy.py", testing_plan_text)


if __name__ == "__main__":
    unittest.main()
