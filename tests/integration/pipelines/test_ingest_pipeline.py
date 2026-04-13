from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.conftest import (
    REPO_ROOT,
    assert_lint_artifact,
    assert_run_frontmatter_fields,
    bootstrap_site_and_space,
    latest_run_directory,
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
            relation_records = sorted((space_root / "relations").glob("rel-*.json"))
            topic_records = sorted((space_root / "topics").glob("topic-*.json"))
            self.assertEqual(len(source_records), 1)
            self.assertGreaterEqual(len(claim_records), 1)
            self.assertTrue((space_root / "relations").is_dir())
            self.assertEqual(len(topic_records), 0)

            run_dir = latest_run_directory(space_root)
            run_md_path = run_dir / "run.md"
            lint_path = run_dir / "lint.json"

            frontmatter = assert_run_frontmatter_fields(
                run_md_path,
                expected_fields={
                    "flow_key": "ingest_pipeline",
                    "status": "success",
                    "execution_mode": "mock_llm_test",
                    "semantic_flows": ["ingest_extraction", "topic_generation"],
                    "source_ids": [source_records[0].stem],
                    "claims_changed": len(claim_records),
                    "relations_changed": len(relation_records),
                    "topic_pages_changed": len(topic_records),
                    "lint_error_count": 0,
                    "lint_warning_count": 0,
                    "lint_info_count": 0,
                },
            )
            self.assertEqual(
                frontmatter["semantic_flow_invocation_counts"],
                {"ingest_extraction": 1, "topic_generation": 1},
            )
            self.assertEqual(frontmatter["run_id"], run_dir.name)

            assert_lint_artifact(
                lint_path,
                expected_workflow="ingest_source",
                expected_error_count=0,
                expected_warning_count=0,
                expected_info_count=0,
            )

            build_manifest_path = site_path / "outputs" / "build_site" / "manifest.json"
            self.assertTrue(build_manifest_path.is_file())
            self.assertIn("build_manifest_path=", result.stdout)


if __name__ == "__main__":
    unittest.main()
