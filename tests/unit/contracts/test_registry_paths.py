from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from sapi.core.registry import load_registry, resolve_registry_path, resolve_space_root


REPO_ROOT = Path(__file__).resolve().parents[3]


class RegistryPathContractTests(unittest.TestCase):
    def test_non_bootstrap_scripts_require_explicit_registry_path(self) -> None:
        commands = [
            ["scripts/ingest_source.py", "space-a", "source.txt"],
            ["scripts/query.py", "space-a", "question"],
            ["scripts/create_comments.py", "space-a", "--count", "1"],
            ["scripts/generate_profiles.py", "space-a"],
            ["scripts/build_site.py"],
            ["scripts/lint.py", "space-a"],
            ["scripts/evaluate_source.py", "space-a", "source.txt"],
        ]

        for cmd in commands:
            script = REPO_ROOT / cmd[0]
            result = subprocess.run(
                ["python3", str(script), *cmd[1:]],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2, cmd[0])
            self.assertIn("--registry-path", result.stderr, cmd[0])

    def test_relative_space_root_resolves_against_registry_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            registry_dir = tmp_path / "site"
            registry_dir.mkdir(parents=True)
            registry_path = registry_dir / "spaces.toml"
            registry_path.write_text(
                """
[[spaces]]
space_name = "alpha"
space_root = "spaces/alpha"
""".strip()
            )

            resolved = resolve_space_root(registry_path, "alpha")
            self.assertEqual(resolved, (registry_dir / "spaces/alpha").resolve())

    def test_relative_registry_path_resolves_against_cwd_without_home_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            cwd = tmp_path / "workspace"
            cwd.mkdir(parents=True)
            registry_path = cwd / "spaces.toml"
            registry_path.write_text(
                """
[[spaces]]
space_name = "alpha"
space_root = "spaces/alpha"
""".strip()
            )

            old_cwd = Path.cwd()
            try:
                os.chdir(cwd)
                resolved = resolve_registry_path("spaces.toml")
                self.assertEqual(resolved, registry_path.resolve())
            finally:
                os.chdir(old_cwd)

    def test_no_fallback_or_merge_with_home_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            home = tmp_path / "home"
            home_registry_dir = home / ".sapi"
            home_registry_dir.mkdir(parents=True)
            (home_registry_dir / "spaces.toml").write_text(
                """
[[spaces]]
space_name = "from-home"
space_root = "/tmp/home-space"
""".strip()
            )

            old_home = os.environ.get("HOME")
            os.environ["HOME"] = str(home)
            try:
                with self.assertRaises(ValueError):
                    resolve_registry_path(None)

                missing_registry = tmp_path / "missing-spaces.toml"
                result = subprocess.run(
                    [
                        "python3",
                        str(REPO_ROOT / "scripts/query.py"),
                        "space-a",
                        "question",
                        "--registry-path",
                        str(missing_registry),
                    ],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Registry file not found", result.stderr)
            finally:
                if old_home is None:
                    os.environ.pop("HOME", None)
                else:
                    os.environ["HOME"] = old_home

    def test_explicit_registry_is_authoritative_without_home_registry_merge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            home = tmp_path / "home"
            home_registry_dir = home / ".sapi"
            home_registry_dir.mkdir(parents=True)
            (home_registry_dir / "spaces.toml").write_text(
                """
[[spaces]]
space_name = "home-space"
space_root = "/tmp/home-space"
""".strip()
            )

            explicit_registry = tmp_path / "site" / "spaces.toml"
            explicit_registry.parent.mkdir(parents=True)
            explicit_registry.write_text(
                """
[[spaces]]
space_name = "explicit-space"
space_root = "spaces/explicit"
""".strip()
            )

            old_home = os.environ.get("HOME")
            os.environ["HOME"] = str(home)
            try:
                with self.assertRaises(KeyError):
                    resolve_space_root(explicit_registry, "home-space")
            finally:
                if old_home is None:
                    os.environ.pop("HOME", None)
                else:
                    os.environ["HOME"] = old_home

    def test_duplicate_space_names_fail_fast(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "spaces.toml"
            registry_path.write_text(
                """
[[spaces]]
space_name = "dup"
space_root = "spaces/a"

[[spaces]]
space_name = "dup"
space_root = "spaces/b"
""".strip()
            )

            with self.assertRaises(ValueError):
                load_registry(registry_path)


if __name__ == "__main__":
    unittest.main()
