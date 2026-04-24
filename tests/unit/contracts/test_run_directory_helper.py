from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from tests.conftest import latest_run_directory


class RunDirectoryHelperTests(unittest.TestCase):
    def test_latest_run_directory_prefers_newer_run_record_timestamp_over_lexicographic_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "space"
            runs_root = space_root / "runs"

            newer_name = "run-20260425T120000Z--aaaaabbbbb"
            older_name = "run-20260425T120000Z--zzzzzyyyyy"

            older_run = runs_root / older_name
            older_run.mkdir(parents=True)
            (older_run / "run.md").write_text("---\nrun_id: \"old\"\n---\n")

            time.sleep(0.01)

            newer_run = runs_root / newer_name
            newer_run.mkdir(parents=True)
            (newer_run / "run.md").write_text("---\nrun_id: \"new\"\n---\n")

            self.assertEqual(latest_run_directory(space_root), newer_run)


if __name__ == "__main__":
    unittest.main()
