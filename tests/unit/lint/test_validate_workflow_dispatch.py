from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
import textwrap
import unittest
from unittest.mock import patch

from sapi.lint.lint_engine import LintSummary, write_lint_artifact
from sapi.questions.prepared_questions import write_prepared_question_record
from scripts import lint as lint_script


class ValidateWorkflowDispatchTests(unittest.TestCase):
    def test_validate_accepts_workflow_and_optional_run_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root, registry_path = self._bootstrap_registry(Path(tmp))
            run_id = "run-20260412T120010Z--lint000001"
            write_lint_artifact(
                space_root=space_root,
                run_id=run_id,
                workflow="ingest_source",
                summary=LintSummary(error_count=0, warning_count=0, info_count=0, issues=()),
            )

            exit_code, stdout_text, stderr_text = self._invoke(
                [
                    "alpha",
                    "--registry-path",
                    str(registry_path),
                    "--workflow",
                    "ingest_source",
                    "--run-id",
                    run_id,
                ]
            )

            self.assertEqual(0, exit_code)
            self.assertEqual("", stderr_text)
            envelope = json.loads(stdout_text)
            self.assertEqual("ingest_source", envelope["workflow"])
            self.assertEqual(run_id, envelope["run_id"])
            self.assertEqual("success", envelope["status"])
            self.assertEqual(0, envelope["lint"]["error_count"])

    def test_selected_workflow_key_uses_contract_gate_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root, registry_path = self._bootstrap_registry(Path(tmp))
            run_id = "run-20260412T120011Z--lint000002"
            write_lint_artifact(
                space_root=space_root,
                run_id=run_id,
                workflow="ingest_source",
                summary=LintSummary(error_count=1, warning_count=0, info_count=0, issues=()),
            )

            ingest_exit, ingest_stdout, _ = self._invoke(
                [
                    "alpha",
                    "--registry-path",
                    str(registry_path),
                    "--workflow",
                    "ingest_source",
                    "--run-id",
                    run_id,
                ]
            )
            self.assertEqual(1, ingest_exit)
            ingest_envelope = json.loads(ingest_stdout)
            self.assertEqual("failed", ingest_envelope["status"])
            self.assertEqual("lint_gate", ingest_envelope["reason"])

            query_exit, query_stdout, _ = self._invoke(
                [
                    "alpha",
                    "--registry-path",
                    str(registry_path),
                    "--workflow",
                    "query",
                    "--run-id",
                    run_id,
                ]
            )
            self.assertEqual(0, query_exit)
            query_envelope = json.loads(query_stdout)
            self.assertEqual("success", query_envelope["status"])
            self.assertIsNone(query_envelope["reason"])

    def test_exit_codes_and_envelope_status_match_warning_threshold_outcomes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root, registry_path = self._bootstrap_registry(Path(tmp))
            run_id = "run-20260412T120012Z--lint000003"
            write_lint_artifact(
                space_root=space_root,
                run_id=run_id,
                workflow="ingest_source",
                summary=LintSummary(error_count=0, warning_count=2, info_count=0, issues=()),
            )

            exit_code, stdout_text, stderr_text = self._invoke(
                [
                    "alpha",
                    "--registry-path",
                    str(registry_path),
                    "--workflow",
                    "ingest_source",
                    "--run-id",
                    run_id,
                    "--warning-budget",
                    "1",
                ]
            )
            self.assertEqual(0, exit_code)
            self.assertEqual("", stderr_text)
            envelope = json.loads(stdout_text)
            self.assertEqual("success_with_warnings", envelope["status"])
            self.assertEqual(1, envelope["warning_threshold"])
            self.assertEqual(2, envelope["lint"]["warning_count"])

    def test_validate_reports_prepared_question_lint_issues_without_run_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root, registry_path = self._bootstrap_registry(Path(tmp))
            write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload(
                    "question-protein-intake",
                    measurement_ids=["measurement-protein-grams--123456789abc"],
                ),
            )

            exit_code, stdout_text, stderr_text = self._invoke(
                [
                    "alpha",
                    "--registry-path",
                    str(registry_path),
                    "--workflow",
                    "refresh_questions",
                ]
            )

            self.assertEqual(1, exit_code)
            self.assertEqual("", stderr_text)
            envelope = json.loads(stdout_text)
            self.assertEqual("failed", envelope["status"])
            self.assertEqual(1, envelope["lint"]["error_count"])
            self.assertEqual(
                "invalid_question_measurement",
                envelope["lint"]["issues"][0]["check_id"],
            )

    def test_invalid_warning_budget_fails_fast(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _, registry_path = self._bootstrap_registry(Path(tmp))
            exit_code, stdout_text, stderr_text = self._invoke(
                [
                    "alpha",
                    "--registry-path",
                    str(registry_path),
                    "--warning-budget",
                    "invalid",
                ]
            )
            self.assertEqual(1, exit_code)
            self.assertEqual("", stdout_text)
            self.assertIn("positive integer", stderr_text)

    def _bootstrap_registry(self, tmp_root: Path) -> tuple[Path, Path]:
        site_root = tmp_root / "site"
        space_root = site_root / "spaces" / "alpha"
        space_root.mkdir(parents=True)
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
        return space_root, registry_path

    def _invoke(self, argv: list[str]) -> tuple[int, str, str]:
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        with patch("scripts.lint.run_guardrail_checks", return_value=[]):
            with patch("scripts.lint.evaluate_pipeline_pr_evidence", return_value=[]):
                with patch("sys.stdout", stdout_capture), patch("sys.stderr", stderr_capture):
                    exit_code = lint_script.run_main(argv)
        return exit_code, stdout_capture.getvalue().strip(), stderr_capture.getvalue().strip()


def _question_payload(
    question_id: str,
    *,
    measurement_ids: list[str] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "prepared_question_v1",
        "question_id": question_id,
        "question": "What protein intake supports muscle growth?",
        "status": "active",
        "display_order": 1,
        "scope": {"space_name": "alpha"},
        "linked_source_ids": [],
        "claim_ids": [],
        "evidence_ids": [],
        "measurement_ids": measurement_ids if measurement_ids is not None else [],
        "synthesis": {},
        "freshness": {},
        "warnings": [],
    }


if __name__ == "__main__":
    unittest.main()
