from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

from sapi.core.registry import resolve_space_root


REPO_ROOT = Path(__file__).resolve().parents[3]


class BootstrapSiteSpaceTests(unittest.TestCase):
    def test_create_site_creates_site_json_spaces_registry_and_runtime_skeleton(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = Path(tmp) / "site-a"
            self._run(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "My Site"])

            site_json_path = site_path / "site.json"
            self.assertTrue(site_json_path.is_file())
            site_json = json.loads(site_json_path.read_text())
            self.assertEqual(site_json["schema_version"], "site_scope_v1")
            self.assertEqual(site_json["site_name"], "My Site")
            self.assertEqual(site_json["site_root"], ".")

            self.assertTrue((site_path / "spaces.toml").is_file())
            discussion_controls_path = site_path / "config" / "discussion_controls.json"
            self.assertTrue(discussion_controls_path.is_file())
            discussion_controls = json.loads(discussion_controls_path.read_text())
            self.assertEqual(
                discussion_controls["schema_version"],
                "comment_section_discussion_controls_v1",
            )
            self.assertEqual(discussion_controls["defaults"], {})
            self.assertEqual(discussion_controls["pages"], {})
            self.assertTrue((site_path / "spaces").is_dir())
            self.assertTrue((site_path / "outputs" / "llm_traces").is_dir())

    def test_create_site_handles_json_escaped_site_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = Path(tmp) / "site-a"
            site_name = 'My "Quoted" Site'
            self._run(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), site_name])
            site_json = json.loads((site_path / "site.json").read_text())
            self.assertEqual(site_json["site_name"], site_name)

    def test_create_space_registers_space_and_creates_canonical_space_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = Path(tmp) / "site-a"
            space_name = "alpha"
            self._run(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "My Site"])
            self._run(["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), space_name])
            self._run(["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), space_name])

            registry = tomllib.loads((site_path / "spaces.toml").read_text())
            spaces = registry.get("spaces", [])
            self.assertEqual(len(spaces), 1)
            self.assertEqual(spaces[0]["space_name"], space_name)
            self.assertEqual(spaces[0]["space_root"], f"spaces/{space_name}")

            space_root = site_path / "spaces" / space_name
            expected_dirs = [
                "sources/records",
                "sources/artifacts",
                "claims",
                "relations",
                "topics",
                "profiles",
                "projections/markdown",
                "runs",
                "outputs/query",
                "outputs/persona_profile_history",
                "outputs/comment_quality",
                "site",
                "raw/snapshots/comment_sections",
                ".locks",
                ".cache",
            ]
            for rel in expected_dirs:
                with self.subTest(path=rel):
                    self.assertTrue((space_root / rel).is_dir())
            self.assertTrue((space_root / "imports.lock.md").is_file())

    def test_layout_keeps_site_and_space_owned_artifacts_under_correct_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = Path(tmp) / "site-a"
            space_name = "alpha"
            self._run(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "My Site"])
            self._run(["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), space_name])

            space_root = site_path / "spaces" / space_name

            # Site-scoped derived artifacts live under <site_path>/outputs.
            self.assertTrue((site_path / "outputs" / "llm_traces").is_dir())
            self.assertFalse((site_path / "outputs" / "query").exists())

            # Space-scoped derived artifacts live under <space_root>/outputs.
            self.assertTrue((space_root / "outputs" / "query").is_dir())
            self.assertTrue((space_root / "outputs" / "persona_profile_history").is_dir())
            self.assertTrue((space_root / "outputs" / "comment_quality").is_dir())
            self.assertFalse((space_root / "outputs" / "llm_traces").exists())

            # Space-owned source artifacts must not be written at site root.
            self.assertTrue((space_root / "sources" / "artifacts").is_dir())
            self.assertFalse((site_path / "sources").exists())

            # Repository-owned persona catalog must not be copied into runtime site/space roots.
            self.assertFalse((site_path / "personas").exists())
            self.assertFalse((space_root / "personas").exists())

    def test_registry_and_site_scope_persist_relative_paths_for_relocatability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            site_path = tmp_path / "site-a"
            moved_site_path = tmp_path / "site-b"
            space_name = "alpha"

            self._run(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "My Site"])
            self._run(["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), space_name])

            site_scope = json.loads((site_path / "site.json").read_text())
            self.assertEqual(site_scope["site_root"], ".")
            self.assertFalse(Path(site_scope["site_root"]).is_absolute())

            registry = tomllib.loads((site_path / "spaces.toml").read_text())
            space_row = registry["spaces"][0]
            self.assertEqual(space_row["space_root"], f"spaces/{space_name}")
            self.assertFalse(Path(space_row["space_root"]).is_absolute())

            shutil.move(str(site_path), str(moved_site_path))
            resolved = resolve_space_root(moved_site_path / "spaces.toml", space_name)
            self.assertEqual(resolved, (moved_site_path / "spaces" / space_name).resolve())
            self.assertTrue(resolved.is_dir())

    def test_create_space_bootstraps_registry_when_create_site_not_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = Path(tmp) / "site-a"
            space_name = "alpha"
            self._run(["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), space_name])

            registry = tomllib.loads((site_path / "spaces.toml").read_text())
            spaces = registry.get("spaces", [])
            self.assertEqual(len(spaces), 1)
            self.assertEqual(spaces[0]["space_name"], space_name)
            self.assertEqual(spaces[0]["space_root"], f"spaces/{space_name}")
            self.assertTrue((site_path / "spaces" / space_name).is_dir())

    def test_create_space_rejects_non_slug_space_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = Path(tmp) / "site-a"
            result = subprocess.run(
                ["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), "Alpha Space"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("lowercase kebab-case", result.stderr)
            self.assertFalse((site_path / "spaces.toml").exists())

    def test_bootstrap_registry_exception_applies_only_to_bootstrap_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = Path(tmp) / "site-a"
            space_name = "alpha"

            # Bootstrap wrappers succeed with no --registry-path argument.
            self._run(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "My Site"])
            self._run(["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), space_name])

            # Non-bootstrap script must fail without --registry-path.
            result = subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts" / "query.py"), space_name, "hello"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--registry-path", result.stderr)

    def _run(self, cmd: list[str]) -> None:
        result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        if result.returncode != 0:
            self.fail(
                f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )


if __name__ == "__main__":
    unittest.main()
