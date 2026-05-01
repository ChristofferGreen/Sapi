from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

from tests.conftest import REPO_ROOT
from sapi.questions.prepared_questions import parse_prepared_question_seed_tsv


class ExampleQuestionSeedTests(unittest.TestCase):
    def test_example_seed_data_has_ten_questions_for_every_space_and_subspace(self) -> None:
        subspaces_path = REPO_ROOT / "tests" / "example" / "subspaces.tsv"
        expected_spaces: set[str] = set()
        for raw_line in subspaces_path.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parent_slug, _parent_title, child_slug, _child_title = raw_line.split("\t")
            expected_spaces.add(parent_slug)
            expected_spaces.add(child_slug)

        rows = parse_prepared_question_seed_tsv(
            REPO_ROOT / "tests" / "example" / "prepared_questions.tsv"
        )
        counts = Counter(row.space_name for row in rows)

        self.assertEqual(set(counts), expected_spaces)
        self.assertTrue(all(counts[space_name] == 10 for space_name in expected_spaces))

    def test_example_runner_relies_on_create_space_for_question_seeding(self) -> None:
        create_space_text = (REPO_ROOT / "create_space.sh").read_text()
        runner_text = (REPO_ROOT / "tests" / "example" / "run_example_site.sh").read_text()

        self.assertIn("tests/example/prepared_questions.tsv", create_space_text)
        self.assertIn("create_questions.sh", create_space_text)
        self.assertNotIn("003-seed-prepared-questions", runner_text)
        self.assertNotIn("QUESTIONS_TSV", runner_text)


if __name__ == "__main__":
    unittest.main()
