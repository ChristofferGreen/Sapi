from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


class BootstrapRegistryExceptionIntegrationTests(unittest.TestCase):
    def test_bootstrap_wrappers_allow_missing_operator_registry_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = Path(tmp) / "site-a"
            create_site = self._run(
                ["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "My Site"]
            )
            self.assertEqual(create_site.returncode, 0, msg=create_site.stderr)

            create_space = self._run(
                ["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), "alpha"]
            )
            self.assertEqual(create_space.returncode, 0, msg=create_space.stderr)

    def test_non_bootstrap_scripts_require_explicit_registry_path(self) -> None:
        scripts = [
            ["scripts/ingest_source.py", "alpha", "source.txt"],
            ["scripts/query.py", "alpha", "question"],
            ["scripts/create_comments.py", "alpha", "--count", "5"],
            ["scripts/generate_profiles.py", "alpha"],
            ["scripts/generate_overview.py", "alpha"],
            ["scripts/build_site.py"],
            ["scripts/lint.py", "alpha"],
        ]
        for script_cmd in scripts:
            with self.subTest(script=script_cmd[0]):
                result = self._run(["python3", str(REPO_ROOT / script_cmd[0]), *script_cmd[1:]])
                self.assertEqual(result.returncode, 2, msg=result.stderr)
                self.assertIn("--registry-path", result.stderr)

    def test_non_bootstrap_wrappers_effectively_route_registry_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = tmp_root / "site-a"
            self._run(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "My Site"], check=True)
            self._run(["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), "alpha"], check=True)
            source_path = tmp_root / "source.txt"
            source_path.write_text("source payload\n")
            topic_path = site_path / "spaces" / "alpha" / "topics" / "topic-alpha.json"
            topic_path.write_text(
                '{"topic_id":"topic-alpha","title":"Topic Alpha","structure_type":"wiki","sections":[],"claim_ids":[],"source_ids":[]}\n'
            )

            wrapper_commands = [
                ["bash", str(REPO_ROOT / "ingest.sh"), str(site_path), "alpha", str(source_path), "--mock-llm"],
                ["bash", str(REPO_ROOT / "query.sh"), str(site_path), "alpha", "what is this", "--mock-llm"],
                ["bash", str(REPO_ROOT / "create_comments.sh"), str(site_path), "alpha", "--count", "5", "--mock-llm"],
                ["bash", str(REPO_ROOT / "generate_profiles.sh"), str(site_path), "alpha", "--mock-llm"],
                ["bash", str(REPO_ROOT / "generate_overview.sh"), str(site_path), "alpha", "--mock-llm"],
                ["bash", str(REPO_ROOT / "validate.sh"), str(site_path), "alpha"],
                ["bash", str(REPO_ROOT / "regenerate_web.sh"), str(site_path), "alpha"],
            ]
            for command in wrapper_commands:
                with self.subTest(wrapper=Path(command[1]).name):
                    result = self._run(command)
                    wrapper_name = Path(command[1]).name
                    if wrapper_name in {"validate.sh"}:
                        self.assertNotEqual(result.returncode, 2, msg=result.stderr)
                        self.assertNotIn("--registry-path", result.stderr)
                        continue
                    self.assertEqual(result.returncode, 0, msg=result.stderr)

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
