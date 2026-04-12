from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from tests.conftest import REPO_ROOT, bootstrap_site_and_space, run_command, write_source_fixture


class RunTruthAdvancementIntegrationTests(unittest.TestCase):
    _RUN_ID_RE = re.compile(r"run_id=(run-[0-9]{8}T[0-9]{6}Z--[a-z0-9]+)")
    _STATE_RELATIVE_PATH = Path("outputs") / "run_truth" / "reconciliation_state.json"

    def test_success_and_success_with_warnings_advance_reconciliation_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"

            source_a = write_source_fixture(tmp_root, filename="source-a.txt", content="run-truth source a\n")
            ingest_success = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_a),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Run Truth Source A",
                    "--mock-llm",
                ]
            )
            self.assertEqual(ingest_success.returncode, 0, msg=ingest_success.stderr)
            ingest_success_run_id = self._extract_run_id(ingest_success.stdout)

            query_success = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "query.py"),
                    "alpha",
                    "run truth query",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--mock-llm",
                ]
            )
            self.assertEqual(query_success.returncode, 0, msg=query_success.stderr)
            query_success_run_id = self._extract_run_id(query_success.stdout)

            self._write_topic_fixture(space_root, topic_id="topic-alpha", title="Alpha")
            comments_success = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "create_comments.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--count",
                    "5",
                    "--comment-page",
                    "topic:topic-alpha",
                    "--mock-llm",
                ]
            )
            self.assertEqual(comments_success.returncode, 0, msg=comments_success.stderr)
            comments_success_run_id = self._extract_run_id(comments_success.stdout)

            profiles_success = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "generate_profiles.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--persona-id",
                    "commenter-1",
                    "--mock-llm",
                ]
            )
            self.assertEqual(profiles_success.returncode, 0, msg=profiles_success.stderr)
            profiles_success_run_id = self._extract_run_id(profiles_success.stdout)

            source_b = write_source_fixture(tmp_root, filename="source-b.txt", content="run-truth source b\n")
            ingest_warning = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_b),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Run Truth Source B",
                    "--build-deferred",
                    "--mock-llm",
                ]
            )
            self.assertEqual(ingest_warning.returncode, 0, msg=ingest_warning.stderr)
            ingest_warning_run_id = self._extract_run_id(ingest_warning.stdout)

            state_payload = self._read_reconciliation_state(space_root)
            flow_states = state_payload["flow_states"]
            self.assertEqual(
                flow_states["ingest_pipeline"]["last_advanced_run_id"],
                ingest_warning_run_id,
            )
            self.assertEqual(
                flow_states["ingest_pipeline"]["last_advanced_status"],
                "success_with_warnings",
            )
            self.assertEqual(
                flow_states["ingest_pipeline"]["consecutive_advanced_runs"],
                2,
            )
            self.assertEqual(
                flow_states["query_pipeline"]["last_advanced_run_id"],
                query_success_run_id,
            )
            self.assertEqual(
                flow_states["query_pipeline"]["consecutive_advanced_runs"],
                1,
            )
            self.assertEqual(
                flow_states["comment_section_pipeline"]["last_advanced_run_id"],
                comments_success_run_id,
            )
            self.assertEqual(
                flow_states["comment_section_pipeline"]["consecutive_advanced_runs"],
                1,
            )
            self.assertEqual(
                flow_states["persona_profile_pipeline"]["last_advanced_run_id"],
                profiles_success_run_id,
            )
            self.assertEqual(
                flow_states["persona_profile_pipeline"]["consecutive_advanced_runs"],
                1,
            )
            self.assertNotEqual(ingest_success_run_id, ingest_warning_run_id)

    def test_failed_runs_do_not_advance_reconciliation_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"

            source_a = write_source_fixture(tmp_root, filename="source-a.txt", content="baseline source\n")
            ingest_success = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_a),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Baseline Source",
                    "--mock-llm",
                ]
            )
            self.assertEqual(ingest_success.returncode, 0, msg=ingest_success.stderr)

            query_success = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "query.py"),
                    "alpha",
                    "baseline query",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--mock-llm",
                ]
            )
            self.assertEqual(query_success.returncode, 0, msg=query_success.stderr)

            self._write_topic_fixture(space_root, topic_id="topic-alpha", title="Alpha")
            comments_success = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "create_comments.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--count",
                    "5",
                    "--comment-page",
                    "topic:topic-alpha",
                    "--mock-llm",
                ]
            )
            self.assertEqual(comments_success.returncode, 0, msg=comments_success.stderr)

            profiles_success = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "generate_profiles.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--persona-id",
                    "commenter-1",
                    "--mock-llm",
                ]
            )
            self.assertEqual(profiles_success.returncode, 0, msg=profiles_success.stderr)

            baseline_state = self._read_reconciliation_state(space_root)

            source_b = write_source_fixture(tmp_root, filename="source-b.txt", content="failing source\n")
            ingest_failed = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_b),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Failing Source",
                    "--simulate-terminal-failure",
                    "--mock-llm",
                ]
            )
            self.assertNotEqual(ingest_failed.returncode, 0)

            query_failed = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "query.py"),
                    "alpha",
                    "failing query",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--simulate-terminal-failure",
                    "--mock-llm",
                ]
            )
            self.assertNotEqual(query_failed.returncode, 0)

            comments_failed = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "create_comments.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--count",
                    "5",
                    "--comment-page",
                    "topic:topic-alpha",
                    "--simulate-terminal-failure",
                    "--mock-llm",
                ]
            )
            self.assertNotEqual(comments_failed.returncode, 0)

            profiles_failed = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "generate_profiles.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--persona-id",
                    "commenter-1",
                    "--simulate-terminal-failure",
                    "--mock-llm",
                ]
            )
            self.assertNotEqual(profiles_failed.returncode, 0)

            state_after_failures = self._read_reconciliation_state(space_root)
            self.assertEqual(baseline_state, state_after_failures)

    def _read_reconciliation_state(self, space_root: Path) -> dict[str, object]:
        path = space_root / self._STATE_RELATIVE_PATH
        self.assertTrue(path.is_file(), str(path))
        payload = json.loads(path.read_text())
        self.assertEqual(payload["schema_version"], "run_truth_reconciliation_v1")
        self.assertIsInstance(payload["flow_states"], dict)
        return payload

    def _extract_run_id(self, output_text: str) -> str:
        match = self._RUN_ID_RE.search(output_text)
        if match is None:
            raise AssertionError(f"Unable to parse run_id from output: {output_text}")
        return match.group(1)

    def _write_topic_fixture(self, space_root: Path, *, topic_id: str, title: str) -> None:
        topic_path = space_root / "topics" / f"{topic_id}.json"
        topic_path.parent.mkdir(parents=True, exist_ok=True)
        topic_path.write_text(
            json.dumps(
                {
                    "topic_id": topic_id,
                    "title": title,
                    "structure_type": "wiki",
                    "sections": [],
                    "claim_ids": [],
                    "source_ids": [],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )


if __name__ == "__main__":
    unittest.main()
