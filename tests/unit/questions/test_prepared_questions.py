from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.questions.prepared_questions import (
    PreparedQuestionSeed,
    active_prepared_questions,
    load_prepared_questions,
    parse_prepared_question_seed_tsv,
    upsert_prepared_question_seeds,
    write_prepared_question_record,
)


SOURCE_ID = "source-protein--123456789abc"
CLAIM_ID = "claim-protein-intake--123456789abc"
EVIDENCE_ID = "evidence-protein-intake--123456789abc"


class PreparedQuestionTests(unittest.TestCase):
    def test_seed_tsv_parses_and_rejects_duplicate_orders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tsv_path = Path(tmp) / "questions.tsv"
            tsv_path.write_text(
                "# space_slug\tquestion_id\tdisplay_order\tquestion\n"
                "alpha\tquestion-first\t1\tWhat is first?\n"
                "alpha\tquestion-second\t2\tWhat is second?\n"
            )

            rows = parse_prepared_question_seed_tsv(tsv_path)

            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0].question_id, "question-first")
            self.assertEqual(rows[1].display_order, 2)

            tsv_path.write_text(
                "alpha\tquestion-first\t1\tWhat is first?\n"
                "alpha\tquestion-second\t1\tWhat is second?\n"
            )
            with self.assertRaisesRegex(ValueError, "duplicate display_order"):
                parse_prepared_question_seed_tsv(tsv_path)

    def test_seed_tsv_supports_status_and_rejects_invalid_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tsv_path = Path(tmp) / "questions.tsv"
            tsv_path.write_text(
                "alpha\tquestion-first\t1\tdraft\tWhat is first?\n"
                "alpha\tquestion-second\t2\tinactive\tWhat is second?\n"
            )

            rows = parse_prepared_question_seed_tsv(tsv_path)

            self.assertEqual(rows[0].status, "draft")
            self.assertEqual(rows[1].status, "inactive")

            tsv_path.write_text(
                "alpha\tquestion-first\t1\tWhat is first?\n"
                "alpha\tquestion-first\t2\tWhat is second?\n"
            )
            with self.assertRaisesRegex(ValueError, "duplicate question_id"):
                parse_prepared_question_seed_tsv(tsv_path)

            tsv_path.write_text("alpha\tquestion-first\t1\tremoved\tWhat is first?\n")
            with self.assertRaisesRegex(ValueError, "status must be one of"):
                parse_prepared_question_seed_tsv(tsv_path)

    def test_upsert_preserves_links_and_synthesis_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            seed = PreparedQuestionSeed(
                space_name="alpha",
                question_id="question-protein-intake",
                display_order=1,
                question="What protein intake supports muscle growth?",
            )

            written = upsert_prepared_question_seeds(
                space_root=space_root,
                space_name="alpha",
                seeds=[seed],
            )
            self.assertEqual(len(written), 1)

            payload_path = space_root / "questions" / "question-protein-intake.json"
            payload = json.loads(payload_path.read_text())
            _write_linked_artifacts(space_root)
            payload["linked_source_ids"] = [SOURCE_ID]
            payload["synthesis"] = {"short_answer": "Current answer."}
            payload_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

            updated_seed = PreparedQuestionSeed(
                space_name="alpha",
                question_id="question-protein-intake",
                display_order=2,
                question="How much protein supports muscle growth?",
            )
            upsert_prepared_question_seeds(
                space_root=space_root,
                space_name="alpha",
                seeds=[updated_seed],
            )

            questions = load_prepared_questions(space_root)
            self.assertEqual(len(questions), 1)
            question = questions[0]
            self.assertEqual(question.question, "How much protein supports muscle growth?")
            self.assertEqual(question.display_order, 2)
            self.assertEqual(question.linked_source_ids, (SOURCE_ID,))
            self.assertEqual(question.synthesis["short_answer"], "Current answer.")

    def test_upsert_applies_lifecycle_status_updates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            seed = PreparedQuestionSeed(
                space_name="alpha",
                question_id="question-protein-intake",
                display_order=1,
                question="What protein intake supports muscle growth?",
            )
            upsert_prepared_question_seeds(
                space_root=space_root,
                space_name="alpha",
                seeds=[seed],
            )

            upsert_prepared_question_seeds(
                space_root=space_root,
                space_name="alpha",
                seeds=[
                    PreparedQuestionSeed(
                        space_name="alpha",
                        question_id="question-protein-intake",
                        display_order=1,
                        question="What protein intake supports muscle growth?",
                        status="inactive",
                    )
                ],
            )

            questions = load_prepared_questions(space_root)
            self.assertEqual(questions[0].status, "inactive")

    def test_loader_validates_records_and_default_active_filtering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            _write_linked_artifacts(space_root)
            write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload(
                    "question-protein-intake",
                    2,
                    linked_source_ids=[SOURCE_ID],
                    claim_ids=[CLAIM_ID],
                    evidence_ids=[EVIDENCE_ID],
                ),
            )
            write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload("question-training-volume", 1, status="inactive"),
            )

            questions = load_prepared_questions(space_root)

            self.assertEqual([question.question_id for question in questions], [
                "question-training-volume",
                "question-protein-intake",
            ])
            self.assertEqual(questions[1].linked_source_ids, (SOURCE_ID,))
            self.assertEqual(questions[1].claim_ids, (CLAIM_ID,))
            self.assertEqual(questions[1].evidence_ids, (EVIDENCE_ID,))
            self.assertEqual(
                [question.question_id for question in active_prepared_questions(space_root)],
                ["question-protein-intake"],
            )

    def test_loader_rejects_duplicate_payload_ids_and_orders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            questions_root = space_root / "questions"
            questions_root.mkdir(parents=True)
            (questions_root / "question-first.json").write_text(
                json.dumps(_question_payload("question-first", 1), indent=2, sort_keys=True) + "\n"
            )
            (questions_root / "question-second.json").write_text(
                json.dumps(_question_payload("question-first", 2), indent=2, sort_keys=True) + "\n"
            )

            with self.assertRaisesRegex(ValueError, "filename must match question_id"):
                load_prepared_questions(space_root)

            (questions_root / "question-second.json").write_text(
                json.dumps(_question_payload("question-second", 1), indent=2, sort_keys=True) + "\n"
            )
            with self.assertRaisesRegex(ValueError, "duplicate display_order"):
                load_prepared_questions(space_root)

    def test_loader_rejects_invalid_records_broken_links_and_wrong_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            questions_root = space_root / "questions"
            questions_root.mkdir(parents=True)

            invalid_payload = _question_payload("question-invalid", 1)
            invalid_payload["unexpected"] = "not canonical"
            (questions_root / "question-invalid.json").write_text(
                json.dumps(invalid_payload, indent=2, sort_keys=True) + "\n"
            )
            with self.assertRaisesRegex(ValueError, "invalid prepared question record"):
                load_prepared_questions(space_root)

            missing_source_payload = _question_payload(
                "question-invalid",
                1,
                linked_source_ids=[SOURCE_ID],
            )
            (questions_root / "question-invalid.json").write_text(
                json.dumps(missing_source_payload, indent=2, sort_keys=True) + "\n"
            )
            with self.assertRaisesRegex(ValueError, "linked source_id not found"):
                load_prepared_questions(space_root)

            wrong_scope_payload = _question_payload("question-invalid", 1, space_name="beta")
            (questions_root / "question-invalid.json").write_text(
                json.dumps(wrong_scope_payload, indent=2, sort_keys=True) + "\n"
            )
            with self.assertRaisesRegex(ValueError, "scope.space_name must match"):
                load_prepared_questions(space_root)

    def test_writer_rejects_missing_links_and_preserves_stable_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            with self.assertRaisesRegex(ValueError, "linked claim_id not found"):
                write_prepared_question_record(
                    space_root=space_root,
                    space_name="alpha",
                    payload=_question_payload("question-protein-intake", 1, claim_ids=[CLAIM_ID]),
                )

            _write_linked_artifacts(space_root)
            first_path = write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload("question-protein-intake", 1, claim_ids=[CLAIM_ID]),
            )
            second_path = write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload(
                    "question-protein-intake",
                    3,
                    question="How much protein supports hypertrophy?",
                    claim_ids=[CLAIM_ID],
                ),
            )

            self.assertEqual(first_path, second_path)
            self.assertEqual(second_path.name, "question-protein-intake.json")
            questions = load_prepared_questions(space_root)
            self.assertEqual(questions[0].question, "How much protein supports hypertrophy?")
            self.assertEqual(questions[0].display_order, 3)

    def test_question_ids_may_use_deterministic_suffixes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            path = write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload("question-protein-intake--123456789abc", 1),
            )

            self.assertEqual(path.name, "question-protein-intake--123456789abc.json")
            self.assertEqual(load_prepared_questions(space_root)[0].question_id, path.stem)


