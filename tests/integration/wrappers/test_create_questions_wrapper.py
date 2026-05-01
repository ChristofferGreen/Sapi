from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.conftest import REPO_ROOT, bootstrap_site_and_space, run_command


class CreateQuestionsWrapperTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()

