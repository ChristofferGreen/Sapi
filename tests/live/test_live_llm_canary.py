from __future__ import annotations

import os
from pathlib import Path
import shutil
import tempfile
import unittest

import pytest

from tests.conftest import (
    REPO_ROOT,
    bootstrap_site_and_space,
    parse_run_frontmatter,
    run_command,
    run_directories,
    write_source_fixture,
)

@pytest.mark.live_llm
class LiveLlmCanaryTests(unittest.TestCase):
    def test_live_llm_canary_ingest_then_query_smoke_test(self) -> None:
        if os.environ.get("SAPI_RUN_LIVE_CANARY") != "1":
            self.skipTest("Set SAPI_RUN_LIVE_CANARY=1 to execute live LLM canary checks.")
        if shutil.which("codex") is None:
            self.skipTest("Install Codex CLI to execute live LLM canary checks.")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            source_path = write_source_fixture(
                tmp_root,
                filename="live-canary-source.txt",
                content="Live canary source fixture for end-to-end smoke coverage.\n",
            )

            before_runs = run_directories(space_root)
            ingest_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Live Canary Source",
                ]
            )
            self.assertEqual(ingest_result.returncode, 0, msg=ingest_result.stderr)
            ingest_frontmatter = _capture_single_new_run_frontmatter(
                space_root=space_root,
                before_runs=before_runs,
            )
            self.assertEqual("live_llm", ingest_frontmatter["execution_mode"])
            self.assertEqual("ingest_pipeline", ingest_frontmatter["flow_key"])

            before_runs = run_directories(space_root)
            query_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "query.py"),
                    "alpha",
                    "Live canary smoke query",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                ]
            )
            self.assertEqual(query_result.returncode, 0, msg=query_result.stderr)
            query_frontmatter = _capture_single_new_run_frontmatter(
                space_root=space_root,
                before_runs=before_runs,
            )
            self.assertEqual("live_llm", query_frontmatter["execution_mode"])
            self.assertEqual("query_pipeline", query_frontmatter["flow_key"])


def _capture_single_new_run_frontmatter(
    *,
    space_root: Path,
    before_runs: list[Path],
) -> dict[str, object]:
    after_runs = run_directories(space_root)
    created_runs = [path for path in after_runs if path not in before_runs]
    if len(created_runs) != 1:
        raise AssertionError(
            "Expected exactly one new run directory. "
            f"before={[path.name for path in before_runs]} "
            f"after={[path.name for path in after_runs]}"
        )
    return parse_run_frontmatter(created_runs[0] / "run.md")


if __name__ == "__main__":
    unittest.main()
