from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

import pytest

from tests.conftest import REPO_ROOT, bootstrap_site_and_space, parse_run_frontmatter, run_command

@pytest.mark.live_llm
class LiveLlmCanaryTests(unittest.TestCase):
    def test_live_llm_canary_query_smoke_test(self) -> None:
        if os.environ.get("SAPI_RUN_LIVE_CANARY") != "1":
            self.skipTest("Set SAPI_RUN_LIVE_CANARY=1 to execute live LLM canary checks.")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
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

            run_dirs = sorted((site_path / "spaces" / "alpha" / "runs").glob("run-*"))
            self.assertEqual(1, len(run_dirs))
            frontmatter = parse_run_frontmatter(run_dirs[0] / "run.md")
            self.assertEqual("live_llm", frontmatter["execution_mode"])
            self.assertEqual("query_pipeline", frontmatter["flow_key"])


if __name__ == "__main__":
    unittest.main()
