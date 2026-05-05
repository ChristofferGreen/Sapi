from __future__ import annotations

import unittest

from tests.conftest import REPO_ROOT


class ExampleRunnerScoutingContractTests(unittest.TestCase):
    def test_example_runner_scouts_and_imports_five_sources_before_direct_ingest(self) -> None:
        script = (REPO_ROOT / "tests" / "example" / "run_example_site.sh").read_text()
        self.assertIn("SCOUT_DONE=0", script)
        self.assertIn("SCOUT_IMPORT_DONE=0", script)
        self.assertIn("scout_sources.sh", script)
        self.assertIn("import_scouted_sources.sh", script)
        self.assertIn("--count 5", script)
        self.assertIn("SAPI_EXAMPLE_LIVE_SCOUTING", script)
        self.assertIn("is_scouted_ingest_row", script)

    def test_example_scouting_plan_identifies_space_question_and_five_candidates(self) -> None:
        rows = [
            line
            for line in (REPO_ROOT / "tests" / "example" / "scouting_plan.tsv").read_text().splitlines()
            if line.strip() and not line.startswith("#")
        ]
        self.assertEqual(len(rows), 5)
        spaces = set()
        questions = set()
        for row in rows:
            parts = row.split("\t")
            self.assertEqual(len(parts), 9)
            spaces.add(parts[0])
            questions.add(parts[1])
        self.assertEqual(spaces, {"compilers"})
        self.assertEqual(questions, {"question-profile-guided-optimization"})


if __name__ == "__main__":
    unittest.main()
