from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


class Todo0200BootstrapTests(unittest.TestCase):
    def test_root_layout_contains_required_bootstrap_paths(self) -> None:
        required_dirs = [
            ".skills",
            "personas",
            "personas/profile_images",
            "sapi",
            "scripts",
            "tests",
            "docs",
            "schemas",
            "ai_flows/generation_specs",
        ]
        for rel in required_dirs:
            self.assertTrue((REPO_ROOT / rel).is_dir(), rel)

        required_files = [
            "package.json",
            "package-lock.json",
            ".nvmrc",
            "create_site.sh",
            "create_space.sh",
            "create_subspaces.sh",
            "ingest.sh",
            "query.sh",
            "create_comments.sh",
            "generate_profiles.sh",
            "regenerate_web.sh",
            "validate.sh",
            "evaluate_source.sh",
        ]
        for rel in required_files:
            self.assertTrue((REPO_ROOT / rel).is_file(), rel)

        package_json = json.loads((REPO_ROOT / "package.json").read_text())
        lock_json = json.loads((REPO_ROOT / "package-lock.json").read_text())
        self.assertEqual(package_json["name"], "sapi")
        self.assertEqual(lock_json["name"], "sapi")
        self.assertTrue((REPO_ROOT / ".nvmrc").read_text().strip())

    def test_wrapper_usage_signatures_match_design_contract(self) -> None:
        expected_usage = {
            "create_site.sh": "Usage: create_site.sh <site_path> <site_name>",
            "create_space.sh": "Usage: create_space.sh <site_path> <space_name>",
            "create_subspaces.sh": "Usage: create_subspaces.sh <site_path> <subspaces_tsv>",
            "ingest.sh": "Usage: ingest.sh <site_path> <space_name> <source_path_or_url> [--force] [--verbose]",
            "create_comments.sh": "Usage: create_comments.sh <site_path> <space_name> --count <n> [--verbose] [--comment-user ...] [--comment-page ...] [--comment-seed ...] [--comment-evidence-mode ...]",
            "generate_profiles.sh": "Usage: generate_profiles.sh <site_path> <space_name> [--persona-id <persona_id> ...] [--verbose]",
            "regenerate_web.sh": "Usage: regenerate_web.sh <site_path> [space_name] [--verbose]",
            "query.sh": "Usage: query.sh <site_path> <space_name> <question> [--verbose]",
            "validate.sh": "Usage: validate.sh <site_path> <space_name> [--workflow ...] [--run-id ...]",
            "evaluate_source.sh": "Usage: evaluate_source.sh <site_path> <space_name> <source_path_or_url> [--out <artifact_dir>] [--comments <n>] [--comment-user ...] [--comment-page ...] [--verbose]",
        }

        for script_name, usage_line in expected_usage.items():
            script_path = REPO_ROOT / script_name
            self.assertTrue(os.access(script_path, os.X_OK), script_name)
            result = subprocess.run(
                [str(script_path)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2, script_name)
            self.assertIn(usage_line, result.stderr, script_name)

    def test_readme_points_to_authoritative_docs_and_reconstruction_status(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text()
        self.assertIn("This repository is in reconstruction mode", readme)
        self.assertIn("docs/contract_index.md", readme)
        self.assertIn("docs/design.md", readme)
        self.assertIn("docs/low_level.md", readme)
        self.assertIn("docs/testing_plan.md", readme)


if __name__ == "__main__":
    unittest.main()
