from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sapi.profiles.persona_catalog import load_seeded_persona_catalog
from tests.conftest import REPO_ROOT, bootstrap_site_and_space, run_command, write_source_fixture


class SiteNewRefreshPolicyIntegrationTests(unittest.TestCase):
    def test_query_profiles_and_claim_only_comments_do_not_refresh_site_root_new(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            source_path = write_source_fixture(tmp_root, content="site-root refresh fixture\n")

            ingest_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Refresh Policy Fixture",
                    "--mock-llm",
                ]
            )
            self.assertEqual(ingest_result.returncode, 0, msg=ingest_result.stderr)

            new_index_path = site_path / "site" / "new" / "index.html"
            self.assertTrue(new_index_path.is_file())
            baseline_mtime = new_index_path.stat().st_mtime_ns

            query_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "query.py"),
                    "alpha",
                    "Does query refresh site root?",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--mock-llm",
                ]
            )
            self.assertEqual(query_result.returncode, 0, msg=query_result.stderr)
            self.assertEqual(new_index_path.stat().st_mtime_ns, baseline_mtime)

            profiles_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "generate_profiles.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--persona-id",
                    _seeded_persona_ids(count=1)[0],
                    "--mock-llm",
                ]
            )
            self.assertEqual(profiles_result.returncode, 0, msg=profiles_result.stderr)
            self.assertEqual(new_index_path.stat().st_mtime_ns, baseline_mtime)

            comments_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "create_comments.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--count",
                    "5",
                    "--mock-llm",
                ]
            )
            self.assertEqual(comments_result.returncode, 0, msg=comments_result.stderr)
            self.assertEqual(new_index_path.stat().st_mtime_ns, baseline_mtime)

    def test_subsequent_ingest_refreshes_site_root_new(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            source_path = write_source_fixture(tmp_root, filename="source-a.txt", content="ingest fixture a\n")

            ingest_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Ingest Refresh Fixture A",
                    "--mock-llm",
                ]
            )
            self.assertEqual(ingest_result.returncode, 0, msg=ingest_result.stderr)

            new_index_path = site_path / "site" / "new" / "index.html"
            baseline_mtime = new_index_path.stat().st_mtime_ns
            second_source_path = write_source_fixture(
                tmp_root,
                filename="source-b.txt",
                content="ingest fixture b\n",
            )

            second_ingest_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(second_source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Ingest Refresh Fixture B",
                    "--mock-llm",
                ]
            )
            self.assertEqual(second_ingest_result.returncode, 0, msg=second_ingest_result.stderr)
            self.assertGreater(new_index_path.stat().st_mtime_ns, baseline_mtime)


def _seeded_persona_ids(*, count: int) -> list[str]:
    rows = load_seeded_persona_catalog(repo_root=REPO_ROOT, require_image_files=False)
    return [str(row["persona_id"]) for row in rows[:count]]


if __name__ == "__main__":
    unittest.main()
