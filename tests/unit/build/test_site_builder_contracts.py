from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.build_site import _validate_frontend_toolchain_reproducibility


REPO_ROOT = Path(__file__).resolve().parents[3]


class SiteBuilderContractTests(unittest.TestCase):
    def test_build_renders_deterministic_html_from_canonical_json_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_source_record(space_root, source_id="source-a", title="Source A")
            self._write_topic_record(
                space_root,
                topic_id="topic-a",
                title="Topic A",
                source_ids=["source-a"],
            )
            # Non-canonical artifact should not affect deterministic build output.
            (space_root / "raw" / "semantic_dump.json").write_text(json.dumps({"noise": True}))

            command = [
                "python3",
                str(REPO_ROOT / "scripts" / "build_site.py"),
                "--registry-path",
                str(site_path / "spaces.toml"),
                "alpha",
            ]
            first = self._run(command)
            self.assertEqual(first.returncode, 0, msg=first.stderr)
            self.assertIn("deterministic build complete", first.stdout)

            manifest_path = site_path / "outputs" / "build_site" / "manifest.json"
            self.assertTrue(manifest_path.is_file())
            first_manifest_text = manifest_path.read_text()
            first_manifest = json.loads(first_manifest_text)
            self.assertEqual(first_manifest["semantic_flows_executed"], [])
            self.assertEqual(first_manifest["space_targets"], ["alpha"])
            self.assertEqual(first_manifest["frozen_install_mode"], "npm ci")
            self.assertIn("toolchain_versions", first_manifest)
            self.assertIn("node", first_manifest["toolchain_versions"])
            self.assertIn("package_manager", first_manifest["toolchain_versions"])
            self.assertIn("tailwind_cli", first_manifest["toolchain_versions"])

            space_index_path = space_root / "site" / "index.html"
            topic_page_path = space_root / "site" / "topics" / "topic-a.html"
            source_page_path = space_root / "site" / "sources" / "source-a.html"
            site_new_path = site_path / "site" / "new" / "index.html"
            self.assertTrue(space_index_path.is_file())
            self.assertTrue(topic_page_path.is_file())
            self.assertTrue(source_page_path.is_file())
            self.assertTrue(site_new_path.is_file())

            first_index_text = space_index_path.read_text()
            self.assertIn("Topic A", first_index_text)
            self.assertIn("Source A", first_index_text)

            second = self._run(command)
            self.assertEqual(second.returncode, 0, msg=second.stderr)
            second_manifest_text = manifest_path.read_text()
            self.assertEqual(first_manifest_text, second_manifest_text)
            self.assertEqual(first_index_text, space_index_path.read_text())

    def test_build_fails_fast_on_unresolved_topic_source_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_topic_record(
                space_root,
                topic_id="topic-missing-link",
                title="Broken Topic",
                source_ids=["source-does-not-exist"],
            )

            result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "alpha",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unresolved source link", result.stderr)

    def test_build_fails_fast_on_template_conversion_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_source_record(space_root, source_id="source-a", title="Source A")
            bad_topic_payload = {
                "topic_id": "topic-invalid-section",
                "title": "Invalid Topic",
                "structure_type": "wiki",
                "sections": [{"heading": "Summary"}],
                "claim_ids": [],
                "source_ids": ["source-a"],
            }
            (space_root / "topics" / "topic-invalid-section.json").write_text(
                json.dumps(bad_topic_payload, indent=2, sort_keys=True) + "\n"
            )

            result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "alpha",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("sections[0].body", result.stderr)

    def test_toolchain_reproducibility_validation_enforces_package_manager_lockfile_node_pin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)

            # Missing packageManager.
            self._write_package_json(repo_root, {"name": "sapi", "version": "0.0.0"})
            self._write_npm_lockfile(repo_root, "sapi", "0.0.0")
            (repo_root / ".nvmrc").write_text("20\n")
            with self.assertRaises(ValueError):
                _validate_frontend_toolchain_reproducibility(repo_root)

            # Mismatched package-manager family and lockfile.
            self._write_package_json(
                repo_root,
                {"name": "sapi", "version": "0.0.0", "packageManager": "pnpm@9.0.0"},
            )
            with self.assertRaises(ValueError):
                _validate_frontend_toolchain_reproducibility(repo_root)

            # Multiple lockfiles.
            (repo_root / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")
            with self.assertRaises(ValueError):
                _validate_frontend_toolchain_reproducibility(repo_root)

            # Missing node pin.
            (repo_root / "pnpm-lock.yaml").unlink()
            (repo_root / ".nvmrc").unlink()
            self._write_package_json(
                repo_root,
                {"name": "sapi", "version": "0.0.0", "packageManager": "npm@10.9.2"},
            )
            with self.assertRaises(ValueError):
                _validate_frontend_toolchain_reproducibility(repo_root)

            # Valid reproducibility envelope.
            (repo_root / ".nvmrc").write_text("20\n")
            result = _validate_frontend_toolchain_reproducibility(repo_root)
            self.assertEqual(result["package_manager"], "npm@10.9.2")
            self.assertEqual(result["frozen_install_mode"], "npm ci")
            self.assertEqual(result["node"], "20")

    def _bootstrap_site_space(self, tmp_root: Path, space_name: str) -> tuple[Path, Path]:
        site_path = tmp_root / "site-a"
        self._run(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "My Site"], check=True)
        self._run(["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), space_name], check=True)
        space_root = site_path / "spaces" / space_name
        return site_path, space_root

    def _write_source_record(self, space_root: Path, *, source_id: str, title: str) -> None:
        payload = {
            "schema_version": "source_record_v1",
            "source_id": source_id,
            "title": title,
            "date": "2026-04-12",
            "ingested_at": "2026-04-12T00:00:00Z",
        }
        path = space_root / "sources" / "records" / f"{source_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def _write_topic_record(
        self,
        space_root: Path,
        *,
        topic_id: str,
        title: str,
        source_ids: list[str],
    ) -> None:
        payload = {
            "topic_id": topic_id,
            "title": title,
            "structure_type": "wiki",
            "sections": [{"heading": "Summary", "body": "Body"}],
            "claim_ids": [],
            "source_ids": source_ids,
        }
        path = space_root / "topics" / f"{topic_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def _write_package_json(self, repo_root: Path, payload: dict[str, object]) -> None:
        (repo_root / "package.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def _write_npm_lockfile(self, repo_root: Path, name: str, version: str) -> None:
        payload = {
            "name": name,
            "version": version,
            "lockfileVersion": 3,
            "requires": True,
            "packages": {"": {"name": name, "version": version}},
        }
        (repo_root / "package-lock.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

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
