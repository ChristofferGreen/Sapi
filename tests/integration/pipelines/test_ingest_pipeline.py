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
    write_source_fixture,
)


class IngestPipelineIntegrationTests(unittest.TestCase):
    def test_ingest_mock_mode_writes_canonical_artifacts_and_run_lint_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            source_path = write_source_fixture(tmp_root, content="tier3 ingest fixture\n")

            result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Tier3 Ingest Fixture",
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            source_records = sorted((space_root / "sources" / "records").glob("source-*.json"))
            claim_records = sorted((space_root / "claims").glob("claim-*.json"))
            topic_records = sorted((space_root / "topics").glob("topic-*.json"))
            self.assertEqual(len(source_records), 1)
            self.assertGreaterEqual(len(claim_records), 1)
            self.assertEqual(len(topic_records), 1)

            run_dir = latest_run_directory(space_root)
            run_md_path = run_dir / "run.md"
            lint_path = run_dir / "lint.json"
            self.assertTrue(run_md_path.is_file())
            self.assertTrue(lint_path.is_file())

            frontmatter = parse_run_frontmatter(run_md_path)
            self.assertEqual(frontmatter["flow_key"], "ingest_pipeline")
            self.assertEqual(frontmatter["status"], "success")
            self.assertEqual(frontmatter["execution_mode"], "mock_llm_test")
            self.assertEqual(frontmatter["semantic_flows"], ["ingest_extraction", "topic_generation"])
            self.assertEqual(
                frontmatter["semantic_flow_invocation_counts"],
                {"ingest_extraction": 1, "topic_generation": 1},
            )

            lint_payload = json.loads(lint_path.read_text())
            self.assertEqual(lint_payload["workflow"], "ingest_source")
            self.assertEqual(lint_payload["error_count"], 0)

            build_manifest_path = site_path / "outputs" / "build_site" / "manifest.json"
            self.assertTrue(build_manifest_path.is_file())
            self.assertIn("build_manifest_path=", result.stdout)


if __name__ == "__main__":
    unittest.main()