def _question_payload(
    question_id: str,
    display_order: int,
    *,
    question: str = "What protein intake supports muscle growth?",
    status: str = "active",
    space_name: str = "alpha",
    linked_source_ids: list[str] | None = None,
    claim_ids: list[str] | None = None,
    evidence_ids: list[str] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "prepared_question_v1",
        "question_id": question_id,
        "question": question,
        "status": status,
        "display_order": display_order,
        "scope": {"space_name": space_name},
        "linked_source_ids": [] if linked_source_ids is None else linked_source_ids,
        "claim_ids": [] if claim_ids is None else claim_ids,
        "evidence_ids": [] if evidence_ids is None else evidence_ids,
        "measurement_ids": [],
        "synthesis": {},
        "freshness": {},
        "warnings": [],
    }


def _write_linked_artifacts(space_root: Path) -> None:
    source_path = space_root / "sources" / "records" / f"{SOURCE_ID}.json"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        json.dumps(
            {
                "schema_version": "source_record_v1",
                "source_id": SOURCE_ID,
                "title": "Protein source",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    claim_path = space_root / "claims" / f"{CLAIM_ID}.json"
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    claim_path.write_text(
        json.dumps(
            {
                "schema_version": "claim_record_v1",
                "claim_id": CLAIM_ID,
                "source_id": SOURCE_ID,
                "text": "Protein supports muscle growth.",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    evidence_path = space_root / "evidence" / f"{EVIDENCE_ID}.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(
            {
                "schema_version": "evidence_record_v1",
                "evidence_id": EVIDENCE_ID,
                "source_id": SOURCE_ID,
                "claim_ids": [CLAIM_ID],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


if __name__ == "__main__":
    unittest.main()
