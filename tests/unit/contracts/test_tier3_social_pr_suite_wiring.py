from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_JSON_PATH = REPO_ROOT / "package.json"
TESTING_PLAN_PATH = REPO_ROOT / "docs" / "testing_plan.md"
COMMENTS_TEST_PATH = REPO_ROOT / "tests" / "integration" / "pipelines" / "test_comments_pipeline.py"
PROFILES_TEST_PATH = REPO_ROOT / "tests" / "integration" / "pipelines" / "test_profiles_pipeline.py"


class Tier3SocialPrSuiteWiringTests(unittest.TestCase):
    def test_pr_suite_command_includes_pipeline_integration_directory(self) -> None:
        package_json = json.loads(PACKAGE_JSON_PATH.read_text())
        scripts = package_json.get("scripts", {})
        self.assertIsInstance(scripts, dict)
        test_pr_command = scripts.get("test:pr")
        self.assertIsInstance(test_pr_command, str)
        self.assertIn("tests/integration/pipelines", test_pr_command)

    def test_tier3_social_modules_are_listed_and_use_mock_llm_mode(self) -> None:
        testing_plan_text = TESTING_PLAN_PATH.read_text()
        self.assertIn("PR required:", testing_plan_text)
        self.assertIn("Tier 3", testing_plan_text)
        self.assertIn("test_comments_pipeline.py", testing_plan_text)
        self.assertIn("test_profiles_pipeline.py", testing_plan_text)

        for path in (COMMENTS_TEST_PATH, PROFILES_TEST_PATH):
            self.assertTrue(path.is_file(), str(path))
            self.assertIn("--mock-llm", path.read_text(), str(path))


if __name__ == "__main__":
    unittest.main()
