from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.conftest import (
    REPO_ROOT,
    bootstrap_site_and_space,
    latest_run_directory,
    parse_run_frontmatter,
    run_command,
)


class QueryPipelineOutputsIntegrationTests(unittest.TestCase):
    def test_markdown_mode_omits_manifest_and_writes_run_lint_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = bootstrap_site_and_space(Path(tmp), "alpha")
            space_root = site_path / "spaces" / "alpha"

            result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "query.py"),
                    "alpha",
                    "contract question",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--output-format",
                    "markdown",
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            output_dir = _latest_query_output_dir(space_root)
            query_payload = json.loads((output_dir / "query.json").read_text())
            self.assertIsNone(query_payload["manifest_path"])
            self.assertFalse((output_dir / "manifest.json").exists())

            run_dir = latest_run_directory(space_root)
            frontmatter = parse_run_frontmatter(run_dir / "run.md")
            self.assertEqual(frontmatter["flow_key"], "query_pipeline")
            self.assertEqual(frontmatter["status"], "success")
            self.assertEqual(frontmatter["execution_mode"], "mock_llm_test")
            self.assertEqual(frontmatter["semantic_flows"], ["query_synthesis"])
            self.assertEqual(frontmatter["semantic_flow_invocation_counts"], {"query_synthesis": 1})
            self.assertIsNone(frontmatter["manifest_path"])
            self.assertTrue((run_dir / "lint.json").is_file())

            self.assertFalse((site_path / "outputs" / "build_site" / "manifest.json").exists())

    def test_manifest_mode_writes_manifest_and_canonical_manifest_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = bootstrap_site_and_space(Path(tmp), "alpha")
            space_root = site_path / "spaces" / "alpha"

            result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "query.py"),
                    "alpha",
                    "contract question",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--output-format",
                    "mermaid",
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            output_dir = _latest_query_output_dir(space_root)
            query_payload = json.loads((output_dir / "query.json").read_text())
            manifest_path = output_dir / "manifest.json"
            self.assertTrue(manifest_path.is_file())
            self.assertEqual(query_payload["manifest_path"], str(manifest_path.resolve()))

            run_dir = latest_run_directory(space_root)
            frontmatter = parse_run_frontmatter(run_dir / "run.md")
            self.assertEqual(frontmatter["flow_key"], "query_pipeline")
            self.assertEqual(frontmatter["manifest_path"], str(manifest_path.resolve()))


def _latest_query_output_dir(space_root: Path) -> Path:
    query_root = space_root / "outputs" / "query"
    output_dirs = sorted(path for path in query_root.glob("query-*") if path.is_dir())
    if not output_dirs:
        raise AssertionError("Expected at least one query output directory.")
    return output_dirs[-1]


if __name__ == "__main__":
    unittest.main()
