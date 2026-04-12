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


GOLDEN_RUN_ENVELOPE_SNAPSHOT = (
    Path(__file__).resolve().parent
    / "run_envelope_snapshot"
    / "query_run_frontmatter.normalized.json"
)


class RunEnvelopeSnapshotGoldenTests(unittest.TestCase):
    def test_query_run_frontmatter_matches_golden_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"

            query_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "query.py"),
                    "alpha",
                    "What is available?",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--mock-llm",
                ]
            )
            self.assertEqual(query_result.returncode, 0, msg=query_result.stderr)

            run_dir = latest_run_directory(space_root)
            frontmatter = parse_run_frontmatter(run_dir / "run.md")
            normalized_frontmatter = _normalize_frontmatter(frontmatter)

            expected = json.loads(GOLDEN_RUN_ENVELOPE_SNAPSHOT.read_text())
            self.assertEqual(normalized_frontmatter, expected)


def _normalize_frontmatter(frontmatter: dict[str, object]) -> dict[str, object]:
    normalized = json.loads(json.dumps(frontmatter))
    normalized["run_id"] = "<run_id>"
    normalized["query_id"] = "<query_id>"
    normalized["started_at"] = "<started_at>"
    normalized["completed_at"] = "<completed_at>"
    toolchain_versions = normalized.get("toolchain_versions")
    if isinstance(toolchain_versions, dict) and "python" in toolchain_versions:
        toolchain_versions["python"] = "<python_version>"
    return normalized


if __name__ == "__main__":
    unittest.main()
