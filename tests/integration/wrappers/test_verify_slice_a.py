from __future__ import annotations

import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
_MANIFEST_RE = re.compile(r"manifest_path=([^,\s)]+)")


class VerifySliceAIntegrationTests(unittest.TestCase):
    def test_verify_slice_a_executes_vertical_slice_and_writes_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = tmp_root / "slice-a-site"
            source_path = tmp_root / "source.txt"
            source_path.write_text("slice a verification source\n")

            result = _run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "verify_slice_a.py"),
                    str(site_path),
                    "alpha",
                    str(source_path),
                    "What changed?",
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("verification complete", result.stdout)

            match = _MANIFEST_RE.search(result.stdout)
            self.assertIsNotNone(match, result.stdout)
            manifest_path = Path(match.group(1))
            self.assertTrue(manifest_path.is_file())

            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(manifest["status"], "success")
            self.assertEqual(
                manifest["checks"]["end_to_end_path_executed"],
                ["create_site", "create_space", "ingest", "build", "query", "validate"],
            )
            self.assertEqual(manifest["checks"]["ingest_run_envelope_errors"], [])
            self.assertEqual(manifest["checks"]["query_run_envelope_errors"], [])
            self.assertEqual(manifest["checks"]["deferred_build_backlog_run_ids"], [])

            run_ids = manifest["run_ids"]
            self.assertRegex(run_ids["ingest"], r"^run-")
            self.assertRegex(run_ids["query"], r"^run-")


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


if __name__ == "__main__":
    unittest.main()
