from __future__ import annotations

import io
from pathlib import Path
import tempfile
import textwrap
import unittest
from unittest.mock import patch

from sapi.lint.guardrails import evaluate_pipeline_pr_evidence
from scripts import lint as lint_script


REPO_ROOT = Path(__file__).resolve().parents[3]
PR_TEMPLATE_PATH = REPO_ROOT / ".github" / "pull_request_template.md"
CONTRIBUTING_DOC_PATH = REPO_ROOT / "docs" / "contributing.md"


class PipelinePrChecklistGateTests(unittest.TestCase):
    def test_pr_template_includes_all_required_pipeline_review_questions(self) -> None:
        content = PR_TEMPLATE_PATH.read_text()
        required_questions = (
            "Q1 Which canonical artifacts can this command mutate?",
            "Q2 Which semantic flow keys can run, and in what order?",
            "Q3 What exactly is rolled back on terminal failure?",
            "Q4 Does run envelope include correct `flow_key`, ordered-unique `semantic_flows[]`, `semantic_flow_invocation_counts`, and required extension fields?",
            "Q5 Are manifest outputs conditional by query format as required?",
            "Q6 Are comments default-target rules, count bounds, and `comment_uid` stability preserved?",
            "Q7 Are profile/history links canonical in rendered output?",
            "Q8 Are site-root `New` refresh decisions correct for this flow?",
            "Docs Sync: Contract-level changes follow `design.md` -> `low_level.md` -> code/tests order.",
        )
        for question in required_questions:
            self.assertIn(question, content)

    def test_contributing_docs_enforce_design_low_level_code_order(self) -> None:
        content = CONTRIBUTING_DOC_PATH.read_text()
        self.assertIn("Update `docs/design.md` first", content)
        self.assertIn("Update `docs/low_level.md` second", content)
        self.assertIn("Update code and tests last", content)
        self.assertIn("must fail quality gates", content)

    def test_pipeline_changes_require_checklist_evidence(self) -> None:
        issues = evaluate_pipeline_pr_evidence(
            repo_root=REPO_ROOT,
            changed_files=["sapi/query/query_pipeline.py"],
            checklist_path=None,
        )
        self.assertTrue(any(issue.check_id == "pipeline_pr_checklist_missing" for issue in issues))

    def test_pipeline_changes_fail_when_docs_sync_item_is_not_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checklist_path = Path(tmp) / "pipeline-checklist.md"
            checklist_path.write_text(
                textwrap.dedent(
                    """
                    - [x] Q1 Which canonical artifacts can this command mutate?
                    - [x] Q2 Which semantic flow keys can run, and in what order?
                    - [x] Q3 What exactly is rolled back on terminal failure?
                    - [x] Q4 Does run envelope include correct `flow_key`, ordered-unique `semantic_flows[]`, `semantic_flow_invocation_counts`, and required extension fields?
                    - [x] Q5 Are manifest outputs conditional by query format as required?
                    - [x] Q6 Are comments default-target rules, count bounds, and `comment_uid` stability preserved?
                    - [x] Q7 Are profile/history links canonical in rendered output?
                    - [x] Q8 Are site-root `New` refresh decisions correct for this flow?
                    - [ ] Docs Sync: Contract-level changes follow `design.md` -> `low_level.md` -> code/tests order
                    """
                ).strip()
                + "\n"
            )
            issues = evaluate_pipeline_pr_evidence(
                repo_root=REPO_ROOT,
                changed_files=["scripts/query.py"],
                checklist_path=str(checklist_path),
            )
        self.assertTrue(any(issue.check_id == "pipeline_pr_checklist_incomplete" for issue in issues))

    def test_pipeline_changes_pass_with_completed_checklist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checklist_path = Path(tmp) / "pipeline-checklist.md"
            checklist_path.write_text(
                textwrap.dedent(
                    """
                    - [x] Q1 Which canonical artifacts can this command mutate?
                    - [x] Q2 Which semantic flow keys can run, and in what order?
                    - [x] Q3 What exactly is rolled back on terminal failure?
                    - [x] Q4 Does run envelope include correct `flow_key`, ordered-unique `semantic_flows[]`, `semantic_flow_invocation_counts`, and required extension fields?
                    - [x] Q5 Are manifest outputs conditional by query format as required?
                    - [x] Q6 Are comments default-target rules, count bounds, and `comment_uid` stability preserved?
                    - [x] Q7 Are profile/history links canonical in rendered output?
                    - [x] Q8 Are site-root `New` refresh decisions correct for this flow?
                    - [x] Docs Sync: Contract-level changes follow `design.md` -> `low_level.md` -> code/tests order
                    """
                ).strip()
                + "\n"
            )
            issues = evaluate_pipeline_pr_evidence(
                repo_root=REPO_ROOT,
                changed_files=["sapi/ingest/ingest_pipeline.py"],
                checklist_path=str(checklist_path),
            )
        self.assertEqual([], issues)

    def test_validate_entrypoint_fails_when_pipeline_changes_missing_checklist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp)
            (site_root / "spaces" / "alpha").mkdir(parents=True)
            registry_path = site_root / "spaces.toml"
            registry_path.write_text(
                textwrap.dedent(
                    """
                    [[spaces]]
                    space_name = "alpha"
                    space_root = "spaces/alpha"
                    """
                ).strip()
                + "\n"
            )

            stderr_capture = io.StringIO()
            with patch("scripts.lint.run_guardrail_checks", return_value=[]):
                with patch("sys.stderr", stderr_capture):
                    exit_code = lint_script.run_main(
                        [
                            "alpha",
                            "--registry-path",
                            str(registry_path),
                            "--changed-file",
                            "sapi/query/query_pipeline.py",
                        ]
                    )

        self.assertEqual(1, exit_code)
        stderr_text = stderr_capture.getvalue()
        self.assertIn("pipeline_pr_checklist_missing", stderr_text)


if __name__ == "__main__":
    unittest.main()
