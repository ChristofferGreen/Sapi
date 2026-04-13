from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.conftest import REPO_ROOT, bootstrap_site_and_space, run_command, write_source_fixture


class BuildDeterminismIntegrationTests(unittest.TestCase):
    def test_repeated_full_builds_produce_identical_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            source_path = write_source_fixture(tmp_root, content="tier4 deterministic fixture\n")

            ingest_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Tier4 Determinism Source",
                    "--mock-llm",
                ]
            )
            self.assertEqual(ingest_result.returncode, 0, msg=ingest_result.stderr)

            first_build = _run_build(site_path=site_path, incremental=False)
            self.assertEqual(first_build.returncode, 0, msg=first_build.stderr)
            first_snapshot = _capture_build_snapshot(site_path=site_path)
            self.assertIn("outputs/build_site/manifest.json", first_snapshot)
            self.assertIn("site/index.html", first_snapshot)
            self.assertIn("spaces/alpha/site/index.html", first_snapshot)
            self.assertIn("site/assets/site.css", first_snapshot)
            self.assertIn("spaces/alpha/site/assets/site.css", first_snapshot)
            self.assertIn('<meta name="viewport" content="width=device-width, initial-scale=1">', first_snapshot["site/index.html"])
            self.assertIn('<link rel="stylesheet" href="assets/site.css">', first_snapshot["site/index.html"])
            self.assertIn(
                '<link rel="stylesheet" href="assets/site.css">',
                first_snapshot["spaces/alpha/site/index.html"],
            )

            second_build = _run_build(site_path=site_path, incremental=False)
            self.assertEqual(second_build.returncode, 0, msg=second_build.stderr)
            second_snapshot = _capture_build_snapshot(site_path=site_path)

            self.assertEqual(first_snapshot, second_snapshot)


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


def _capture_build_snapshot(*, site_path: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in sorted((site_path / "site").rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in {".html", ".svg", ".css"}:
            continue
        snapshot[str(path.relative_to(site_path))] = path.read_text()

    for path in sorted((site_path / "spaces" / "alpha" / "site").rglob("*")):
        if not path.is_file() or path.suffix not in {".html", ".css"}:
            continue
        snapshot[str(path.relative_to(site_path))] = path.read_text()

    manifest_path = site_path / "outputs" / "build_site" / "manifest.json"
    snapshot[str(manifest_path.relative_to(site_path))] = manifest_path.read_text()
    return snapshot


if __name__ == "__main__":
    unittest.main()
