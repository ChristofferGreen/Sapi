from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.conftest import (
    REPO_ROOT,
    assert_lint_artifact,
    bootstrap_site_and_space,
    latest_run_directory,
    parse_run_frontmatter,
    run_command,
)


class OverviewPipelineIntegrationTests(unittest.TestCase):
    def test_overview_pipeline_writes_canonical_artifacts_and_run_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"

            _seed_json(
                space_root / "sources" / "records" / "source-alpha--aaaaaaaaaaaa.json",
                {"source_id": "source-alpha--aaaaaaaaaaaa", "title": "Source Alpha"},
            )
            _seed_json(
                space_root / "claims" / "claim-alpha--bbbbbbbbbbbb.json",
                {
                    "claim_id": "claim-alpha--bbbbbbbbbbbb",
                    "source_id": "source-alpha--aaaaaaaaaaaa",
                    "text": "Alpha supports a shared overview contract.",
                },
            )
            _seed_json(
                space_root / "relations" / "supports:claim-alpha--bbbbbbbbbbbb->claim-alpha--bbbbbbbbbbbb.json",
                {"relation_id": "supports:claim-alpha--bbbbbbbbbbbb->claim-alpha--bbbbbbbbbbbb"},
            )
            _seed_json(
                space_root / "topics" / "topic-alpha--cccccccccccc.json",
                {
                    "topic_id": "topic-alpha--cccccccccccc",
                    "title": "Topic Alpha",
                    "claim_ids": ["claim-alpha--bbbbbbbbbbbb"],
                    "source_ids": ["source-alpha--aaaaaaaaaaaa"],
                },
            )

            result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "generate_overview.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("scripts/generate_overview.py overview complete", result.stdout)

            overview_root = space_root / "outputs" / "space_overview" / "space--alpha"
            context_payload = json.loads((overview_root / "context.json").read_text())
            overview_payload = json.loads((overview_root / "overview.json").read_text())
            article_text = (overview_root / "article.md").read_text()

            self.assertEqual(context_payload["metadata"]["overview_id"], "space--alpha")
            self.assertEqual(overview_payload["metadata"]["overview_id"], "space--alpha")
            self.assertEqual(overview_payload["metadata"]["scope_kind"], "space")
            self.assertEqual(len(overview_payload["sections"]), 5)
            self.assertEqual(
                overview_payload["references"]["source_ids"],
                ["source-alpha--aaaaaaaaaaaa"],
            )
            self.assertEqual(
                overview_payload["references"]["claim_ids"],
                ["claim-alpha--bbbbbbbbbbbb"],
            )
            self.assertIn("# State of the Evidence in alpha", article_text)
            self.assertIn("## Topic framing", article_text)

            run_dir = latest_run_directory(space_root)
            frontmatter = parse_run_frontmatter(run_dir / "run.md")
            self.assertEqual(frontmatter["flow_key"], "overview_pipeline")
            self.assertEqual(frontmatter["semantic_flows"], ["space_overview_generation"])
            self.assertEqual(
                frontmatter["semantic_flow_invocation_counts"],
                {"space_overview_generation": 1},
            )
            self.assertEqual(frontmatter["overview_id"], "space--alpha")
            self.assertEqual(frontmatter["scope_kind"], "space")
            self.assertEqual(frontmatter["input_signature"], context_payload["freshness"]["input_signature"])
            self.assertEqual(frontmatter["refresh_decision"], "refresh")
            self.assertEqual(frontmatter["refresh_reason"], "artifacts_missing_or_invalid")
            self.assertFalse(frontmatter["force_mode"])
            self.assertEqual(frontmatter["status"], "success")
            assert_lint_artifact(
                run_dir / "lint.json",
                expected_workflow="generate_overview",
                expected_error_count=0,
                expected_warning_count=0,
                expected_info_count=0,
            )

    def test_overview_pipeline_handles_no_source_context_as_success_with_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"

            result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "generate_overview.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            overview_root = space_root / "outputs" / "space_overview" / "space--alpha"
            overview_payload = json.loads((overview_root / "overview.json").read_text())
            self.assertEqual(overview_payload["references"]["source_ids"], [])
            self.assertEqual(overview_payload["references"]["claim_ids"], [])
            self.assertEqual(overview_payload["references"]["citation_anchors"], [])
            self.assertTrue(overview_payload["warnings"])
            for section in overview_payload["sections"]:
                self.assertEqual(section["source_ids"], [])
                self.assertEqual(section["claim_ids"], [])
                self.assertEqual(section["citation_anchor_ids"], [])

            run_dir = latest_run_directory(space_root)
            frontmatter = parse_run_frontmatter(run_dir / "run.md")
            self.assertEqual(frontmatter["status"], "success_with_warnings")
            self.assertEqual(frontmatter["source_records_used"], 0)
            self.assertEqual(frontmatter["refresh_decision"], "refresh")

    def test_overview_pipeline_terminal_failure_rolls_back_outputs_and_run_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            _seed_json(
                space_root / "sources" / "records" / "source-alpha--aaaaaaaaaaaa.json",
                {"source_id": "source-alpha--aaaaaaaaaaaa", "title": "Source Alpha"},
            )

            result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "generate_overview.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--simulate-terminal-failure",
                    "--mock-llm",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Simulated terminal overview failure", result.stderr)
            self.assertEqual(
                list((space_root / "outputs" / "space_overview").glob("space--alpha")),
                [],
            )
            self.assertEqual(list((space_root / "runs").glob("*/run.md")), [])
            self.assertEqual(list((space_root / "runs").glob("*/lint.json")), [])

    def test_overview_pipeline_skips_semantic_regeneration_when_input_signature_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"

            _seed_json(
                space_root / "sources" / "records" / "source-alpha--aaaaaaaaaaaa.json",
                {"source_id": "source-alpha--aaaaaaaaaaaa", "title": "Source Alpha"},
            )

            first = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "generate_overview.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--mock-llm",
                ]
            )
            self.assertEqual(first.returncode, 0, msg=first.stderr)

            overview_root = space_root / "outputs" / "space_overview" / "space--alpha"
            first_overview_text = (overview_root / "overview.json").read_text()
            first_article_text = (overview_root / "article.md").read_text()

            second = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "generate_overview.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--mock-llm",
                ]
            )
            self.assertEqual(second.returncode, 0, msg=second.stderr)

            run_dir = latest_run_directory(space_root)
            frontmatter = parse_run_frontmatter(run_dir / "run.md")
            self.assertEqual(frontmatter["refresh_decision"], "skip")
            self.assertEqual(frontmatter["refresh_reason"], "no_content_change")
            self.assertEqual(frontmatter["semantic_flows"], [])
            self.assertEqual(frontmatter["semantic_flow_invocation_counts"], {})
            self.assertEqual(frontmatter["llm_attempt_count"], 0)
            self.assertFalse(frontmatter["force_mode"])
            self.assertEqual(first_overview_text, (overview_root / "overview.json").read_text())
            self.assertEqual(first_article_text, (overview_root / "article.md").read_text())

    def test_overview_pipeline_force_mode_bypasses_unchanged_signature_skip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"

            _seed_json(
                space_root / "sources" / "records" / "source-alpha--aaaaaaaaaaaa.json",
                {"source_id": "source-alpha--aaaaaaaaaaaa", "title": "Source Alpha"},
            )

            first = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "generate_overview.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--mock-llm",
                ]
            )
            self.assertEqual(first.returncode, 0, msg=first.stderr)

            forced = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "generate_overview.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--mock-llm",
                    "--force",
                ]
            )
            self.assertEqual(forced.returncode, 0, msg=forced.stderr)

            run_dir = latest_run_directory(space_root)
            frontmatter = parse_run_frontmatter(run_dir / "run.md")
            self.assertEqual(frontmatter["refresh_decision"], "refresh")
            self.assertEqual(frontmatter["refresh_reason"], "force_mode")
            self.assertEqual(frontmatter["semantic_flows"], ["space_overview_generation"])
            self.assertEqual(
                frontmatter["semantic_flow_invocation_counts"],
                {"space_overview_generation": 1},
            )
            self.assertTrue(frontmatter["force_mode"])


def _seed_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    unittest.main()
