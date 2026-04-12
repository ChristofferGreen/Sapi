from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


class WrapperMockModePolicyTests(unittest.TestCase):
    def test_wrapper_default_does_not_silently_enable_mock_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = self._bootstrap_site_and_space(Path(tmp), "alpha")
            for wrapper_name, command in self._semantic_wrapper_commands(site_path):
                with self.subTest(wrapper=wrapper_name):
                    result = self._run(command)
                    self.assertEqual(result.returncode, 0, msg=result.stderr)
                    self.assertIn("execution_mode=live_llm", result.stdout)

    def test_wrapper_explicit_mock_mode_is_forwarded_and_auditable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = self._bootstrap_site_and_space(Path(tmp), "alpha")
            for wrapper_name, command in self._semantic_wrapper_commands(site_path):
                with self.subTest(wrapper=wrapper_name):
                    result = self._run([*command, "--mock-llm"])
                    self.assertEqual(result.returncode, 0, msg=result.stderr)
                    self.assertIn("execution_mode=mock_llm_test", result.stdout)

    def test_env_var_flow_control_is_rejected_even_when_wrapper_invoked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = self._bootstrap_site_and_space(Path(tmp), "alpha")
            for prohibited_key in ("SAPI_MOCK_LLM", "SAPI_ENABLE_DETERMINISTIC_SEMANTICS"):
                for wrapper_name, command in self._semantic_wrapper_commands(site_path):
                    with self.subTest(wrapper=wrapper_name, env_key=prohibited_key):
                        env = os.environ.copy()
                        env[prohibited_key] = "1"
                        result = self._run(command, env=env)
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn(prohibited_key, result.stderr)

    def _bootstrap_site_and_space(self, tmp_root: Path, space_name: str) -> Path:
        site_path = tmp_root / "site-a"
        self._run(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "My Site"], check=True)
        self._run(["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), space_name], check=True)
        return site_path

    def _semantic_wrapper_commands(self, site_path: Path) -> list[tuple[str, list[str]]]:
        return [
            (
                "ingest.sh",
                [
                    "bash",
                    str(REPO_ROOT / "ingest.sh"),
                    str(site_path),
                    "alpha",
                    "https://example.com/source",
                ],
            ),
            (
                "query.sh",
                [
                    "bash",
                    str(REPO_ROOT / "query.sh"),
                    str(site_path),
                    "alpha",
                    "what is this",
                ],
            ),
            (
                "create_comments.sh",
                [
                    "bash",
                    str(REPO_ROOT / "create_comments.sh"),
                    str(site_path),
                    "alpha",
                    "--count",
                    "5",
                ],
            ),
            (
                "generate_profiles.sh",
                [
                    "bash",
                    str(REPO_ROOT / "generate_profiles.sh"),
                    str(site_path),
                    "alpha",
                ],
            ),
        ]

    def _run(
        self,
        cmd: list[str],
        *,
        check: bool = False,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            env=env,
        )
        if check and result.returncode != 0:
            raise AssertionError(
                f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )
        return result


if __name__ == "__main__":
    unittest.main()
