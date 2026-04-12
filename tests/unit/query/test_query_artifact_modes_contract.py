from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
_NON_MARKDOWN_MODES = ("mermaid", "images", "slides", "pdf")


class QueryArtifactModesContractTests(unittest.TestCase):
    def test_non_markdown_modes_emit_canonical_manifest_and_manifest_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = _bootstrap_site_and_space(Path(tmp), "alpha")
            for mode in _NON_MARKDOWN_MODES:
                with self.subTest(mode=mode):
                    output_dir = _run_query_and_get_output_dir(site_path=site_path, output_mode=mode)
                    query_payload = json.loads((output_dir / "query.json").read_text())
                    manifest_path = output_dir / "manifest.json"
                    self.assertTrue(manifest_path.is_file())
                    self.assertEqual(query_payload["manifest_path"], str(manifest_path.resolve()))

    def test_markdown_mode_emits_no_manifest_and_keeps_manifest_path_null(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = _bootstrap_site_and_space(Path(tmp), "alpha")
            output_dir = _run_query_and_get_output_dir(site_path=site_path, output_mode="markdown")
            query_payload = json.loads((output_dir / "query.json").read_text())
            self.assertFalse((output_dir / "manifest.json").exists())
            self.assertIsNone(query_payload["manifest_path"])

    def test_manifest_keys_and_hash_contract_match_mode_specific_artifacts(self) -> None:
        required_manifest_keys = {
            "query_id",
            "mode",
            "run_id",
            "question",
            "claims_used",
            "sources_used",
            "artifacts",
            "artifact_hashes",
        }
        with tempfile.TemporaryDirectory() as tmp:
            site_path = _bootstrap_site_and_space(Path(tmp), "alpha")
            for mode in _NON_MARKDOWN_MODES:
                with self.subTest(mode=mode):
                    output_dir = _run_query_and_get_output_dir(site_path=site_path, output_mode=mode)
                    manifest = json.loads((output_dir / "manifest.json").read_text())
                    self.assertTrue(required_manifest_keys.issubset(set(manifest.keys())))
                    self.assertEqual(manifest["mode"], mode)

                    artifact_hashes = manifest["artifact_hashes"]
                    self.assertIsInstance(artifact_hashes, dict)
                    for relative_path, declared_hash in artifact_hashes.items():
                        artifact_path = output_dir / relative_path
                        self.assertTrue(artifact_path.is_file())
                        actual_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
                        self.assertEqual(declared_hash, actual_hash)

                    artifacts = manifest["artifacts"]
                    self.assertIsInstance(artifacts, list)
                    self.assertGreaterEqual(len(artifacts), 1)
                    first_row = artifacts[0]
                    if mode == "mermaid":
                        self.assertTrue(any(row.get("file") == "diagram.mmd" for row in artifacts))
                        self.assertIn("claim_ids", first_row)
                    elif mode == "images":
                        self.assertIn("file", first_row)
                        self.assertIn("title", first_row)
                        self.assertIn("alt_text", first_row)
                        self.assertIn("claim_ids", first_row)
                    elif mode == "slides":
                        self.assertIn("deck_md", first_row)
                        self.assertIn("deck_html", first_row)
                        self.assertIn("deck_pdf", first_row)
                        self.assertIn("slides", first_row)
                    elif mode == "pdf":
                        self.assertIn("file", first_row)
                        self.assertIn("mime_type", first_row)
                        self.assertIn("claim_ids", first_row)


def _bootstrap_site_and_space(tmp_root: Path, space_name: str) -> Path:
    site_path = tmp_root / "site-a"
    _run(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "My Site"], check=True)
    _run(["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), space_name], check=True)
    return site_path


def _run_query_and_get_output_dir(*, site_path: Path, output_mode: str) -> Path:
    space_root = site_path / "spaces" / "alpha"
    before = {path.name for path in (space_root / "outputs" / "query").glob("query-*")}
    result = _run(
        [
            "python3",
            str(REPO_ROOT / "scripts" / "query.py"),
            "alpha",
            "artifact mode contract check",
            "--registry-path",
            str(site_path / "spaces.toml"),
            "--output-format",
            output_mode,
            "--mock-llm",
        ]
    )
    if result.returncode != 0:
        raise AssertionError(
            f"Query command failed unexpectedly (exit={result.returncode}):\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    after = {path.name for path in (space_root / "outputs" / "query").glob("query-*")}
    new_dirs = sorted(after - before)
    if len(new_dirs) != 1:
        raise AssertionError(f"Expected one new query output directory, got: {new_dirs}")
    return space_root / "outputs" / "query" / new_dirs[0]


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

