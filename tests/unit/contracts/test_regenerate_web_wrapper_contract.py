from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


class RegenerateWebWrapperContractTests(unittest.TestCase):
    def test_wrapper_dispatches_to_build_entrypoint_with_wrapper_managed_registry_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = self._bootstrap_site_and_space(Path(tmp), "alpha")
            result = self._run(
                [
                    "bash",
                    str(REPO_ROOT / "regenerate_web.sh"),
                    str(site_path),
                    "alpha",
                    "--verbose",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("scripts/build_site.py deterministic build complete", result.stdout)
            self.assertIn("workflow_key=build_site", result.stdout)
            self.assertIn(str(site_path / "spaces.toml"), result.stdout)

    def test_wrapper_argument_conflict_handling_rejects_registry_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = self._bootstrap_site_and_space(Path(tmp), "alpha")
            result = self._run(
                [
                    "bash",
                    str(REPO_ROOT / "regenerate_web.sh"),
                    str(site_path),
                    "--registry-path",
                    str(site_path / "other.toml"),
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("wrapper-managed", result.stderr)
            self.assertIn("Usage:", result.stderr)

    def test_end_to_end_wrapper_invocation_writes_deterministic_build_output_without_semantic_flows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = self._bootstrap_site_and_space(Path(tmp), "alpha")
            cmd = [
                "bash",
                str(REPO_ROOT / "regenerate_web.sh"),
                str(site_path),
                "alpha",
            ]
            first = self._run(cmd)
            self.assertEqual(first.returncode, 0, msg=first.stderr)

            manifest_path = site_path / "outputs" / "build_site" / "manifest.json"
            self.assertTrue(manifest_path.is_file())
            first_manifest_text = manifest_path.read_text()
            first_manifest = json.loads(first_manifest_text)
            self.assertEqual(first_manifest["workflow_key"], "build_site")
            self.assertEqual(first_manifest["semantic_flows_executed"], [])
            self.assertEqual(first_manifest["space_targets"], ["alpha"])

            second = self._run(cmd)
            self.assertEqual(second.returncode, 0, msg=second.stderr)
            second_manifest_text = manifest_path.read_text()
            self.assertEqual(first_manifest_text, second_manifest_text)

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
