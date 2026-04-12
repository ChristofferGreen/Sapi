from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


class QueryModePreflightTests(unittest.TestCase):
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
