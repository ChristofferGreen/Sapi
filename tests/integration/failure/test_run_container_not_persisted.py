from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.conftest import (
    REPO_ROOT,
    assert_no_run_containers,
    bootstrap_site_and_space,
    run_command,
    write_source_fixture,
)


class RunContainerNotPersistedIntegrationTests(unittest.TestCase):
    def test_query_terminal_failure_does_not_persist_run_container(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = bootstrap_site_and_space(Path(tmp), "alpha")
            space_root = site_path / "spaces" / "alpha"

            result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "query.py"),
                    "alpha",
                    "What changed?",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--simulate-terminal-failure",
                    "--mock-llm",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Simulated terminal query failure", result.stderr)

            self.assertEqual(list((space_root / "outputs" / "query").glob("query-*")), [])
            assert_no_run_containers(space_root)

    def test_ingest_terminal_failure_does_not_persist_run_container(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            source_path = write_source_fixture(tmp_root, content="failure rollback contract\n")

            result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--simulate-terminal-failure",
                    "--mock-llm",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Simulated terminal ingest failure", result.stderr)

            self.assertEqual(list((space_root / "sources" / "records").glob("*.json")), [])
            self.assertEqual(list((space_root / "claims").glob("*.json")), [])
            self.assertEqual(list((space_root / "relations").glob("*.json")), [])
            self.assertEqual(list((space_root / "topics").glob("*.json")), [])
            assert_no_run_containers(space_root)


if __name__ == "__main__":
    unittest.main()
