from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.questions.prepared_questions import (
    PreparedQuestionSeed,
    load_prepared_questions,
    parse_prepared_question_seed_tsv,
    upsert_prepared_question_seeds,
)


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
            payload["linked_source_ids"] = ["source-a"]
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
            self.assertEqual(question.linked_source_ids, ("source-a",))
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


if __name__ == "__main__":
    unittest.main()
