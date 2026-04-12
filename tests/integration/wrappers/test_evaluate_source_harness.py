from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


class EvaluateSourceHarnessIntegrationTests(unittest.TestCase):
    def test_default_run_emits_required_artifact_pack_and_manifest_linkage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path, source_path = self._bootstrap_site_space_and_source(Path(tmp), "alpha")
            result = self._run(
                [
                    "bash",
                    str(REPO_ROOT / "evaluate_source.sh"),
                    str(site_path),
                    "alpha",
                    str(source_path),
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            space_root = site_path / "spaces" / "alpha"
            evaluations_root = space_root / "outputs" / "evaluations"
            self.assertTrue(evaluations_root.is_dir())
            evaluation_dirs = sorted(path for path in evaluations_root.iterdir() if path.is_dir())
            self.assertEqual(len(evaluation_dirs), 1)
            evaluation_dir = evaluation_dirs[0]

            required_paths = [
                evaluation_dir / "README.md",
                evaluation_dir / "summary.md",
                evaluation_dir / "ingest_run.md",
                evaluation_dir / "lint_summary.md",
                evaluation_dir / "site_links.md",
                evaluation_dir / "query_answers" / "strict.md",
                evaluation_dir / "manifest.json",
            ]
            for path in required_paths:
                self.assertTrue(path.is_file(), path)
            self.assertFalse((evaluation_dir / "comments_review.md").exists())

            manifest = json.loads((evaluation_dir / "manifest.json").read_text())
            self.assertEqual(manifest["evaluation_id"], evaluation_dir.name)
            self.assertEqual(manifest["workflow_key"], "evaluate_source_quality")
            self.assertEqual(manifest.get("workflow_statuses", {}).get("comments"), "skipped")

            run_ids = manifest.get("run_ids")
            self.assertIsInstance(run_ids, dict)
            ingest_run_id = run_ids.get("ingest")
            query_run_id = run_ids.get("query")
            self.assertIsInstance(ingest_run_id, str)
            self.assertIsInstance(query_run_id, str)
            self.assertTrue((space_root / "runs" / ingest_run_id).is_dir())
            self.assertTrue((space_root / "runs" / query_run_id).is_dir())
            self.assertIsNone(run_ids.get("comments"))

            markdown_artifacts = set(manifest.get("markdown_artifacts", []))
            self.assertSetEqual(
                markdown_artifacts,
                {
                    "README.md",
                    "summary.md",
                    "ingest_run.md",
                    "lint_summary.md",
                    "site_links.md",
                    "query_answers/strict.md",
                },
            )
            for rel in markdown_artifacts:
                self.assertTrue((evaluation_dir / rel).is_file(), rel)

            self.assertIn("# Source Evaluation Artifact Pack", (evaluation_dir / "README.md").read_text())
            self.assertIn("## Execution Summary", (evaluation_dir / "README.md").read_text())
            self.assertIn("# Evaluation Summary", (evaluation_dir / "summary.md").read_text())
            self.assertIn("## Checklist", (evaluation_dir / "summary.md").read_text())
            self.assertIn("# Ingest Run", (evaluation_dir / "ingest_run.md").read_text())
            self.assertIn("ingest_run_id", (evaluation_dir / "ingest_run.md").read_text())
            self.assertIn("# Lint Summary", (evaluation_dir / "lint_summary.md").read_text())
            self.assertIn("# Site Links", (evaluation_dir / "site_links.md").read_text())
            self.assertIn("# Strict Query Answer", (evaluation_dir / "query_answers" / "strict.md").read_text())

    def test_out_override_and_comments_mode_emit_comments_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, source_path = self._bootstrap_site_space_and_source(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            (space_root / "topics" / "topic-example.json").write_text(
                json.dumps(
                    {
                        "topic_id": "topic-example",
                        "title": "Topic Example",
                        "sections": [],
                        "source_ids": [],
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
            out_dir = tmp_root / "custom-evaluation-pack"
            result = self._run(
                [
                    "bash",
                    str(REPO_ROOT / "evaluate_source.sh"),
                    str(site_path),
                    "alpha",
                    str(source_path),
                    "--out",
                    str(out_dir),
                    "--comments",
                    "6",
                    "--comment-user",
                    "persona-1",
                    "--comment-page",
                    "topic:topic-example",
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            required_paths = [
                out_dir / "README.md",
                out_dir / "summary.md",
                out_dir / "ingest_run.md",
                out_dir / "lint_summary.md",
                out_dir / "site_links.md",
                out_dir / "comments_review.md",
                out_dir / "query_answers" / "strict.md",
                out_dir / "manifest.json",
            ]
            for path in required_paths:
                self.assertTrue(path.is_file(), path)

            manifest = json.loads((out_dir / "manifest.json").read_text())
            self.assertEqual(manifest.get("comments_requested"), 6)
            workflow_statuses = manifest.get("workflow_statuses", {})
            self.assertEqual(workflow_statuses.get("comments"), "success")
            self.assertIn("comments_review.md", set(manifest.get("markdown_artifacts", [])))
            self.assertEqual(manifest.get("comments", {}).get("requested_count"), 6)
            self.assertEqual(
                manifest.get("comments", {}).get("effective_page_targets"),
                ["topic:topic-example"],
            )
            self.assertEqual(manifest.get("comments", {}).get("effective_user_targets"), ["persona-1"])
            self.assertEqual(
                manifest.get("comments", {}).get("effective_page_requested_counts"),
                [{"target": "topic:topic-example", "requested_count": 6}],
            )
            self.assertEqual(
                manifest.get("comments", {}).get("effective_user_requested_counts"),
                [{"target": "persona-1", "requested_count": 6}],
            )
            self.assertIn("run_ids", manifest)
            self.assertIsInstance(manifest.get("run_ids"), dict)
            self.assertIsInstance(manifest.get("run_ids", {}).get("ingest"), str)

            default_evaluations_root = site_path / "spaces" / "alpha" / "outputs" / "evaluations"
            self.assertFalse(default_evaluations_root.exists())

            readme_text = (out_dir / "README.md").read_text()
            self.assertIn("create_comments:", readme_text)
            self.assertIn("--count 6", readme_text)
            self.assertIn("--comment-user persona-1", readme_text)
            self.assertIn("--comment-page topic:topic-example", readme_text)

            comments_review = (out_dir / "comments_review.md").read_text()
            self.assertIn("# Comments Review", comments_review)
            self.assertIn("## Per-Page Requested Counts", comments_review)
            self.assertIn("## Per-User Requested Counts", comments_review)
            self.assertIn("## Representative Thread Excerpt", comments_review)
            self.assertIn("| `topic:topic-example` | 6 |", comments_review)
            self.assertIn("| `persona-1` | 6 |", comments_review)

    def test_invalid_comments_arg_fails_fast_without_partial_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path, source_path = self._bootstrap_site_space_and_source(Path(tmp), "alpha")
            result = self._run(
                [
                    "bash",
                    str(REPO_ROOT / "evaluate_source.sh"),
                    str(site_path),
                    "alpha",
                    str(source_path),
                    "--comments",
                    "0",
                    "--mock-llm",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--comments must be a positive integer", result.stderr)

            space_root = site_path / "spaces" / "alpha"
            self.assertFalse((space_root / "outputs" / "evaluations").exists())
            run_dirs = list((space_root / "runs").glob("run-*")) if (space_root / "runs").exists() else []
            self.assertEqual(run_dirs, [])

    def test_runtime_flags_are_forwarded_and_documented_in_readme_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path, source_path = self._bootstrap_site_space_and_source(Path(tmp), "alpha")
            result = self._run(
                [
                    "bash",
                    str(REPO_ROOT / "evaluate_source.sh"),
                    str(site_path),
                    "alpha",
                    str(source_path),
                    "--comments",
                    "5",
                    "--llm-backend",
                    "backend-forwarded",
                    "--llm-model",
                    "model-forwarded",
                    "--llm-reasoning-effort",
                    "low",
                    "--llm-timeout-secs",
                    "42",
                    "--llm-trace",
                    "--warning-budget",
                    "88",
                    "--run-search-visibility",
                    "on",
                    "--site-presentation-mode",
                    "debug",
                    "--enable-source-index",
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            space_root = site_path / "spaces" / "alpha"
            evaluations_root = space_root / "outputs" / "evaluations"
            evaluation_dirs = sorted(path for path in evaluations_root.iterdir() if path.is_dir())
            self.assertEqual(len(evaluation_dirs), 1)
            readme_text = (evaluation_dirs[0] / "README.md").read_text()
            self.assertIn("--llm-backend backend-forwarded", readme_text)
            self.assertIn("--llm-model model-forwarded", readme_text)
            self.assertIn("--llm-reasoning-effort low", readme_text)
            self.assertIn("--llm-timeout-secs 42", readme_text)
            self.assertIn("--llm-trace", readme_text)
            self.assertIn("--warning-budget 88", readme_text)
            self.assertIn("--run-search-visibility on", readme_text)
            self.assertIn("--site-presentation-mode debug", readme_text)
            self.assertIn("--enable-source-index", readme_text)
            self.assertIn("validate_lint:", readme_text)

    def _bootstrap_site_space_and_source(self, tmp_root: Path, space_name: str) -> tuple[Path, Path]:
        site_path = tmp_root / "site-a"
        self._run(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "My Site"], check=True)
        self._run(["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), space_name], check=True)
        source_path = tmp_root / "source.txt"
        source_path.write_text("source text for evaluate_source harness tests\n")
        return site_path, source_path

    def _run(self, cmd: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
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


if __name__ == "__main__":
    unittest.main()
