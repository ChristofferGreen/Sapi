from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


class WrapperAliasConflictsIntegrationTests(unittest.TestCase):
    def test_ingest_removed_source_only_flags_fail_fast(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = self._bootstrap_site_and_space(Path(tmp), "alpha")
            source_path = Path(tmp) / "source.txt"
            source_path.write_text("sample source\n")
            for removed_flag in ("--source-only", "--query-only"):
                with self.subTest(flag=removed_flag):
                    result = self._run(
                        [
                            "bash",
                            str(REPO_ROOT / "ingest.sh"),
                            str(site_path),
                            "alpha",
                            str(source_path),
                            removed_flag,
                        ]
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("has been removed", result.stderr)
                    self.assertIn("Usage:", result.stderr)

    def test_comments_user_alias_conflict_fails_fast(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = self._bootstrap_site_and_space(Path(tmp), "alpha")
            result = self._run(
                [
                    "bash",
                    str(REPO_ROOT / "create_comments.sh"),
                    str(site_path),
                    "alpha",
                    "--count",
                    "5",
                    "--comment-user",
                    "persona-maya-santoro",
                    "--user",
                    "persona-eli-okafor",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot combine", result.stderr)
            self.assertIn("Usage:", result.stderr)

    def test_comments_page_alias_conflict_fails_fast(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = self._bootstrap_site_and_space(Path(tmp), "alpha")
            result = self._run(
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
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot combine", result.stderr)
            self.assertIn("Usage:", result.stderr)

    def test_comments_count_alias_conflict_fails_fast(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = self._bootstrap_site_and_space(Path(tmp), "alpha")
            result = self._run(
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
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot combine positional count alias with --count", result.stderr)
            self.assertIn("Usage:", result.stderr)

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
