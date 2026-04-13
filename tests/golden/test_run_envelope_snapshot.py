from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.profiles.persona_catalog import load_seeded_persona_catalog
from tests.conftest import (
    REPO_ROOT,
    bootstrap_site_and_space,
    parse_run_frontmatter,
    run_directories,
    run_command,
    write_source_fixture,
)


GOLDEN_QUERY_RUN_ENVELOPE_SNAPSHOT = (
    Path(__file__).resolve().parent
    / "run_envelope_snapshot"
    / "query_run_frontmatter.normalized.json"
)
GOLDEN_INGEST_RUN_ENVELOPE_SNAPSHOT = (
    Path(__file__).resolve().parent
    / "run_envelope_snapshot"
    / "ingest_run_frontmatter.normalized.json"
)
GOLDEN_COMMENTS_RUN_ENVELOPE_SNAPSHOT = (
    Path(__file__).resolve().parent
    / "run_envelope_snapshot"
    / "comments_run_frontmatter.normalized.json"
)
GOLDEN_PROFILES_RUN_ENVELOPE_SNAPSHOT = (
    Path(__file__).resolve().parent
    / "run_envelope_snapshot"
    / "profiles_run_frontmatter.normalized.json"
)


class RunEnvelopeSnapshotGoldenTests(unittest.TestCase):
    def test_ingest_run_frontmatter_matches_golden_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            source_path = write_source_fixture(
                tmp_root,
                filename="run-envelope-ingest-source.txt",
                content="run envelope ingest fixture\n",
            )

            frontmatter = _run_and_capture_new_frontmatter(
                space_root=space_root,
                cmd=[
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Run Envelope Ingest Fixture",
                    "--mock-llm",
                ],
            )
            normalized_frontmatter = _normalize_frontmatter(frontmatter)

            expected = json.loads(GOLDEN_INGEST_RUN_ENVELOPE_SNAPSHOT.read_text())
            self.assertEqual(normalized_frontmatter, expected)

    def test_query_run_frontmatter_matches_golden_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"

            frontmatter = _run_and_capture_new_frontmatter(
                space_root=space_root,
                cmd=[
                    "python3",
                    str(REPO_ROOT / "scripts" / "query.py"),
                    "alpha",
                    "What is available?",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--mock-llm",
                ],
            )
            normalized_frontmatter = _normalize_frontmatter(frontmatter)

            expected = json.loads(GOLDEN_QUERY_RUN_ENVELOPE_SNAPSHOT.read_text())
            self.assertEqual(normalized_frontmatter, expected)

    def test_comments_run_frontmatter_matches_golden_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            source_path = write_source_fixture(
                tmp_root,
                filename="run-envelope-comments-source.txt",
                content="run envelope comments fixture\n",
            )

            ingest_frontmatter = _run_and_capture_new_frontmatter(
                space_root=space_root,
                cmd=[
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Run Envelope Comments Fixture",
                    "--mock-llm",
                ],
            )
            self.assertEqual(ingest_frontmatter["flow_key"], "ingest_pipeline")

            second_source_path = write_source_fixture(
                tmp_root,
                filename="run-envelope-comments-source-2.txt",
                content="run envelope comments fixture source two\n",
            )
            second_ingest_frontmatter = _run_and_capture_new_frontmatter(
                space_root=space_root,
                cmd=[
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(second_source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Run Envelope Comments Fixture Two",
                    "--mock-llm",
                ],
            )
            self.assertEqual(second_ingest_frontmatter["flow_key"], "ingest_pipeline")

            comments_frontmatter = _run_and_capture_new_frontmatter(
                space_root=space_root,
                cmd=[
                    "python3",
                    str(REPO_ROOT / "scripts" / "create_comments.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--count",
                    "5",
                    "--mock-llm",
                ],
            )
            normalized_frontmatter = _normalize_frontmatter(comments_frontmatter)

            expected = json.loads(GOLDEN_COMMENTS_RUN_ENVELOPE_SNAPSHOT.read_text())
            self.assertEqual(normalized_frontmatter, expected)

    def test_profiles_run_frontmatter_matches_golden_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            persona_id = _seeded_persona_ids(count=1)[0]

            profiles_frontmatter = _run_and_capture_new_frontmatter(
                space_root=space_root,
                cmd=[
                    "python3",
                    str(REPO_ROOT / "scripts" / "generate_profiles.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--persona-id",
                    persona_id,
                    "--mock-llm",
                ],
            )
            normalized_frontmatter = _normalize_frontmatter(profiles_frontmatter)

            expected = json.loads(GOLDEN_PROFILES_RUN_ENVELOPE_SNAPSHOT.read_text())
            self.assertEqual(normalized_frontmatter, expected)


def _normalize_frontmatter(frontmatter: dict[str, object]) -> dict[str, object]:
    normalized = json.loads(json.dumps(frontmatter))
    normalized["run_id"] = "<run_id>"
    if "query_id" in normalized:
        normalized["query_id"] = "<query_id>"
    normalized["started_at"] = "<started_at>"
    normalized["completed_at"] = "<completed_at>"
    source_ids = normalized.get("source_ids")
    if isinstance(source_ids, list):
        normalized["source_ids"] = ["<source_id>" for _ in source_ids]
    target_page_refs = normalized.get("target_page_refs")
    if isinstance(target_page_refs, list):
        normalized["target_page_refs"] = ["<target_page_ref>" for _ in target_page_refs]
    persona_ids = normalized.get("persona_ids")
    if isinstance(persona_ids, list):
        normalized["persona_ids"] = ["<persona_id>" for _ in persona_ids]
    toolchain_versions = normalized.get("toolchain_versions")
    if isinstance(toolchain_versions, dict) and "python" in toolchain_versions:
        toolchain_versions["python"] = "<python_version>"
    return normalized


def _run_and_capture_new_frontmatter(*, space_root: Path, cmd: list[str]) -> dict[str, object]:
    before_runs = run_directories(space_root)
    result = run_command(cmd)
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    after_runs = run_directories(space_root)
    created_runs = [path for path in after_runs if path not in before_runs]
    if len(created_runs) != 1:
        raise AssertionError(
            "Expected exactly one new run directory. "
            f"before={[path.name for path in before_runs]} "
            f"after={[path.name for path in after_runs]}"
        )
    return parse_run_frontmatter(created_runs[0] / "run.md")


def _seeded_persona_ids(*, count: int) -> list[str]:
    rows = load_seeded_persona_catalog(repo_root=REPO_ROOT, require_image_files=False)
    return [str(row["persona_id"]) for row in rows[:count]]


if __name__ == "__main__":
    unittest.main()
