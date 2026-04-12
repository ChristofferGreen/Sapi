from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


class WrapperAliasNormalizationTests(unittest.TestCase):
    def test_ingest_query_only_alias_normalizes_to_source_only_with_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = self._bootstrap_site_and_space(Path(tmp), "alpha")
            result = self._run(
                [
                    "bash",
                    str(REPO_ROOT / "ingest.sh"),
                    str(site_path),
                    "alpha",
                    "dummy-source",
                    "--query-only",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("deprecated", result.stderr)
            self.assertIn("scripts/ingest_source.py scaffold ready", result.stdout)

    def test_comment_aliases_and_legacy_positional_count_normalize(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = self._bootstrap_site_and_space(Path(tmp), "alpha")
            result = self._run(
                [
                    "bash",
                    str(REPO_ROOT / "create_comments.sh"),
                    str(site_path),
                    "alpha",
                    "5",
                    "--user",
                    "alice",
                    "--page",
                    "topic:topic-a",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("positional count argument is deprecated", result.stderr)
            self.assertIn("--user is deprecated", result.stderr)
            self.assertIn("--page is deprecated", result.stderr)
            self.assertIn("scripts/create_comments.py scaffold ready", result.stdout)

    def test_ingest_canonical_and_alias_conflict_fails_fast(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = self._bootstrap_site_and_space(Path(tmp), "alpha")
            result = self._run(
                [
                    "bash",
                    str(REPO_ROOT / "ingest.sh"),
                    str(site_path),
                    "alpha",
                    "dummy-source",
                    "--source-only",
                    "--query-only",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot combine --source-only", result.stderr)
            self.assertIn("Usage:", result.stderr)

    def test_comment_canonical_and_alias_conflicts_fail_fast(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = self._bootstrap_site_and_space(Path(tmp), "alpha")

            # conflict: canonical + alias for comment user
            result_user = self._run(
                [
                    "bash",
                    str(REPO_ROOT / "create_comments.sh"),
                    str(site_path),
                    "alpha",
                    "--count",
                    "5",
                    "--comment-user",
                    "alice",
                    "--user",
                    "bob",
                ]
            )
            self.assertNotEqual(result_user.returncode, 0)
            self.assertIn("cannot combine", result_user.stderr)
            self.assertIn("Usage:", result_user.stderr)

            # conflict: canonical + alias for comment page
            result_page = self._run(
                [
                    "bash",
                    str(REPO_ROOT / "create_comments.sh"),
                    str(site_path),
                    "alpha",
                    "--count",
                    "5",
                    "--comment-page",
                    "topic:topic-a",
                    "--page",
                    "topic:topic-b",
                ]
            )
            self.assertNotEqual(result_page.returncode, 0)
            self.assertIn("cannot combine", result_page.stderr)
            self.assertIn("Usage:", result_page.stderr)

            # conflict: canonical + alias for count
            result_count = self._run(
                [
                    "bash",
                    str(REPO_ROOT / "create_comments.sh"),
                    str(site_path),
                    "alpha",
                    "5",
                    "--count",
                    "6",
                ]
            )
            self.assertNotEqual(result_count.returncode, 0)
            self.assertIn("cannot combine positional count alias with --count", result_count.stderr)
            self.assertIn("Usage:", result_count.stderr)

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
