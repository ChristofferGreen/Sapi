from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

import scripts.ingest_source as ingest_source
from tests.conftest import (
    assert_no_run_containers,
    bootstrap_site_and_space,
    write_source_fixture,
)


class SemanticRepairExhaustionRollbackIntegrationTests(unittest.TestCase):
    def test_semantic_repair_exhaustion_rolls_back_default_ingest_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            source_path = write_source_fixture(tmp_root, content="repair exhaustion fixture\n")

            stderr = io.StringIO()
            argv = [
                "ingest_source.py",
                "alpha",
                str(source_path),
                "--registry-path",
                str(site_path / "spaces.toml"),
                "--mock-llm",
            ]
            # Return schema-invalid semantic output for every attempt to force retry exhaustion.
            with patch.object(
                ingest_source._BootstrapIngestExtractionClient,
                "generate_semantic_json",
                return_value=json.dumps({"claims": [], "relations": []}),
            ):
                with patch("sys.argv", argv):
                    with redirect_stderr(stderr):
                        exit_code = ingest_source.main()

            self.assertNotEqual(exit_code, 0)
            self.assertIn("semantic flow", stderr.getvalue().lower())

            self.assertEqual(list((space_root / "sources" / "records").glob("*.json")), [])
            self.assertEqual(list((space_root / "claims").glob("*.json")), [])
            self.assertEqual(list((space_root / "relations").glob("*.json")), [])
            self.assertEqual(list((space_root / "topics").glob("*.json")), [])
            assert_no_run_containers(space_root)


if __name__ == "__main__":
    unittest.main()
