from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.questions.linting import collect_question_lint_issues
from sapi.questions.prepared_questions import load_prepared_questions, write_prepared_question_record
from sapi.questions.synthesis import build_question_synthesis_context


class PreparedQuestionLintingTests(unittest.TestCase):
    def test_stale_synthesis_signature_is_reported_as_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            _write_source(space_root, SOURCE_ID)
            question_path = write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload(linked_source_ids=[SOURCE_ID]),
            )

            issues = collect_question_lint_issues(space_root)

            self.assertEqual([issue.check_id for issue in issues], ["stale_question_synthesis"])
            self.assertEqual(issues[0].severity, "warning")
            self.assertEqual(issues[0].path, str(question_path))

    def test_current_synthesis_signature_does_not_warn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            _write_source(space_root, SOURCE_ID)
            question_path = write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload(linked_source_ids=[SOURCE_ID]),
            )
            question = next(
                question
                for question in load_prepared_questions(space_root)
                if question.question_id == "question-protein-intake"
            )
            payload = json.loads(question_path.read_text())
            payload["freshness"] = {
                "question_synthesis": {
                    "status": "refreshed",
                    "run_id": "run-20260501T120000Z--abcdefghij",
                    "input_signature": build_question_synthesis_context(
                        space_root=space_root,
                        question=question,
                    ).input_signature,
                    "semantic_output_path": "runs/run/semantic/question_synthesis/question-protein-intake.json",
                    "refreshed_at": "2026-05-01T12:00:00Z",
                }
            }
            write_prepared_question_record(space_root=space_root, space_name="alpha", payload=payload)

            self.assertEqual(collect_question_lint_issues(space_root), [])

    def test_missing_measurement_record_is_reported_as_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload(measurement_ids=[MEASUREMENT_ID]),
            )

            issues = collect_question_lint_issues(space_root, include_site_output=False)

            self.assertIn("invalid_question_measurement", [issue.check_id for issue in issues])
            measurement_issue = next(issue for issue in issues if issue.check_id == "invalid_question_measurement")
            self.assertEqual(measurement_issue.severity, "error")
            self.assertIn(MEASUREMENT_ID, measurement_issue.message)

    def test_valid_measurement_record_does_not_report_measurement_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            _write_source(space_root, SOURCE_ID)
            measurement_path = space_root / "measurements" / f"{MEASUREMENT_ID}.json"
            measurement_path.parent.mkdir(parents=True, exist_ok=True)
            measurement_path.write_text(
                json.dumps(
                    {
                        "schema_version": "question_measurement_v1",
                        "question_id": "question-protein-intake",
                        "measurement_id": MEASUREMENT_ID,
                        "source_id": SOURCE_ID,
                        "claim_id": None,
                        "evidence_id": "evidence-protein-study--123456789abc",
                        "measure_name": "protein intake",
                        "value": 1.6,
                        "value_max": 2.2,
                        "unit": "g/kg/day",
                        "population": "resistance-trained adults",
                        "outcome": "muscle hypertrophy",
                        "comparator": "lower intake",
                        "uncertainty": "range depends on context",
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
            evidence_path = space_root / "evidence" / "evidence-protein-study--123456789abc.json"
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            evidence_path.write_text(json.dumps({"evidence_id": "evidence-protein-study--123456789abc"}) + "\n")
            write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload(
                    linked_source_ids=[SOURCE_ID],
                    evidence_ids=["evidence-protein-study--123456789abc"],
                    measurement_ids=[MEASUREMENT_ID],
                ),
            )

            issues = collect_question_lint_issues(space_root, include_site_output=False)

            self.assertNotIn("invalid_question_measurement", [issue.check_id for issue in issues])

    def test_built_question_front_page_state_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload(),
            )
            (space_root / "site" / "questions").mkdir(parents=True)
            (space_root / "site" / "index.html").write_text("<html><body>No questions here</body></html>")
            (space_root / "site" / "questions" / "index.html").write_text("<html><body></body></html>")

            issues = collect_question_lint_issues(space_root)

            self.assertEqual(
                {"missing_question_front_page"},
                {issue.check_id for issue in issues},
            )
            self.assertGreaterEqual(len(issues), 2)


SOURCE_ID = "source-protein-study--123456789abc"
MEASUREMENT_ID = "measurement-protein-grams--123456789abc"


def _question_payload(
    *,
    linked_source_ids: list[str] | None = None,
    evidence_ids: list[str] | None = None,
    measurement_ids: list[str] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "prepared_question_v1",
        "question_id": "question-protein-intake",
        "question": "What protein intake supports muscle growth?",
        "status": "active",
        "display_order": 1,
        "scope": {"space_name": "alpha"},
        "linked_source_ids": linked_source_ids if linked_source_ids is not None else [],
        "claim_ids": [],
        "evidence_ids": evidence_ids if evidence_ids is not None else [],
        "measurement_ids": measurement_ids if measurement_ids is not None else [],
        "synthesis": {},
        "freshness": {},
        "warnings": [],
    }


def _write_source(space_root: Path, source_id: str) -> None:
    path = space_root / "sources" / "records" / f"{source_id}.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "source_id": source_id,
                "title": "Protein study",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


if __name__ == "__main__":
    unittest.main()
