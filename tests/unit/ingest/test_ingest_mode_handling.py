from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


class IngestModeHandlingTests(unittest.TestCase):
    def test_removed_source_only_flags_are_rejected_by_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = _bootstrap_site_and_space(tmp_root, "alpha")
            source_path = tmp_root / "source.txt"
            source_path.write_text("removed flag mode\n")

            for removed_flag in ("--source-only", "--query-only"):
                with self.subTest(flag=removed_flag):
                    result = _run(
                        [
                            "python3",
                            str(REPO_ROOT / "scripts" / "ingest_source.py"),
                            "alpha",
                            str(source_path),
                            "--registry-path",
                            str(site_path / "spaces.toml"),
                            removed_flag,
                            "--mock-llm",
                        ]
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("unrecognized arguments", result.stderr)

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
            self.assertEqual(len(topic_files), 0)
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

    def test_missing_publication_date_persists_warning_and_unknown_inference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = _bootstrap_site_and_space(tmp_root, "alpha")
            source_path = tmp_root / "source.txt"
            source_path.write_text("missing publication date\n")

            result = _run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            space_root = site_path / "spaces" / "alpha"
            source_records = sorted((space_root / "sources" / "records").glob("source-*.json"))
            self.assertEqual(len(source_records), 1)
            source_record = json.loads(source_records[0].read_text())
            self.assertIsNone(source_record["date"])
            self.assertEqual(
                source_record["source_date_inference"],
                {
                    "date": None,
                    "origin": "unknown",
                    "confidence": "unknown",
                    "rationale": None,
                },
            )
            self.assertEqual(source_record["warnings"][0]["code"], "missing_publication_date")

    def test_require_source_date_fails_when_date_cannot_be_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = _bootstrap_site_and_space(tmp_root, "alpha")
            source_path = tmp_root / "source.txt"
            source_path.write_text("strict date failure\n")

            result = _run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--require-source-date",
                    "--mock-llm",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("strict-date mode (`--require-source-date`) is enabled", result.stderr)

            space_root = site_path / "spaces" / "alpha"
            source_records = sorted((space_root / "sources" / "records").glob("source-*.json"))
            self.assertEqual(source_records, [])
            run_paths = sorted((space_root / "runs").glob("*/run.md"))
            self.assertEqual(run_paths, [])

    def test_comment_inputs_require_explicit_opt_in_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = _bootstrap_site_and_space(tmp_root, "alpha")
            source_path = tmp_root / "source.txt"
            source_path.write_text("comment opt-in boundary\n")

            result = _run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--comment-count",
                    "10",
                    "--comment-page",
                    "topic:topic-a",
                    "--mock-llm",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("require explicit opt-in", result.stderr)

            space_root = site_path / "spaces" / "alpha"
            source_records = sorted((space_root / "sources" / "records").glob("source-*.json"))
            self.assertEqual(source_records, [])

    def test_inline_comment_enrichment_requires_explicit_follow_up_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = _bootstrap_site_and_space(tmp_root, "alpha")
            source_path = tmp_root / "source.txt"
            source_path.write_text("inline enrichment boundary\n")

            result = _run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--enable-comment-enrichment",
                    "--comment-count",
                    "10",
                    "--comment-page",
                    "topic:topic-a",
                    "--mock-llm",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("run create_comments.sh as an explicit follow-up step", result.stderr)

            space_root = site_path / "spaces" / "alpha"
            source_records = sorted((space_root / "sources" / "records").glob("source-*.json"))
            self.assertEqual(source_records, [])

    def test_inline_comment_enrichment_enforces_comment_pipeline_contract_bounds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = _bootstrap_site_and_space(tmp_root, "alpha")
            source_path = tmp_root / "source.txt"
            source_path.write_text("inline enrichment contract bounds\n")

            result = _run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--enable-comment-enrichment",
                    "--comment-count",
                    "4",
                    "--comment-page",
                    "topic:topic-a",
                    "--mock-llm",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requested_comment_count must be in [5, 50]", result.stderr)

    def test_verbose_mode_prints_prompt_stream_trace_dir_and_writes_trace_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = _bootstrap_site_and_space(tmp_root, "alpha")
            source_path = tmp_root / "source.txt"
            source_path.write_text("verbose trace contract\n")

            result = _run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Verbose Trace Source",
                    "--verbose",
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("LLM trace dir", result.stdout)
            self.assertIn("Final LLM prompt", result.stdout)
            self.assertIn("LLM stream output", result.stdout)
            self.assertLess(
                result.stdout.index("LLM trace dir"),
                result.stdout.index("scripts/ingest_source.py source ingested"),
            )

            trace_root = site_path / "outputs" / "llm_traces"
            self.assertTrue(trace_root.is_dir())
            trace_dirs = sorted(path for path in trace_root.glob("*") if path.is_dir())
            self.assertGreaterEqual(len(trace_dirs), 2)
            self.assertFalse((site_path / "spaces" / "alpha" / "outputs" / "llm_traces").exists())
            for trace_dir in trace_dirs:
                self.assertRegex(
                    trace_dir.name,
                    r"^\d{8}T\d{6}Z-[a-z0-9_-]+-\d+-\d+(?:-\d+)?$",
                )
                self.assertTrue(any(trace_dir.glob("*.prompt.txt")))
                self.assertTrue(any(trace_dir.glob("*.context.json")))
                self.assertTrue(any(trace_dir.glob("*.response.*")))
                self.assertTrue(any(trace_dir.glob("*.meta.json")))


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
