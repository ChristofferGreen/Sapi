from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


class WrapperRuntimeFlagIntegrationTests(unittest.TestCase):
    def test_wrappers_forward_runtime_flags_with_consistent_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = self._bootstrap_site_and_space(Path(tmp), "alpha")
            source_path = Path(tmp) / "source.txt"
            source_path.write_text("runtime flag forwarding source\n")

            runtime_args = [
                "--mock-llm",
                "--llm-backend",
                "backend-test",
                "--llm-model",
                "model-test",
                "--llm-reasoning-effort",
                "low",
                "--llm-timeout-secs",
                "31",
                "--warning-budget",
                "77",
                "--run-search-visibility",
                "on",
                "--site-presentation-mode",
                "debug",
                "--enable-source-index",
            ]

            ingest_result = self._run(
                [
                    "bash",
                    str(REPO_ROOT / "ingest.sh"),
                    str(site_path),
                    "alpha",
                    str(source_path),
                    *runtime_args,
                ]
            )
            self.assertEqual(ingest_result.returncode, 0, msg=ingest_result.stderr)
            self.assertIn("runtime_flags={'llm_backend': 'backend-test'", ingest_result.stdout)
            self.assertIn("'llm_model': 'model-test'", ingest_result.stdout)
            self.assertIn("'llm_reasoning_effort': 'low'", ingest_result.stdout)
            self.assertIn("'llm_timeout_secs': 31", ingest_result.stdout)
            self.assertIn("'warning_budget': 77", ingest_result.stdout)
            self.assertIn("'run_search_visibility': 'on'", ingest_result.stdout)
            self.assertIn("'site_presentation_mode': 'debug'", ingest_result.stdout)

            query_result = self._run(
                [
                    "bash",
                    str(REPO_ROOT / "query.sh"),
                    str(site_path),
                    "alpha",
                    "what happened",
                    *runtime_args,
                ]
            )
            self.assertEqual(query_result.returncode, 0, msg=query_result.stderr)
            self.assertIn("runtime_flags={'llm_backend': 'backend-test'", query_result.stdout)
            self.assertIn("'llm_model': 'model-test'", query_result.stdout)
            self.assertIn("'llm_reasoning_effort': 'low'", query_result.stdout)

            comments_result = self._run(
                [
                    "bash",
                    str(REPO_ROOT / "create_comments.sh"),
                    str(site_path),
                    "alpha",
                    "--count",
                    "5",
                    *runtime_args,
                ]
            )
            self.assertEqual(comments_result.returncode, 0, msg=comments_result.stderr)
            self.assertIn("runtime_flags={'llm_backend': 'backend-test'", comments_result.stdout)
            self.assertIn("'warning_budget': 77", comments_result.stdout)

            profiles_result = self._run(
                [
                    "bash",
                    str(REPO_ROOT / "generate_profiles.sh"),
                    str(site_path),
                    "alpha",
                    *runtime_args,
                ]
            )
            self.assertEqual(profiles_result.returncode, 0, msg=profiles_result.stderr)
            self.assertIn("runtime_flags={'llm_backend': 'backend-test'", profiles_result.stdout)

    def test_wrapper_invalid_trace_dir_combination_fails_fast(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = self._bootstrap_site_and_space(Path(tmp), "alpha")
            source_path = Path(tmp) / "source.txt"
            source_path.write_text("runtime flag invalid combo\n")

            commands = [
                [
                    "bash",
                    str(REPO_ROOT / "ingest.sh"),
                    str(site_path),
                    "alpha",
                    str(source_path),
                    "--llm-trace-dir",
                    str(Path(tmp) / "trace"),
                ],
                [
                    "bash",
                    str(REPO_ROOT / "query.sh"),
                    str(site_path),
                    "alpha",
                    "what happened",
                    "--llm-trace-dir",
                    str(Path(tmp) / "trace"),
                ],
                [
                    "bash",
                    str(REPO_ROOT / "create_comments.sh"),
                    str(site_path),
                    "alpha",
                    "--count",
                    "5",
                    "--llm-trace-dir",
                    str(Path(tmp) / "trace"),
                ],
                [
                    "bash",
                    str(REPO_ROOT / "generate_profiles.sh"),
                    str(site_path),
                    "alpha",
                    "--llm-trace-dir",
                    str(Path(tmp) / "trace"),
                ],
            ]
            for command in commands:
                with self.subTest(wrapper=Path(command[1]).name):
                    result = self._run(command)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("--llm-trace-dir requires trace emission", result.stderr)

    def _bootstrap_site_and_space(self, tmp_root: Path, space_name: str) -> Path:
        site_path = tmp_root / "site-a"
        self._run(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "My Site"], check=True)
        self._run(["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), space_name], check=True)
        return site_path

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
