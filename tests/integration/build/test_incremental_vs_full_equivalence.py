from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.conftest import REPO_ROOT, bootstrap_site_and_space, run_command, write_source_fixture


class IncrementalBuildEquivalenceIntegrationTests(unittest.TestCase):
    def test_incremental_build_matches_full_build_rendered_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            source_path = write_source_fixture(tmp_root, content="tier4 incremental equivalence fixture\n")

            ingest_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Tier4 Incremental Source",
                    "--mock-llm",
                ]
            )
            self.assertEqual(ingest_result.returncode, 0, msg=ingest_result.stderr)

            full_build = _run_build(site_path=site_path, incremental=False)
            self.assertEqual(full_build.returncode, 0, msg=full_build.stderr)
            full_snapshot = _capture_rendered_snapshot(site_path=site_path)
            self.assertIn("site/index.html", full_snapshot)
            self.assertIn("spaces/alpha/site/index.html", full_snapshot)
            self.assertIn("site/assets/site.css", full_snapshot)
            self.assertIn("spaces/alpha/site/assets/site.css", full_snapshot)

            incremental_build = _run_build(site_path=site_path, incremental=True)
            self.assertEqual(incremental_build.returncode, 0, msg=incremental_build.stderr)
            incremental_snapshot = _capture_rendered_snapshot(site_path=site_path)

            self.assertEqual(full_snapshot, incremental_snapshot)

    def test_full_build_prunes_stale_rendered_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            source_path = write_source_fixture(tmp_root, content="stale file pruning fixture\n")

            ingest_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Stale Pruning Source",
                    "--mock-llm",
                ]
            )
            self.assertEqual(ingest_result.returncode, 0, msg=ingest_result.stderr)

            stale_space_file = site_path / "spaces" / "alpha" / "site" / "sources" / "stale-source.html"
            stale_space_file.parent.mkdir(parents=True, exist_ok=True)
            stale_space_file.write_text("<html><body>stale source page</body></html>\n")

            stale_root_file = site_path / "site" / "new" / "stale-feed-page.html"
            stale_root_file.parent.mkdir(parents=True, exist_ok=True)
            stale_root_file.write_text("<html><body>stale feed page</body></html>\n")

            full_build = _run_build(site_path=site_path, incremental=False)
            self.assertEqual(full_build.returncode, 0, msg=full_build.stderr)

            self.assertFalse(stale_space_file.exists())
            self.assertFalse(stale_root_file.exists())
            self.assertTrue((site_path / "spaces" / "alpha" / "site" / "sources" / "index.html").is_file())
            self.assertTrue((site_path / "site" / "new" / "index.html").is_file())


def _run_build(*, site_path: Path, incremental: bool) -> object:
    cmd = [
        "python3",
        str(REPO_ROOT / "scripts" / "build_site.py"),
        "--registry-path",
        str(site_path / "spaces.toml"),
        "alpha",
    ]
    if incremental:
        cmd.append("--incremental")
    return run_command(cmd)


def _capture_rendered_snapshot(*, site_path: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for root in (site_path / "site", site_path / "spaces" / "alpha" / "site"):
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix not in {".html", ".svg", ".css"}:
                continue
            snapshot[str(path.relative_to(site_path))] = path.read_text()
    return snapshot


if __name__ == "__main__":
    unittest.main()
