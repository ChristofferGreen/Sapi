from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_JSON_PATH = REPO_ROOT / "package.json"
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"
TESTING_PLAN_PATH = REPO_ROOT / "docs" / "testing_plan.md"


class CiTierMatrixWiringTests(unittest.TestCase):
    def test_package_scripts_match_tier_commands_and_live_marker_policy(self) -> None:
        package_json = json.loads(PACKAGE_JSON_PATH.read_text())
        scripts = package_json.get("scripts", {})
        self.assertIsInstance(scripts, dict)

        test_pr = scripts.get("test:pr")
        test_tier45 = scripts.get("test:tier4-5")
        test_live = scripts.get("test:live")
        self.assertIsInstance(test_pr, str)
        self.assertIsInstance(test_tier45, str)
        self.assertIsInstance(test_live, str)

        self.assertIn("tests/unit", test_pr)
        self.assertIn("tests/integration/failure", test_pr)
        self.assertIn("tests/integration/pipelines", test_pr)
        self.assertIn('-m "not live_llm"', test_pr)

        self.assertIn("tests/integration/build", test_tier45)
        self.assertIn("tests/golden", test_tier45)
        self.assertIn('-m "not live_llm"', test_tier45)

        self.assertIn("tests/live", test_live)
        self.assertIn('-m "live_llm"', test_live)

    def test_ci_workflow_maps_pr_and_nightly_tiers(self) -> None:
        content = WORKFLOW_PATH.read_text()
        self.assertIn("pull_request:", content)
        self.assertIn("schedule:", content)
        self.assertIn("pr-required:", content)
        self.assertIn("nightly-tier4-6:", content)
        self.assertIn("npm run test:pr", content)
        self.assertIn("npm run test:tier4-5", content)
        self.assertIn("npm run test:live", content)
        self.assertIn("continue-on-error: true", content)

    def test_testing_plan_ci_matrix_is_explicit_for_pr_and_nightly(self) -> None:
        content = TESTING_PLAN_PATH.read_text()
        self.assertIn("PR required:", content)
        self.assertIn("Tier 1", content)
        self.assertIn("Tier 2", content)
        self.assertIn("Tier 3", content)
        self.assertIn("Nightly:", content)
        self.assertIn("Tier 4", content)
        self.assertIn("Tier 5", content)
        self.assertIn("Tier 6", content)


if __name__ == "__main__":
    unittest.main()
