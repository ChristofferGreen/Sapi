from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.conftest import REPO_ROOT, bootstrap_site_and_space, run_command


class CreateQuestionsWrapperTests(unittest.TestCase):
    def test_wrapper_rejects_invalid_arguments(self) -> None:
        result = run_command(["bash", str(REPO_ROOT / "create_questions.sh")])

        self.assertEqual(result.returncode, 2)
        self.assertIn("Usage: create_questions.sh", result.stderr)

    def test_wrapper_creates_questions_and_builder_renders_question_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = bootstrap_site_and_space(Path(tmp), "alpha")
            questions_tsv = Path(tmp) / "questions.tsv"
            questions_tsv.write_text(
                "alpha\tquestion-protein-intake\t1\tWhat protein intake supports muscle growth?\n"
                "alpha\tquestion-training-volume\t2\tHow much training volume is optimal?\n"
            )

            create_result = run_command(
                [
                    "bash",
                    str(REPO_ROOT / "create_questions.sh"),
                    str(site_path),
                    str(questions_tsv),
                ]
            )
            self.assertEqual(create_result.returncode, 0, msg=create_result.stderr)
            self.assertIn("questions=2", create_result.stdout)

            question_path = (
                site_path
                / "spaces"
                / "alpha"
                / "questions"
                / "question-protein-intake.json"
            )
            payload = json.loads(question_path.read_text())
            self.assertEqual(payload["question"], "What protein intake supports muscle growth?")
            self.assertEqual(payload["display_order"], 1)
            self.assertEqual(payload["scope"]["space_name"], "alpha")

            build_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "alpha",
                ]
            )
            self.assertEqual(build_result.returncode, 0, msg=build_result.stderr)

            home_text = (site_path / "spaces" / "alpha" / "site" / "index.html").read_text()
            self.assertIn("What protein intake supports muscle growth?", home_text)
            self.assertIn('href="questions/question-protein-intake.html"', home_text)

            index_text = (
                site_path / "spaces" / "alpha" / "site" / "questions" / "index.html"
            ).read_text()
            self.assertIn("How much training volume is optimal?", index_text)

            detail_text = (
                site_path / "spaces" / "alpha" / "site" / "questions" / "question-protein-intake.html"
            ).read_text()
            self.assertIn("No sources have been linked to this question yet.", detail_text)
            self.assertIn("No synthesis has been generated for this question yet.", detail_text)

    def test_wrapper_rejects_duplicate_question_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = bootstrap_site_and_space(Path(tmp), "alpha")
            questions_tsv = Path(tmp) / "questions.tsv"
            questions_tsv.write_text(
                "alpha\tquestion-protein-intake\t1\tWhat protein intake supports muscle growth?\n"
                "alpha\tquestion-protein-intake\t2\tHow much protein is too much?\n"
            )

            result = run_command(
                [
                    "bash",
                    str(REPO_ROOT / "create_questions.sh"),
                    str(site_path),
                    str(questions_tsv),
                ]
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate question_id", result.stderr)

    def test_wrapper_updates_reorders_and_deactivates_questions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = bootstrap_site_and_space(Path(tmp), "alpha")
            questions_tsv = Path(tmp) / "questions.tsv"
            questions_tsv.write_text(
                "alpha\tquestion-protein-intake\t1\tWhat protein intake supports muscle growth?\n"
                "alpha\tquestion-training-volume\t2\tHow much training volume is optimal?\n"
            )
            result = run_command(
                [
                    "bash",
                    str(REPO_ROOT / "create_questions.sh"),
                    str(site_path),
                    str(questions_tsv),
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            questions_tsv.write_text(
                "alpha\tquestion-training-volume\t1\tactive\tHow much weekly training volume is optimal?\n"
                "alpha\tquestion-protein-intake\t2\tinactive\tWhat protein intake supports muscle growth?\n"
            )
            result = run_command(
                [
                    "bash",
                    str(REPO_ROOT / "create_questions.sh"),
                    str(site_path),
                    str(questions_tsv),
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            protein_path = (
                site_path
                / "spaces"
                / "alpha"
                / "questions"
                / "question-protein-intake.json"
            )
            training_path = (
                site_path
                / "spaces"
                / "alpha"
                / "questions"
                / "question-training-volume.json"
            )
            protein_payload = json.loads(protein_path.read_text())
            training_payload = json.loads(training_path.read_text())
            self.assertEqual(protein_payload["status"], "inactive")
            self.assertEqual(protein_payload["display_order"], 2)
            self.assertEqual(training_payload["display_order"], 1)
            self.assertEqual(
                training_payload["question"],
                "How much weekly training volume is optimal?",
            )

    def test_wrapper_targets_registered_subspaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "nutrition")
            create_child_result = run_command(
                [
                    "bash",
                    str(REPO_ROOT / "create_space.sh"),
                    str(site_path),
                    "nutrition-protein",
                ]
            )
            self.assertEqual(create_child_result.returncode, 0, msg=create_child_result.stderr)
            subspaces_tsv = tmp_root / "subspaces.tsv"
            subspaces_tsv.write_text(
                "nutrition\tNutrition\tnutrition-protein\tProtein\n"
            )
            subspace_result = run_command(
                [
                    "bash",
                    str(REPO_ROOT / "create_subspaces.sh"),
                    str(site_path),
                    str(subspaces_tsv),
                ]
            )
            self.assertEqual(subspace_result.returncode, 0, msg=subspace_result.stderr)

            questions_tsv = tmp_root / "questions.tsv"
            questions_tsv.write_text(
                "nutrition\tquestion-diet-quality\t1\tWhat diet patterns improve health?\n"
                "nutrition-protein\tquestion-protein-intake\t1\tWhat protein intake supports muscle growth?\n"
            )

            result = run_command(
                [
                    "bash",
                    str(REPO_ROOT / "create_questions.sh"),
                    str(site_path),
                    str(questions_tsv),
                    "nutrition-protein",
                ]
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("spaces=1", result.stdout)
            self.assertFalse(
                (site_path / "spaces" / "nutrition" / "questions" / "question-diet-quality.json").exists()
            )
            child_question = (
                site_path
                / "spaces"
                / "nutrition-protein"
                / "questions"
                / "question-protein-intake.json"
            )
            payload = json.loads(child_question.read_text())
            self.assertEqual(payload["scope"]["space_name"], "nutrition-protein")

    def test_wrapper_rejects_empty_space_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = bootstrap_site_and_space(Path(tmp), "alpha")
            questions_tsv = Path(tmp) / "questions.tsv"
            questions_tsv.write_text(
                "alpha\tquestion-protein-intake\t1\tWhat protein intake supports muscle growth?\n"
            )

            result = run_command(
                [
                    "bash",
                    str(REPO_ROOT / "create_questions.sh"),
                    str(site_path),
                    str(questions_tsv),
                    "missing-space",
                ]
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("No prepared question rows found for space", result.stderr)


if __name__ == "__main__":
    unittest.main()
