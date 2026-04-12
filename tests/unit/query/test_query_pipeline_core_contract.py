from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


class QueryPipelineCoreContractTests(unittest.TestCase):
    def test_mode_preflight_rejects_explicit_strict_include_disputed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = _bootstrap_site_and_space(Path(tmp), "alpha")
            result = _run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "query.py"),
                    "alpha",
                    "What changed?",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--mode",
                    "strict",
                    "--include-disputed",
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("--mode strict --include-disputed", result.stderr)

            space_root = site_path / "spaces" / "alpha"
            self.assertEqual(list((space_root / "outputs" / "query").glob("query-*")), [])
            self.assertEqual(list((space_root / "runs").glob("*/run.md")), [])

    def test_query_writes_only_query_outputs_plus_run_lint_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = _bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"

            _seed_canonical_record(
                space_root / "sources" / "records" / "source-sentinel--aaaaaaaaaaaa.json",
                {"source_id": "source-sentinel--aaaaaaaaaaaa"},
            )
            _seed_canonical_record(
                space_root / "claims" / "claim-sentinel--bbbbbbbbbbbb.json",
                {"claim_id": "claim-sentinel--bbbbbbbbbbbb"},
            )
            _seed_canonical_record(
                space_root / "relations" / "supports:claim-a->claim-b.json",
                {"relation_id": "supports:claim-a->claim-b"},
            )
            _seed_canonical_record(
                space_root / "topics" / "topic-sentinel--cccccccccccc.json",
                {"topic_id": "topic-sentinel--cccccccccccc"},
            )
            _seed_canonical_record(
                space_root / "profiles" / "persona-sentinel.json",
                {"persona_id": "persona-sentinel"},
            )

            canonical_before = {
                _relative_to_space(space_root, path): path.read_text()
                for path in _canonical_artifact_paths(space_root)
            }
            all_before = {path.relative_to(space_root) for path in space_root.rglob("*") if path.is_file()}

            result = _run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "query.py"),
                    "alpha",
                    "What changed?",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("scripts/query.py query complete", result.stdout)

            query_dirs = sorted((space_root / "outputs" / "query").glob("query-*"))
            self.assertEqual(len(query_dirs), 1)
            query_record_path = query_dirs[0] / "query.json"
            self.assertTrue(query_record_path.is_file())
            payload = json.loads(query_record_path.read_text())
            self.assertEqual(payload["mode"], "strict")
            self.assertEqual(payload["manifest_path"], None)
            required_keys = {
                "query_id",
                "answer",
                "claims_used",
                "sources_used",
                "retrieval_counts",
                "contradictions_considered",
                "falsification_signals",
                "omitted_due_to_budget",
                "mode",
                "scope",
                "run_id",
                "query_timestamp_utc",
                "citation_coverage",
                "lint_summary",
                "execution",
                "warnings",
                "manifest_path",
            }
            self.assertTrue(required_keys.issubset(set(payload.keys())))
            self.assertTrue(
                {
                    "claims_retrieved",
                    "sources_retrieved",
                }.issubset(set(payload["retrieval_counts"].keys()))
            )
            self.assertTrue(
                {
                    "error_count",
                    "warning_count",
                    "info_count",
                }.issubset(set(payload["lint_summary"].keys()))
            )
            self.assertTrue(
                {
                    "execution_mode",
                    "llm_attempt_count",
                    "reasoning_effort",
                    "model_fingerprint",
                    "provider_fingerprint",
                }.issubset(set(payload["execution"].keys()))
            )
            self.assertIsInstance(payload["warnings"], list)

            run_paths = sorted((space_root / "runs").glob("*/run.md"))
            self.assertEqual(len(run_paths), 1)
            lint_paths = sorted((space_root / "runs").glob("*/lint.json"))
            self.assertEqual(len(lint_paths), 1)
            self.assertFalse((site_path / "outputs" / "build_site" / "manifest.json").exists())

            canonical_after = {
                _relative_to_space(space_root, path): path.read_text()
                for path in _canonical_artifact_paths(space_root)
            }
            self.assertEqual(canonical_after, canonical_before)

            all_after = {path.relative_to(space_root) for path in space_root.rglob("*") if path.is_file()}
            new_paths = all_after - all_before
            for path in new_paths:
                path_text = str(path)
                allowed = path_text.startswith("outputs/query/query-") or path_text.startswith("runs/run-")
                self.assertTrue(allowed, f"Unexpected query write path: {path_text}")

    def test_terminal_failure_rolls_back_query_outputs_and_run_lint_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = _bootstrap_site_and_space(Path(tmp), "alpha")
            space_root = site_path / "spaces" / "alpha"

            result = _run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "query.py"),
                    "alpha",
                    "What changed?",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--simulate-terminal-failure",
                    "--mock-llm",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Simulated terminal query failure", result.stderr)

            self.assertEqual(list((space_root / "outputs" / "query").glob("query-*")), [])
            self.assertEqual(list((space_root / "runs").glob("*/run.md")), [])
            self.assertEqual(list((space_root / "runs").glob("*/lint.json")), [])


def _bootstrap_site_and_space(tmp_root: Path, space_name: str) -> Path:
    site_path = tmp_root / "site-a"
    _run(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "My Site"], check=True)
    _run(["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), space_name], check=True)
    return site_path


def _seed_canonical_record(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _canonical_artifact_paths(space_root: Path) -> list[Path]:
    results: list[Path] = []
    for relative_dir in ("sources/records", "claims", "relations", "topics", "profiles"):
        root = space_root / relative_dir
        if root.is_dir():
            results.extend(path for path in root.rglob("*.json") if path.is_file())
    return sorted(results)


def _relative_to_space(space_root: Path, path: Path) -> str:
    return str(path.relative_to(space_root))


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


if __name__ == "__main__":
    unittest.main()
