from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

import scripts.ingest_source as ingest_source
import scripts.query as query_entrypoint
from tests.conftest import (
    assert_rollback_cleanup,
    bootstrap_site_and_space,
    write_source_fixture,
)


class PostprocessFailureRollbackIntegrationTests(unittest.TestCase):
    def test_postprocess_failure_rolls_back_invocation_scoped_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            source_path = write_source_fixture(tmp_root, content="postprocess rollback fixture\n")

            stderr = io.StringIO()
            argv = [
                "ingest_source.py",
                "alpha",
                str(source_path),
                "--registry-path",
                str(site_path / "spaces.toml"),
                "--source-title",
                "Rollback Fixture",
                "--mock-llm",
            ]
            with patch.object(
                ingest_source,
                "_run_coalesced_ingest_topic_postprocess",
                side_effect=RuntimeError("forced deterministic postprocess failure"),
            ):
                with patch("sys.argv", argv):
                    with redirect_stderr(stderr):
                        exit_code = ingest_source.main()

            self.assertNotEqual(exit_code, 0)
            self.assertIn("forced deterministic postprocess failure", stderr.getvalue())

            assert_rollback_cleanup(
                space_root,
                empty_globs=(
                    "sources/records/*.json",
                    "claims/*.json",
                    "relations/*.json",
                    "topics/*.json",
                ),
                absent_paths=(site_path / "outputs" / "build_site" / "manifest.json",),
            )

    def test_query_non_markdown_postprocess_failure_rolls_back_query_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"

            stderr = io.StringIO()
            argv = [
                "query.py",
                "alpha",
                "What changed?",
                "--registry-path",
                str(site_path / "spaces.toml"),
                "--output-format",
                "slides",
                "--mock-llm",
            ]
            with patch.object(
                query_entrypoint,
                "build_query_artifacts",
                side_effect=RuntimeError("forced query postprocess failure"),
            ):
                with patch("sys.argv", argv):
                    with redirect_stderr(stderr):
                        exit_code = query_entrypoint.main()

            self.assertNotEqual(exit_code, 0)
            self.assertIn("forced query postprocess failure", stderr.getvalue())
            assert_rollback_cleanup(
                space_root,
                empty_globs=("outputs/query/query-*",),
            )


if __name__ == "__main__":
    unittest.main()
