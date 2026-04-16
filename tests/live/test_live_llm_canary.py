from __future__ import annotations

import os
from pathlib import Path
import shutil
import tempfile
import unittest

import pytest

from sapi.profiles.persona_catalog import load_seeded_persona_catalog
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
    def test_live_llm_canary_validates_semantic_artifacts_across_flows(self) -> None:
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

            query_id = str(query_frontmatter.get("query_id") or "")
            self.assertTrue(query_id)
            query_artifact_path = space_root / "outputs" / "query" / query_id / "query.json"
            query_payload = _load_json_object(query_artifact_path)
            self.assertEqual(query_payload.get("query_id"), query_id)
            self.assertIn("answer", query_payload)

            (space_root / "topics" / "topic-live-canary.json").write_text(
                '{"topic_id":"topic-live-canary","title":"Live Canary Topic","sections":[{"heading":"Summary","body":"Live canary topic body."}],"source_ids":[]}\n'
            )
            before_runs = run_directories(space_root)
            comments_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "create_comments.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--count",
                    "5",
                    "--comment-page",
                    "topic:topic-live-canary",
                ]
            )
            self.assertEqual(comments_result.returncode, 0, msg=comments_result.stderr)
            comments_frontmatter = _capture_single_new_run_frontmatter(
                space_root=space_root,
                before_runs=before_runs,
            )
            self.assertEqual("live_llm", comments_frontmatter["execution_mode"])
            self.assertEqual("comment_section_pipeline", comments_frontmatter["flow_key"])
            comments_run_id = str(comments_frontmatter.get("run_id") or "")
            self.assertTrue(comments_run_id)
            comments_artifact_path = (
                space_root
                / "runs"
                / comments_run_id
                / "semantic"
                / "comment_section_generation"
                / "topic--topic-live-canary.json"
            )
            comments_payload = _load_json_object(comments_artifact_path)
            self.assertEqual(comments_payload.get("page_ref"), "topic:topic-live-canary")
            self.assertIsInstance(comments_payload.get("comments"), list)

            persona_id = _seeded_persona_ids(count=1)[0]
            before_runs = run_directories(space_root)
            profiles_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "generate_profiles.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--persona-id",
                    persona_id,
                ]
            )
            self.assertEqual(profiles_result.returncode, 0, msg=profiles_result.stderr)
            profiles_frontmatter = _capture_single_new_run_frontmatter(
                space_root=space_root,
                before_runs=before_runs,
            )
            self.assertEqual("live_llm", profiles_frontmatter["execution_mode"])
            self.assertEqual("persona_profile_pipeline", profiles_frontmatter["flow_key"])
            profile_artifact_path = space_root / "profiles" / f"persona-{persona_id}.json"
            profile_payload = _load_json_object(profile_artifact_path)
            self.assertEqual(profile_payload.get("persona_id"), persona_id)
            self.assertEqual(profile_payload.get("space_name"), "alpha")


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


def _load_json_object(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise AssertionError(f"Expected JSON artifact path: {path}")
    import json

    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise AssertionError(f"Expected JSON object payload at: {path}")
    return payload


def _seeded_persona_ids(*, count: int) -> list[str]:
    rows = load_seeded_persona_catalog(repo_root=REPO_ROOT, require_image_files=False)
    return [str(row["persona_id"]) for row in rows[:count]]


if __name__ == "__main__":
    unittest.main()
