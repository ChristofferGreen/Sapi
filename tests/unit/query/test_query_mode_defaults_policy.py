from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


class QueryModeDefaultsPolicyTests(unittest.TestCase):
    def test_mode_defaults_apply_include_disputed_by_mode(self) -> None:
        expected = {
            "strict": False,
            "exploratory": True,
            "comparative": True,
        }
        with tempfile.TemporaryDirectory() as tmp:
            site_path = _bootstrap_site_and_space(Path(tmp), "alpha")
            space_root = site_path / "spaces" / "alpha"
            _seed_claim(space_root, "claim-alpha--aaaaaaaaaaaa")

            for mode, include_disputed_expected in expected.items():
                with self.subTest(mode=mode):
                    payload = _run_query_and_load_payload(
                        site_path=site_path,
                        mode=mode,
                    )
                    self.assertEqual(
                        payload["execution"]["include_disputed"],
                        include_disputed_expected,
                    )

    def test_include_warnings_default_true_and_override_reflected_in_output_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = _bootstrap_site_and_space(Path(tmp), "alpha")

            default_payload = _run_query_and_load_payload(
                site_path=site_path,
                mode="strict",
            )
            self.assertTrue(default_payload["execution"]["include_warnings"])
            self.assertGreaterEqual(len(default_payload["warnings"]), 1)

            override_payload = _run_query_and_load_payload(
                site_path=site_path,
                mode="strict",
                extra_args=["--no-include-warnings"],
            )
            self.assertFalse(override_payload["execution"]["include_warnings"])
            self.assertEqual(override_payload["warnings"], [])

    def test_retrieval_budget_defaults_and_overrides_are_auditable_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = _bootstrap_site_and_space(Path(tmp), "alpha")
            space_root = site_path / "spaces" / "alpha"

            for suffix in ("a", "b", "c", "d", "e"):
                _seed_claim(space_root, f"claim-{suffix}--aaaaaaaaaaaa")
            for suffix in ("a", "b", "c", "d"):
                _seed_source(space_root, f"source-{suffix}--bbbbbbbbbbbb")

            defaults_payload = _run_query_and_load_payload(
                site_path=site_path,
                mode="strict",
            )
            self.assertEqual(
                defaults_payload["execution"]["retrieval_budget"],
                {"max_claims": 120, "max_sources": 40},
            )
            self.assertEqual(
                defaults_payload["retrieval_counts"],
                {"claims_retrieved": 5, "sources_retrieved": 4},
            )
            self.assertEqual(defaults_payload["omitted_due_to_budget"], {"claims": 0, "sources": 0})

            override_payload = _run_query_and_load_payload(
                site_path=site_path,
                mode="strict",
                extra_args=["--max-claims", "2", "--max-sources", "1"],
            )
            self.assertEqual(
                override_payload["execution"]["retrieval_budget"],
                {"max_claims": 2, "max_sources": 1},
            )
            self.assertEqual(
                override_payload["retrieval_counts"],
                {"claims_retrieved": 2, "sources_retrieved": 1},
            )
            self.assertEqual(override_payload["omitted_due_to_budget"], {"claims": 3, "sources": 3})
            self.assertEqual(
                override_payload["claims_used"],
                ["claim-a--aaaaaaaaaaaa", "claim-b--aaaaaaaaaaaa"],
            )
            self.assertEqual(
                override_payload["sources_used"],
                ["source-a--bbbbbbbbbbbb"],
            )

    def test_invalid_mode_flag_combination_fails_fast_before_retrieval_generation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = _bootstrap_site_and_space(Path(tmp), "alpha")
            space_root = site_path / "spaces" / "alpha"
            before_dirs = {path.name for path in (space_root / "outputs" / "query").glob("query-*")}
            before_runs = {path.name for path in (space_root / "runs").glob("run-*")}

            result = _run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "query.py"),
                    "alpha",
                    "fail fast",
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

            after_dirs = {path.name for path in (space_root / "outputs" / "query").glob("query-*")}
            after_runs = {path.name for path in (space_root / "runs").glob("run-*")}
            self.assertEqual(after_dirs, before_dirs)
            self.assertEqual(after_runs, before_runs)


def _bootstrap_site_and_space(tmp_root: Path, space_name: str) -> Path:
    site_path = tmp_root / "site-a"
    _run(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "My Site"], check=True)
    _run(["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), space_name], check=True)
    return site_path


def _seed_claim(space_root: Path, claim_id: str) -> None:
    path = space_root / "claims" / f"{claim_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"claim_id": claim_id}, indent=2, sort_keys=True) + "\n")


def _seed_source(space_root: Path, source_id: str) -> None:
    path = space_root / "sources" / "records" / f"{source_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"source_id": source_id}, indent=2, sort_keys=True) + "\n")


def _run_query_and_load_payload(
    *,
    site_path: Path,
    mode: str,
    extra_args: list[str] | None = None,
) -> dict[str, object]:
    space_root = site_path / "spaces" / "alpha"
    before = {path.name for path in (space_root / "outputs" / "query").glob("query-*")}
    cmd = [
        "python3",
        str(REPO_ROOT / "scripts" / "query.py"),
        "alpha",
        "what changed?",
        "--registry-path",
        str(site_path / "spaces.toml"),
        "--mode",
        mode,
        "--mock-llm",
    ]
    if extra_args:
        cmd.extend(extra_args)
    result = _run(cmd)
    if result.returncode != 0:
        raise AssertionError(
            f"Query command failed unexpectedly (exit={result.returncode}):\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    after = {path.name for path in (space_root / "outputs" / "query").glob("query-*")}
    new = sorted(after - before)
    if len(new) != 1:
        raise AssertionError(f"Expected exactly one new query output directory, got: {new}")
    query_json = space_root / "outputs" / "query" / new[0] / "query.json"
    return json.loads(query_json.read_text())


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

