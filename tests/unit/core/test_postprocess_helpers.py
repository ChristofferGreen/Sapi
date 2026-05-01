from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sapi.core.postprocess import run_space_build_postprocess


class PostprocessHelperTests(unittest.TestCase):
    def test_run_space_build_postprocess_returns_manifest_path_on_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            site_path = Path(tmp) / "site"
            manifest_path = site_path / "outputs" / "build_site" / "manifest.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text("{}\n")

            with patch("subprocess.run") as run_mock:
                run_mock.return_value = subprocess.CompletedProcess(
                    args=["python3", "scripts/build_site.py"],
                    returncode=0,
                    stdout="ok",
                    stderr="",
                )
                resolved = run_space_build_postprocess(
                    repo_root=repo_root,
                    registry_path=site_path / "spaces.toml",
                    site_path=site_path,
                    space_name="alpha",
                )

            self.assertEqual(resolved, manifest_path)
            self.assertNotIn("--skip-site-new-index", run_mock.call_args.args[0])

    def test_run_space_build_postprocess_can_skip_site_new_refresh(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            site_path = Path(tmp) / "site"
            manifest_path = site_path / "outputs" / "build_site" / "manifest.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text("{}\n")

            with patch("subprocess.run") as run_mock:
                run_mock.return_value = subprocess.CompletedProcess(
                    args=["python3", "scripts/build_site.py"],
                    returncode=0,
                    stdout="ok",
                    stderr="",
                )
                resolved = run_space_build_postprocess(
                    repo_root=repo_root,
                    registry_path=site_path / "spaces.toml",
                    site_path=site_path,
                    space_name="alpha",
                    refresh_site_new_index=False,
                )

            self.assertEqual(resolved, manifest_path)
            command = run_mock.call_args.args[0]
            self.assertIn("--skip-site-new-index", command)
            self.assertLess(command.index("--skip-site-new-index"), command.index("alpha"))

    def test_run_space_build_postprocess_raises_on_subprocess_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            site_path = Path(tmp) / "site"

            with patch("subprocess.run") as run_mock:
                run_mock.return_value = subprocess.CompletedProcess(
                    args=["python3", "scripts/build_site.py"],
                    returncode=1,
                    stdout="bad-out",
                    stderr="bad-err",
                )
                with self.assertRaisesRegex(RuntimeError, "Deterministic space build failed"):
                    run_space_build_postprocess(
                        repo_root=repo_root,
                        registry_path=site_path / "spaces.toml",
                        site_path=site_path,
                        space_name="alpha",
                    )


if __name__ == "__main__":
    unittest.main()
