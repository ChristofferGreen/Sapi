from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from tests.conftest import REPO_ROOT, bootstrap_site_and_space, latest_run_directory, parse_run_frontmatter, run_command


class ProfilesPipelineIntegrationTests(unittest.TestCase):
    _RUN_ID_RE = re.compile(r"run_id=(run-[0-9]{8}T[0-9]{6}Z--[a-z0-9]+)")

    def test_profiles_write_canonical_records_and_emit_run_envelope_and_projection_stats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"

            selected_persona_ids = [
                "commenter-1",
                "commenter-2",
            ]

            result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "generate_profiles.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--persona-id",
                    selected_persona_ids[0],
                    "--persona-id",
                    selected_persona_ids[1],
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("projection_stats={'persona_profiles':", result.stdout)
            self.assertIn("'accountability':", result.stdout)

            run_dir = latest_run_directory(space_root)
            frontmatter = parse_run_frontmatter(run_dir / "run.md")
            self.assertEqual(frontmatter["flow_key"], "persona_profile_pipeline")
            self.assertEqual(frontmatter["semantic_flows"], ["persona_profile_generation"])
            self.assertEqual(
                frontmatter["semantic_flow_invocation_counts"],
                {"persona_profile_generation": 2},
            )
            self.assertEqual(frontmatter["lint_error_count"], 0)
            self.assertEqual(frontmatter["lint_warning_count"], 0)
            self.assertEqual(frontmatter["lint_info_count"], 0)
            self.assertEqual(frontmatter["persona_ids"], selected_persona_ids)
            self.assertEqual(frontmatter["pages_changed"], 2)
            self.assertEqual(frontmatter["history_generated"], 2)
            self.assertEqual(frontmatter["history_updated"], 0)
            self.assertEqual(frontmatter["history_reused"], 0)

            lint_payload = json.loads((run_dir / "lint.json").read_text())
            self.assertEqual(lint_payload["schema_version"], "lint_summary_v1")
            self.assertEqual(lint_payload["workflow"], "generate_profiles")
            self.assertEqual(lint_payload["error_count"], 0)
            self.assertEqual(lint_payload["warning_count"], 0)
            self.assertEqual(lint_payload["info_count"], 0)

            for persona_id in selected_persona_ids:
                profile_path = space_root / "profiles" / f"persona-{persona_id}.json"
                self.assertTrue(profile_path.is_file())
                profile_payload = json.loads(profile_path.read_text())
                self.assertEqual(profile_payload["persona_id"], persona_id)
                self.assertEqual(profile_payload["space_name"], "alpha")

                history_path = (
                    space_root / "outputs" / "persona_profile_history" / f"{persona_id}.json"
                )
                self.assertTrue(history_path.is_file())
                history_payload = json.loads(history_path.read_text())
                self.assertEqual(history_payload["schema_version"], "persona_profile_history_v1")
                self.assertEqual(history_payload["space_name"], "alpha")
                self.assertEqual(history_payload["persona_id"], persona_id)
                self.assertEqual(len(history_payload["entries"]), 1)

    def test_same_day_rerun_reuses_history_when_metrics_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            persona_id = "commenter-1"

            first_run = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "generate_profiles.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--persona-id",
                    persona_id,
                    "--mock-llm",
                ]
            )
            self.assertEqual(first_run.returncode, 0, msg=first_run.stderr)

            second_run = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "generate_profiles.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--persona-id",
                    persona_id,
                    "--mock-llm",
                ]
            )
            self.assertEqual(second_run.returncode, 0, msg=second_run.stderr)

            second_run_id = self._extract_run_id(second_run.stdout)
            run_dir = space_root / "runs" / second_run_id
            frontmatter = parse_run_frontmatter(run_dir / "run.md")
            self.assertEqual(frontmatter["history_generated"], 0)
            self.assertEqual(frontmatter["history_updated"], 0)
            self.assertEqual(frontmatter["history_reused"], 1)

            history_path = space_root / "outputs" / "persona_profile_history" / f"{persona_id}.json"
            history_payload = json.loads(history_path.read_text())
            self.assertEqual(len(history_payload["entries"]), 1)

    def test_same_day_rerun_updates_history_when_metrics_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            persona_id = "commenter-1"

            first_run = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "generate_profiles.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--persona-id",
                    persona_id,
                    "--mock-llm",
                ]
            )
            self.assertEqual(first_run.returncode, 0, msg=first_run.stderr)

            (space_root / "topics" / "topic-alpha.json").write_text(
                json.dumps(
                    {
                        "topic_id": "topic-alpha",
                        "title": "Alpha",
                        "comment_section": {
                            "page_ref": "topic:topic-alpha",
                            "comments": [
                                {
                                    "comment_uid": "comment-added--abcde12345",
                                    "persona_id": persona_id,
                                    "body": "Metric-changing comment fixture.",
                                    "comment_no": "pc-001",
                                }
                            ],
                        },
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )

            second_run = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "generate_profiles.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--persona-id",
                    persona_id,
                    "--mock-llm",
                ]
            )
            self.assertEqual(second_run.returncode, 0, msg=second_run.stderr)

            second_run_id = self._extract_run_id(second_run.stdout)
            run_dir = space_root / "runs" / second_run_id
            frontmatter = parse_run_frontmatter(run_dir / "run.md")
            self.assertEqual(frontmatter["history_generated"], 0)
            self.assertEqual(frontmatter["history_updated"], 1)
            self.assertEqual(frontmatter["history_reused"], 0)

            history_path = space_root / "outputs" / "persona_profile_history" / f"{persona_id}.json"
            history_payload = json.loads(history_path.read_text())
            self.assertEqual(len(history_payload["entries"]), 1)
            self.assertEqual(history_payload["entries"][0]["comments_total"], 1)

    def _extract_run_id(self, stdout: str) -> str:
        match = self._RUN_ID_RE.search(stdout)
        if match is None:
            raise AssertionError(f"Unable to locate run_id in command output: {stdout}")
        return match.group(1)


if __name__ == "__main__":
    unittest.main()
