from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.create_comments as create_comments
import scripts.generate_profiles as generate_profiles
import scripts.ingest_source as ingest_source
import scripts.query as query_entrypoint
from sapi.profiles.persona_catalog import load_seeded_persona_catalog
from tests.conftest import (
    REPO_ROOT,
    bootstrap_site_and_space,
    latest_run_directory,
    parse_run_frontmatter,
    write_source_fixture,
)


class SemanticAttemptCountRepairIntegrationTests(unittest.TestCase):
    def test_query_repair_success_counts_both_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = bootstrap_site_and_space(Path(tmp), "alpha")
            argv = [
                "query.py",
                "alpha",
                "repair-check query",
                "--registry-path",
                str(site_path / "spaces.toml"),
                "--mock-llm",
            ]

            original = query_entrypoint._MockQuerySynthesisClient.generate_semantic_json
            call_count = 0

            def flaky_first_attempt(
                self: query_entrypoint._MockQuerySynthesisClient,
                request: object,
            ) -> str:
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return json.dumps({"query_id": "broken"})
                return original(self, request)

            with patch.object(
                query_entrypoint._MockQuerySynthesisClient,
                "generate_semantic_json",
                new=flaky_first_attempt,
            ):
                with patch("sys.argv", argv):
                    exit_code = query_entrypoint.main()

            self.assertEqual(exit_code, 0)
            run_dir = latest_run_directory(site_path / "spaces" / "alpha")
            frontmatter = parse_run_frontmatter(run_dir / "run.md")
            self.assertEqual(frontmatter["flow_key"], "query_pipeline")
            self.assertEqual(frontmatter["llm_attempt_count"], 2)
            self.assertEqual(frontmatter["semantic_flow_invocation_counts"], {"query_synthesis": 1})

    def test_comments_repair_success_uses_shared_retry_budget_and_counts_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            (space_root / "topics" / "topic-alpha.json").write_text(
                json.dumps(
                    {
                        "topic_id": "topic-alpha",
                        "title": "Alpha",
                        "sections": [{"heading": "Summary", "body": "Topic fixture"}],
                        "source_ids": [],
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
            argv = [
                "create_comments.py",
                "alpha",
                "--registry-path",
                str(site_path / "spaces.toml"),
                "--count",
                "5",
                "--mock-llm",
            ]

            original = create_comments._MockCommentSectionClient.generate_semantic_json
            call_count = 0

            def flaky_first_attempt(
                self: create_comments._MockCommentSectionClient,
                request: object,
            ) -> str:
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return json.dumps({"page_ref": "topic:topic-alpha"})
                return original(self, request)

            with patch.object(
                create_comments._MockCommentSectionClient,
                "generate_semantic_json",
                new=flaky_first_attempt,
            ):
                with patch("sys.argv", argv):
                    exit_code = create_comments.main()

            self.assertEqual(exit_code, 0)
            run_dir = latest_run_directory(space_root)
            frontmatter = parse_run_frontmatter(run_dir / "run.md")
            self.assertEqual(frontmatter["flow_key"], "comment_section_pipeline")
            self.assertEqual(frontmatter["llm_attempt_count"], 2)
            self.assertEqual(frontmatter["semantic_flow_invocation_counts"], {"comment_section_generation": 1})

    def test_ingest_repair_success_counts_retries_plus_other_flows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            source_path = write_source_fixture(
                tmp_root,
                filename="repair-ingest-source.txt",
                content="ingest repair fixture\n",
            )
            argv = [
                "ingest_source.py",
                "alpha",
                str(source_path),
                "--registry-path",
                str(site_path / "spaces.toml"),
                "--source-title",
                "Repair Ingest Source",
                "--mock-llm",
            ]

            original = ingest_source._MockIngestExtractionClient.generate_semantic_json
            call_count = 0

            def flaky_first_attempt(
                self: ingest_source._MockIngestExtractionClient,
                request: object,
            ) -> str:
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return json.dumps({"claims": [], "relations": []})
                return original(self, request)

            with patch.object(
                ingest_source._MockIngestExtractionClient,
                "generate_semantic_json",
                new=flaky_first_attempt,
            ):
                with patch("sys.argv", argv):
                    exit_code = ingest_source.main()

            self.assertEqual(exit_code, 0)
            run_dir = latest_run_directory(space_root)
            frontmatter = parse_run_frontmatter(run_dir / "run.md")
            self.assertEqual(frontmatter["flow_key"], "ingest_pipeline")
            self.assertEqual(
                frontmatter["semantic_flow_invocation_counts"],
                {"ingest_extraction": 1, "topic_generation": 1},
            )
            self.assertEqual(frontmatter["llm_attempt_count"], 3)

    def test_profiles_repair_success_counts_both_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = bootstrap_site_and_space(Path(tmp), "alpha")
            persona_id = self._seeded_persona_ids(count=1)[0]
            argv = [
                "generate_profiles.py",
                "alpha",
                "--registry-path",
                str(site_path / "spaces.toml"),
                "--persona-id",
                persona_id,
                "--mock-llm",
            ]

            original = generate_profiles._MockPersonaProfileClient.generate_semantic_json
            call_count = 0

            def flaky_first_attempt(
                self: generate_profiles._MockPersonaProfileClient,
                request: object,
            ) -> str:
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return json.dumps({"persona_id": persona_id})
                return original(self, request)

            with patch.object(
                generate_profiles._MockPersonaProfileClient,
                "generate_semantic_json",
                new=flaky_first_attempt,
            ):
                with patch("sys.argv", argv):
                    exit_code = generate_profiles.main()

            self.assertEqual(exit_code, 0)
            run_dir = latest_run_directory(site_path / "spaces" / "alpha")
            frontmatter = parse_run_frontmatter(run_dir / "run.md")
            self.assertEqual(frontmatter["flow_key"], "persona_profile_pipeline")
            self.assertEqual(frontmatter["llm_attempt_count"], 2)
            self.assertEqual(
                frontmatter["semantic_flow_invocation_counts"],
                {"persona_profile_generation": 1},
            )

    def _seeded_persona_ids(self, *, count: int) -> list[str]:
        rows = load_seeded_persona_catalog(repo_root=REPO_ROOT, require_image_files=False)
        return [str(row["persona_id"]) for row in rows[:count]]


if __name__ == "__main__":
    unittest.main()
