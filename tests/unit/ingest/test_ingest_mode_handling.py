from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


class IngestModeHandlingTests(unittest.TestCase):
    def test_query_only_alias_normalizes_to_source_only_and_writes_empty_semantic_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = _bootstrap_site_and_space(tmp_root, "alpha")
            source_path = tmp_root / "source.txt"
            source_path.write_text("source-only alias mode\n")

            result = _run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--query-only",
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("deprecated", result.stderr)

            space_root = site_path / "spaces" / "alpha"
            run_paths = sorted((space_root / "runs").glob("*/run.md"))
            self.assertEqual(len(run_paths), 1)
            frontmatter = _parse_frontmatter(run_paths[0].read_text())
            self.assertEqual(frontmatter["semantic_flows"], [])
            self.assertEqual(frontmatter["semantic_flow_invocation_counts"], {})
            self.assertFalse(frontmatter["force_mode"])
            self.assertFalse(frontmatter["rollback_skipped"])
            self.assertEqual(frontmatter["build_deferred"], False)
            self.assertIsNone(frontmatter["deferred_build_reason"])

            topic_files = sorted((space_root / "topics").glob("topic-*.json"))
            self.assertEqual(topic_files, [])

    def test_deferred_build_runs_write_trackable_deferred_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = _bootstrap_site_and_space(tmp_root, "alpha")
            source_path = tmp_root / "source.txt"
            source_path.write_text("deferred build mode\n")

            result = _run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--build-deferred",
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            space_root = site_path / "spaces" / "alpha"
            run_paths = sorted((space_root / "runs").glob("*/run.md"))
            self.assertEqual(len(run_paths), 1)
            frontmatter = _parse_frontmatter(run_paths[0].read_text())
            self.assertEqual(frontmatter["status"], "success_with_warnings")
            self.assertEqual(frontmatter["semantic_flows"], ["ingest_extraction", "topic_generation"])
            self.assertEqual(
                frontmatter["semantic_flow_invocation_counts"],
                {"ingest_extraction": 1, "topic_generation": 1},
            )
            self.assertEqual(frontmatter["build_deferred"], True)
            self.assertEqual(frontmatter["deferred_build_reason"], "operator_requested_build_deferred")

            topic_files = sorted((space_root / "topics").glob("topic-*.json"))
            self.assertEqual(len(topic_files), 1)
            self.assertFalse((site_path / "outputs" / "build_site" / "manifest.json").exists())

    def test_force_mode_failure_preserves_artifacts_and_writes_force_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = _bootstrap_site_and_space(tmp_root, "alpha")
            source_path = tmp_root / "source.txt"
            source_path.write_text("force mode failure\n")

            result = _run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--force",
                    "--simulate-terminal-failure",
                    "--mock-llm",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Simulated terminal ingest failure", result.stderr)

            space_root = site_path / "spaces" / "alpha"
            source_records = sorted((space_root / "sources" / "records").glob("source-*.json"))
            self.assertEqual(len(source_records), 1)

            run_paths = sorted((space_root / "runs").glob("*/run.md"))
            self.assertEqual(len(run_paths), 1)
            frontmatter = _parse_frontmatter(run_paths[0].read_text())
            self.assertEqual(frontmatter["status"], "failed")
            self.assertTrue(frontmatter["force_mode"])
            self.assertTrue(frontmatter["rollback_skipped"])
            self.assertEqual(frontmatter["build_deferred"], False)
            self.assertIsNone(frontmatter["deferred_build_reason"])


def _bootstrap_site_and_space(tmp_root: Path, space_name: str) -> Path:
    site_path = tmp_root / "site-a"
    _run(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "My Site"], check=True)
    _run(["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), space_name], check=True)
    return site_path


def _run(cmd: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


def _parse_frontmatter(markdown: str) -> dict[str, object]:
    lines = markdown.splitlines()
    if not lines or lines[0] != "---":
        raise AssertionError("run.md missing frontmatter start marker")
    result: dict[str, object] = {}
    index = 1
    while index < len(lines) and lines[index] != "---":
        key, raw = lines[index].split(":", 1)
        result[key.strip()] = json.loads(raw.strip())
        index += 1
    if index >= len(lines) or lines[index] != "---":
        raise AssertionError("run.md missing frontmatter end marker")
    return result


if __name__ == "__main__":
    unittest.main()
