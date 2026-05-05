from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.conftest import REPO_ROOT, run_command


class SourceScoutingWrapperTests(unittest.TestCase):
    def test_scout_and_import_wrappers_report_usage_errors(self) -> None:
        scout = run_command(["bash", str(REPO_ROOT / "scout_sources.sh")])
        self.assertEqual(scout.returncode, 2)
        self.assertIn("Usage: scout_sources.sh", scout.stderr)

        importer = run_command(["bash", str(REPO_ROOT / "import_scouted_sources.sh")])
        self.assertEqual(importer.returncode, 2)
        self.assertIn("Usage: import_scouted_sources.sh", importer.stderr)

    def test_scout_wrapper_rejects_mock_plan_without_explicit_mock_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = Path(tmp) / "site-a"
            run_command(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "Example Site"], check=True)
            run_command(
                [
                    "bash",
                    str(REPO_ROOT / "create_space.sh"),
                    str(site_path),
                    "compilers",
                    "--seed-example-questions",
                ],
                check=True,
            )

            result = run_command(
                [
                    "bash",
                    str(REPO_ROOT / "scout_sources.sh"),
                    str(site_path),
                    "compilers",
                    "question-profile-guided-optimization",
                    "--mock-candidate-plan",
                    str(REPO_ROOT / "tests" / "example" / "scouting_plan.tsv"),
                ]
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--mock-candidate-plan may only be used with --mock-llm", result.stderr)

    def test_ingest_wrapper_rejects_unclear_restricted_source_alias(self) -> None:
        result = run_command(
            [
                "bash",
                str(REPO_ROOT / "ingest.sh"),
                "/tmp/missing-site",
                "alpha",
                "/tmp/source.pdf",
                "--allow-not-publicly-accessible",
            ]
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("use --restricted-source", result.stderr)


if __name__ == "__main__":
    unittest.main()
