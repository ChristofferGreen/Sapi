from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.lint.lint_engine import (
    LintIssue,
    LintSummary,
    evaluate_lint_gate,
    parse_warning_budget,
    summarize_lint_issues,
    write_lint_artifact,
)
from sapi.lint.severity import normalize_lint_severity, severity_for_check


class WarningBudgetGateTests(unittest.TestCase):
    def test_severity_levels_and_example_check_mappings_are_enforced(self) -> None:
        self.assertEqual(normalize_lint_severity("error"), "error")
        self.assertEqual(normalize_lint_severity("warning"), "warning")
        self.assertEqual(normalize_lint_severity("info"), "info")

        self.assertEqual(severity_for_check("missing_claim_annotation"), "error")
        self.assertEqual(severity_for_check("missing_publication_date"), "warning")
        self.assertEqual(severity_for_check("ingest_source_suggestion"), "info")

        with self.assertRaises(ValueError):
            normalize_lint_severity("fatal")
        with self.assertRaises(ValueError):
            severity_for_check("unknown_check")

    def test_warning_budget_parsing_enforces_positive_integer_contract(self) -> None:
        self.assertEqual(parse_warning_budget(None), 200)
        self.assertEqual(parse_warning_budget("25"), 25)
        with self.assertRaises(ValueError):
            parse_warning_budget("0")
        with self.assertRaises(ValueError):
            parse_warning_budget("-3")
        with self.assertRaises(ValueError):
            parse_warning_budget("abc")

    def test_gate_behavior_matches_workflow_key_policy_table(self) -> None:
        lint_with_warning = summarize_lint_issues(
            [
                LintIssue(check_id="missing_publication_date", message="date missing"),
                LintIssue(check_id="missing_publication_date", message="date still missing"),
            ]
        )
        lint_with_error = summarize_lint_issues(
            [LintIssue(check_id="missing_claim_annotation", message="annotation missing")]
        )

        ingest_gate = evaluate_lint_gate("ingest_source", lint_with_warning, warning_threshold=1)
        self.assertFalse(ingest_gate.blocked)
        self.assertEqual(ingest_gate.status, "success_with_warnings")

        ingest_error_gate = evaluate_lint_gate("ingest_source", lint_with_error, warning_threshold=200)
        self.assertTrue(ingest_error_gate.blocked)
        self.assertEqual(ingest_error_gate.status, "failed")

        build_gate = evaluate_lint_gate("build_site", lint_with_error, warning_threshold=1)
        self.assertTrue(build_gate.blocked)
        self.assertEqual(build_gate.status, "failed")

        query_gate = evaluate_lint_gate("query", lint_with_error, warning_threshold=1)
        self.assertFalse(query_gate.blocked)
        self.assertEqual(query_gate.status, "success")

    def test_warning_threshold_boundary_applies_consistently_for_lint_gated_workflows(self) -> None:
        at_threshold = LintSummary(error_count=0, warning_count=1, info_count=0)
        over_threshold = LintSummary(error_count=0, warning_count=2, info_count=0)

        for workflow in (
            "ingest_source",
            "create_comments",
            "generate_profiles",
            "generate_overview",
            "rebuild_topic_collection",
        ):
            with self.subTest(workflow=workflow, case="at-threshold"):
                gate = evaluate_lint_gate(workflow, at_threshold, warning_threshold=1)
                self.assertFalse(gate.blocked)
                self.assertEqual(gate.status, "success")
            with self.subTest(workflow=workflow, case="over-threshold"):
                gate = evaluate_lint_gate(workflow, over_threshold, warning_threshold=1)
                self.assertFalse(gate.blocked)
                self.assertEqual(gate.status, "success_with_warnings")

    def test_query_workflow_remains_non_blocking_even_when_lint_counts_are_high(self) -> None:
        noisy_summary = LintSummary(error_count=3, warning_count=99, info_count=0)
        gate = evaluate_lint_gate("query", noisy_summary, warning_threshold=1)
        self.assertFalse(gate.blocked)
        self.assertEqual(gate.status, "success")

    def test_lint_artifact_writes_canonical_run_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "space-a"
            summary = LintSummary(error_count=0, warning_count=1, info_count=2)
            lint_path = write_lint_artifact(
                space_root=space_root,
                run_id="run-20260412T120000Z--abcdef1234",
                workflow="ingest_source",
                summary=summary,
            )
            self.assertEqual(
                lint_path,
                space_root / "runs" / "run-20260412T120000Z--abcdef1234" / "lint.json",
            )
            payload = json.loads(lint_path.read_text())
            self.assertEqual(payload["schema_version"], "lint_summary_v1")
            self.assertEqual(payload["workflow"], "ingest_source")
            self.assertEqual(payload["error_count"], 0)
            self.assertEqual(payload["warning_count"], 1)
            self.assertEqual(payload["info_count"], 2)


if __name__ == "__main__":
    unittest.main()
