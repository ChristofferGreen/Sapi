from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.conftest import (
    REPO_ROOT,
    assert_lint_artifact,
    assert_run_frontmatter_fields,
    latest_run_directory,
    run_command,
    bootstrap_site_and_space,
    write_source_fixture,
)


class IngestForceModeIntegrationTests(unittest.TestCase):
    def test_force_mode_failure_preserves_partial_artifacts_and_force_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            source_path = write_source_fixture(tmp_root, content="tier3 force-mode fixture\n")

            result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--simulate-terminal-failure",
                    "--force",
                    "--mock-llm",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("status=failed", result.stderr)
            self.assertIn("run_record_path=", result.stderr)

            source_records = sorted((space_root / "sources" / "records").glob("source-*.json"))
            self.assertEqual(len(source_records), 1)

            run_dir = latest_run_directory(space_root)
            run_md_path = run_dir / "run.md"
            lint_path = run_dir / "lint.json"
            assert_run_frontmatter_fields(
                run_md_path,
                expected_fields={
                    "flow_key": "ingest_pipeline",
                    "status": "failed",
                    "execution_mode": "mock_llm_test",
                    "force_mode": True,
                    "rollback_skipped": True,
                },
            )
            assert_lint_artifact(
                lint_path,
                expected_workflow="ingest_source",
            )


if __name__ == "__main__":
    unittest.main()
