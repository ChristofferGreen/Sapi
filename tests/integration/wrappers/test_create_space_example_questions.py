from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.conftest import REPO_ROOT, run_command


class CreateSpaceExampleQuestionSeedTests(unittest.TestCase):
    def test_example_space_creation_seeds_prepared_questions_and_front_page(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = Path(tmp) / "site-a"
            create_site = run_command(
                ["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "Example Site"]
            )
            self.assertEqual(create_site.returncode, 0, msg=create_site.stderr)

            create_space = run_command(
                ["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), "philosophy"]
            )
            self.assertEqual(create_space.returncode, 0, msg=create_space.stderr)
            self.assertIn("questions=10", create_space.stdout)

            question_paths = sorted((site_path / "spaces" / "philosophy" / "questions").glob("question-*.json"))
            self.assertEqual(len(question_paths), 10)
            first_question = json.loads(question_paths[0].read_text())
            self.assertEqual(first_question["scope"]["space_name"], "philosophy")

            build_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "philosophy",
                ]
            )
            self.assertEqual(build_result.returncode, 0, msg=build_result.stderr)

            home_text = (site_path / "spaces" / "philosophy" / "site" / "index.html").read_text()
            self.assertIn('data-front-page="questions"', home_text)
            self.assertIn("What kinds of explanation are most promising for consciousness?", home_text)
            self.assertIn('href="questions/question-consciousness-explanation.html"', home_text)

    def test_example_subspace_creation_seeds_its_own_question_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = Path(tmp) / "site-a"
            run_command(
                ["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "Example Site"],
                check=True,
            )
            create_space = run_command(
                ["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), "mind"]
            )

            self.assertEqual(create_space.returncode, 0, msg=create_space.stderr)
            question_paths = sorted((site_path / "spaces" / "mind" / "questions").glob("question-*.json"))
            self.assertEqual(len(question_paths), 10)
            scopes = {json.loads(path.read_text())["scope"]["space_name"] for path in question_paths}
            self.assertEqual(scopes, {"mind"})


if __name__ == "__main__":
    unittest.main()
