from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.conftest import REPO_ROOT, bootstrap_site_and_space, run_command


GOLDEN_SITE_SNAPSHOT = (
    Path(__file__).resolve().parent / "site_snapshot" / "space_home_empty.html"
)
GOLDEN_SITE_ROOT_INDEX_SNAPSHOT = (
    Path(__file__).resolve().parent / "site_snapshot" / "site_root_index_empty.html"
)


class SiteSnapshotGoldenTests(unittest.TestCase):
    def test_site_root_index_matches_golden_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = bootstrap_site_and_space(Path(tmp), "alpha")
            result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "alpha",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            actual = (site_path / "site" / "index.html").read_text()
            expected = GOLDEN_SITE_ROOT_INDEX_SNAPSHOT.read_text()
            self.assertEqual(actual, expected)

    def test_empty_space_home_matches_golden_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = bootstrap_site_and_space(Path(tmp), "alpha")
            result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "alpha",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            actual = (site_path / "spaces" / "alpha" / "site" / "index.html").read_text()
            expected = GOLDEN_SITE_SNAPSHOT.read_text()
            self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
